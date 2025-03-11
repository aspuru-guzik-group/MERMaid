# -*- coding: utf-8 -*-
import argparse
import importlib.util
import multiprocessing
import json
import sys
from collections import deque
from enum import auto, StrEnum
from functools import partial
from itertools import chain, repeat
from pathlib import Path
from types import ModuleType
from typing import Any, NewType, Sequence, TypeAlias, TypeVar

import numpy as np
from graphdb import janus
from gremlin_python.structure.graph import GraphTraversalSource
from prompt import build_prompt, build_prompt_from_react_file, get_response


C = TypeVar('C', bound=janus.Connection)
TypeEDict = NewType("TypeEDict", dict[Any, Any])
KeyEDict = NewType("KeyEDict", dict[Any, Any])
ParseResult: TypeAlias = tuple[
    list[C]
    , list[TypeEDict]
    , list[KeyEDict]
]

SCHEMA_DEFAULT_PATH = Path(janus.__file__).parent / "schemas"
SCHEMAS = dict(map(
    lambda x: (x.stem, x)
    , SCHEMA_DEFAULT_PATH.glob("*.py")
))
ITERATOR_STR = "Now let's go for optimize iteration number {number}"


class Commands(StrEnum):
    TRANSFORM = auto()
    PARSE = auto()


def filter_none(xs): return filter(lambda x: x is not None, xs)


def read_and_clean_file(path: Path | str) -> list[dict[Any, Any]] | None:
    try:
        with open(path) as f:
            content = f.read().split('```json')[1].split('```')[0]
            return json.loads(content.strip())
    except (FileNotFoundError, json.JSONDecodeError, IndexError):
        return None


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
        "-g", "--graph_name",
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
        help="Folder where the JSON files from transform are stored."
    )

    return parser



def build_transform_argparser():
    parser = argparse.ArgumentParser(add_help=False) 

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Folder where the JSON files from DataRaider are stored."
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
    if s := SCHEMAS.get(schema):
        p = s
    else:
        p = Path(schema)
    return load_module("schema", p)
    

def build_main_argparser() -> argparse.ArgumentParser:
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
        Commands.TRANSFORM,
        help="""Converts a set of JSON files within a folder into an
        intermediate JSON structured format ready to be uploaded to a certain
        database. Optinioally, uploads the transformed files into a database
        and uses RAG to retrieve already known nodes. Address, port and graph
        arguments are only used if RAG is active (see --subs).""",
        parents=[build_transform_argparser(), build_janus_argparser()]
    )
    subparsers.add_parser(
        Commands.PARSE,
        help="""Converts a set of JSON files into the target format and stores
        them in the given graph database.""",
        parents=[build_parser_argparser(), build_janus_argparser()]
    )

    return main_parser


def build_rag_subs(
    graph: janus.GraphTraversalSource
    , sub_dict: dict[str, str]
) -> dict[str, str]:
    out_dict = {}
    for k, v in sub_dict.items():
        if (resp := ', '.join(janus.get_vnamelist_from_db(v, graph))) or None is not None:
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
    if spec.loader is None:
        raise ValueError
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


def parse_or_skip(
    reaction: list[dict[Any, Any]]
    , conn_constructor: type[C]
) -> ParseResult[C]:
    connections = []
    type_e = []
    key_e = []
    for item in reaction:
        try:
            connections.append(conn_constructor.from_dict(item))
        except TypeError:
            type_e.append(TypeEDict(item))
            continue
        except KeyError:
            key_e.append(KeyEDict(item))
            continue
    return (connections, type_e, key_e)


def parse_file_and_update_db(
    graph: GraphTraversalSource
    , file_name: Path
    , conn_constructor: type[C]
) -> ParseResult[C] | None:
    reaction = read_and_clean_file(file_name)
    if not reaction:
        return None
    results = parse_or_skip(
        reaction=reaction
        , conn_constructor=conn_constructor
    )
    if conns := results[0]:
        for item in conns:
            try:
                janus.add_connection(item, graph)
            except TypeError:
                janus.add_connection(item, graph)
            except:
                with open("errors.dat", 'w') as f:
                    f.write(f"{file_name}\n")
                continue
    return results


def get_json_from_react(
    graph: GraphTraversalSource
    , json_react_path: Path | str
    , results_path: Path
    , schema: ModuleType
    , substitutions: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    # Code substitution, load schema file
    if schema.__file__ is None:
        raise ValueError
    with open(schema.__file__, 'r', encoding="utf8") as f:
        rag_dict = {"code": f.readlines()}

    # Load target json
    json_react_path = Path(json_react_path)
    with open(json_react_path, 'r') as f:
        react_dict = json.load(f)

    # Prepare RAG if needed
    if substitutions is not None:
        rag_dict |= build_rag_subs(graph, substitutions)

    optimization_runs = list(react_dict["Optimization Runs"].keys())

    messages = [build_prompt_from_react_file(
        path=json_react_path
        , study_name=json_react_path.stem
        , **rag_dict
    )]
    
    messages.append(get_response(messages))

    save_path = results_path / Path(str(json_react_path.stem) +  '_1' + '.json')
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with open(save_path, 'w') as f:
        f.write(messages[-1]["content"])

    rag_fn = partial(
        parse_file_and_update_db
        , graph=graph
        , file_name=save_path
        , conn_constructor=schema.Connection
    )

    if substitutions is not None:
        rag_fn()
    for n in optimization_runs[1:]:
        messages.append(build_prompt(ITERATOR_STR.format(number=n)))
        messages.append(get_response(messages))
        save_path = results_path / Path(str(json_react_path.stem) +  f'_{n}' + '.json')
        with open(save_path, 'w') as f:
            f.write(messages[-1]["content"])
        print(f"iter: {n}")
        if substitutions is not None:
            rag_fn()
    return messages


def get_graph_from_janus(
    address: str
    , port: int
    , graph_name: str
) -> GraphTraversalSource:
    return janus.get_traversal(
        janus.connect(
            address=address
            , port=port
            , graph_name=graph_name
        ))


def exec_transform(
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


def print_parse_summary(
    results: ParseResult
    , n_files: int | None = None
    , failing_files: list[Path | str] | None = None
) -> None:
    conns_total, type_e_total, key_e_total = map(len, results)
    error_total = type_e_total + key_e_total
    total = conns_total + error_total
    if n_files:
        sys.stdout.write(f"Parsed {n_files}")
    if failing_files:
        sys.stdout.write(f" out of {len(failing_files)}\n")
    print("-Summary-")
    print(f"Connections parsed: {conns_total}/{total}")
    print(f"Total errors: {error_total}")
    print(f"  - Type errors: {type_e_total}/{error_total}")
    print(f"  - Key errors: {key_e_total}/{error_total}")
    print(f"Performance: {conns_total/total:.2f}%")
    print("-Failing files-")
    if failing_files:
        deque(map(print, failing_files), maxlen=0)


def exec_parser(
    args: argparse.Namespace
) -> None:
    rfiles = list(args.input_dir.glob("*.json"))

    graph = get_graph_from_janus(
        address=args.address
        , port=args.port
        , graph_name=args.graph_name
    )

    sync_fn = partial(
        parse_file_and_update_db
        , graph=graph
        , conn_constructor=args.schema.Connection
    )

    n_files = len(rfiles)
    type_e = []
    key_e = []
    conns = []
    failing_files = []
    for n, f in enumerate(rfiles):
        sys.stdout.write(f"\r{n}/{n_files}")
        sys.stdout.flush()
        results = sync_fn(file_name=f)

        if results is None:
            print(f"Unable to parse {f.stem}, skipping.")
            failing_files.append(f)
        else:
            conns += results[0]
            type_e += results[1]
            key_e += results[2]
            if results[1] or results[2]:
                failing_files.append(f)
        
    sys.stdout.write(f"\r{n_files}/{n_files}\n")
    sys.stdout.flush()

    print_parse_summary((conns, type_e, key_e), n_files, failing_files)


if __name__ == "__main__":
    parser = build_main_argparser()
    args = parser.parse_args()
    match args.command:
        case Commands.PARSE:
            exec_parser(args)
            pass
        case Commands.TRANSFORM:
            pass

    # schema = load_module("schema", SCHEMAS[0])
