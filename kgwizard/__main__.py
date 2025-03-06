# -*- coding: utf-8 -*-
import argparse
import importlib.util
from itertools import repeat
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence

import numpy as np
from graphdb import janus, VertexBase
from prompt import (
    build_prompt
    , build_prompt_from_react_file
    , get_response
    )


SCHEMA_DEFAULT_PATH = Path(janus.__file__).parent / "schemas"
SCHEMAS = dict(map(
    lambda x: (x.stem, x)
    , SCHEMA_DEFAULT_PATH.glob("*.py")
))


def build_janus_argparser():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        "-a", "--address",
        type=str,
        default="ws://localhost",
        help="JanusGraph server address. Defaults to ws://localhost."
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8182,
        help="JanusGraph port. Defaults to 8182."
    )

    parser.add_argument(
        "-g", "--graph",
        type=str,
        default="g",
        help="JanusGraph graph name. Defaults to g."
    )

    
    parser.add_argument(
        "-sc", "--schema",
        type=load_schema,
        help=f"""Node/Edge schema to be used during the json conversion. Can be
        either a path or any of the default schemas: {', '.join(SCHEMAS.keys())}."""
    )

    return parser


def build_parser_argparser():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Folder where the JSON files are stored."
    )

    parser.add_argument(
        "-o", "--output_dir",
        type=Path,
        default=Path("./results"),
        help=""""Folder where the generate JSON intermediate files will be
        stored. The folder will be automatically created. Defaults to
        ./results."""
    )

    return parser



def build_transform_argparser():

    parser = argparse.ArgumentParser(add_help=False) 

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Folder where the JSON files are stored."
    )
    
    parser.add_argument(
        "-o", "--output_dir",
        type=Path,
        default=Path("./results"),
        help=""""Folder where the generate JSON intermediate files will be
        stored. The folder will be automatically created. Defaults to
        ./results."""
    )

    parser.add_argument(
        "-np", "--no-parallel",
        action="store_false",
        help="""If active, run the conversions sequentially instead of using
        the dynamic increase parallel algorithm. Overrides the --workers flag.
        """
    )

    parser.add_argument(
        "-w", "--workers",
        type=int,
        help="""If defined, use this number of parallel workers instead of the
        dynamic increase algorithm."""
    )

    parser.add_argument(
        "-s", "--subs",
        type=parse_pair_sep_colon,
        nargs="+",
        help="""Substitution to be made in the instructions file. The input
        format consists on a pair formed by the substitution keyword and the
        node label separated by a colon (keyword:node_name). If substitutions
        are not given, RAG module will not be executed.
        """
    )
    
    parser.add_argument(
        "-ds", "--dynamic_start",
        type=int,
        default=1,
        help="Starting number of workers for the dynamic algorithms.."
    )

    parser.add_argument(
        "-dt", "--dynamic_steps",
        type=int,
        default=5,
        help="Maximum number of steps of the dynamic paralelization algorithm."
    )

    parser.add_argument(
        "-dw", "--dynamic_max_workers",
        type=int,
        default=30,
        help="Maximum number of workers of the dynamic paralelization algorithm."
    )

    return parser


def load_schema(schema: str):
    p: Path
    if s := SCHEMAS.get(schema): p = s
    else: p = Path(schema)
    return load_module("schema", p)
    

def build_main_argparser() -> argparse.ArgumentParser:

    parent_parser = build_janus_argparser()

    main_parser = argparse.ArgumentParser(description="Automated database parser.")
    subparsers = main_parser.add_subparsers(
        title="Commands",
        description="Available commands",
        help="Description",
        dest="command",
        required=True
    )
    subparsers.required = True

    subparsers.add_parser(
        "transform",
        help="""Converts a set of JSON files within a folder into an
        intermediate JSON structured format ready to be uploaded to a certain
        database. Optinioally, uploads the transformed files into a database
        and uses RAG to retrieve already known nodes. Address, port and graph
        arguments are only used if RAG is active (see --subs).""",
        parents=[build_transform_argparser(), build_janus_argparser()]
    )
    subparsers.add_parser(
        "parse",
        help="""Converts a set of JSON files into the target format and stores
        them in the given graph database.""",
        parents=[build_parser_argparser(), build_janus_argparser()]
    )

    return main_parser


def build_rag_subs(
    graph: janus.GraphTraversalSource
    , sub_dict: dict[str, str]
) -> janus.GraphTraversalSource:
    vname_fn = lambda x: ', '.join(janus.get_vnamelist_from_db(x, graph)) or None
    out_dict = {}
    for k, v in sub_dict.items():
        if (resp := vname_fn(v)) is not None:
            out_dict[k] = resp
    return out_dict


def load_module(
    module_name: str
    , module_path: Path
) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Cannot create a module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def dynamic_pool_execution(files, pool_sizes):
    total_files = len(files)
    start_idx = 0

    for pool_size in pool_sizes:
        if start_idx >= total_files:
            print("\nAll files processed. Exiting.\n")
            break

        batch_files = files[start_idx:start_idx + pool_size]

        print(f"\nStarting batch with {pool_size} workers, processing {len(batch_files)} files...\n")

        workers = []
        for file in batch_files:
            p = multiprocessing.Process(target=get_json_from_react, args=(file,))
            p.start()
            workers.append(p)

        for p in workers:
            p.join()

        print(f"\nBatch of {pool_size} workers finished.\n")

        start_idx += len(batch_files)


def generate_pool_sizes(
    total_files: int
    , max_workers: int=30
    , steps: int=20
    , start: int=1
) -> list[int]:
    increasing_sizes = np.round(
        np.linspace(start, max_workers ** 0.6, steps) ** (1 / 0.6)).astype(int).tolist()
    increasing_sizes = [min(x, max_workers) for x in increasing_sizes]
    remaining_files = total_files - sum(increasing_sizes)
    if remaining_files > 0:
        increasing_sizes.extend(repeat(max_workers, remaining_files))
    if (tot := sum(increasing_sizes)) > total_files:
        increasing_sizes[-1] -= tot - total_files

    return increasing_sizes


def parse_pair_sep_colon(
    s: str
) -> tuple[str, str] | None:
    if len(l := s.split(':')) != 2:
        return None
    return (l[0], l[1])


def get_json_from_react(
    connection: janus.DriverRemoteConnection
    , json_react_path: Path | str
    , substitutions: dict[str, Any]
) -> list[dict[str, str]]:
    graph = janus.get_traversal(connection)
    rag_dict = build_rag_subs(graph, substitutions)
    json_react_path = Path(json_react_path)

    with open(json_react_path, 'r') as f:
        react_dict = json.load(f)
    optimization_runs = list(react_dict["Optimization Runs"].keys())

    messages = [build_prompt_from_react_file(
        path=json_react_path
        , study_name=json_react_path.stem
        , **rag_dict
    )]
    messages.append(get_response(messages))
    print(messages)
    save_path = RESULTS_FOLDER / Path(str(json_react_path.stem) +  '_1' + '.json')
    save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, 'w') as f:
        f.write(messages[-1]["content"])
    rag_exec(graph, save_path)
    for n in optimization_runs[1:]:
        messages.append(build_prompt(ITERATOR_STR.format(number=n)))
        messages.append(get_response(messages))
        save_path = RESULTS_FOLDER / Path(str(json_react_path.stem) +  f'_{n}' + '.json')
        with open(save_path, 'w') as f:
            f.write(messages[-1]["content"])
        print(f"iter: {n}")
        rag_exec(graph, save_path)
    return messages


def exec(
    files_set: Sequence
    , max_workers: int=30
    , steps: int=5
    , start: int=1
):
    pool_sizes = generate_pool_sizes(
        total_files=len(files_set)
        , steps=steps
        , max_workers=max_workers
        , start=start
    )
    dynamic_pool_execution(files_set, pool_sizes)

    
if __name__ == "__main__":
    parser = build_main_argparser()
    args = parser.parse_args()
    # schema = load_module("schema", SCHEMAS[0])
