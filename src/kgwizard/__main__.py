# -*- coding: utf-8 -*-
"""
Automated database parser and transformer.

This module provides functionalities for transforming JSON data, parsing it,
and optionally uploading it to a JanusGraph database. It includes dynamic
and static parallel execution for faster processing, as well as a
substitution mechanism (RAG) for retrieving existing nodes in the database.
"""
import argparse
from concurrent.futures.thread import _worker
import importlib.util
import multiprocessing
import json
import os
import sys
from collections import deque
from enum import auto, StrEnum
from functools import partial
from itertools import chain, repeat
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, NewType, Sequence, TypeAlias, TypeVar

import numpy as np
from .graphdb import janus
from gremlin_python.structure.graph import GraphTraversalSource
from .prompt import build_prompt, build_prompt_from_react_file, get_response

# This is the only way I've found to execute the transformation using multiprocessing
global schema


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
    """
    Enumeration of the available commands for the parser.

    :cvar TRANSFORM: Command for transforming raw JSON files into an intermediate
                     format ready for database insertion.
    :cvar PARSE: Command for parsing the intermediate files and storing them
                 directly in the database.
    """
    TRANSFORM = auto()
    PARSE = auto()


def filter_none(xs):
    """
    Filter out None values from an iterable.

    :param xs: The iterable to filter.
    :type xs: Iterable
    :return: An iterator that yields only non-None items from xs.
    :rtype: filter
    """
    return filter(lambda x: x is not None, xs)


def read_and_clean_file(path: Path | str) -> list[dict[Any, Any]] | None:
    """
    Opens a JSON file, extracts data found between ```json ... ``` segments,
    and returns a list of dictionaries.

    :param path: The path or name of the file to read.
    :type path: Path | str
    :return: A list of dictionaries extracted from the JSON file, or None if
        file not found or JSON is invalid.
    :rtype: list[dict[Any, Any]] | None
    """
    try:
        with open(path) as f:
            content = f.read().split('```json')[1].split('```')[0]
            return json.loads(content.strip())
    except (FileNotFoundError, json.JSONDecodeError, IndexError):
        return None


def _get_json_from_react_wrapper(kwargs: dict[str, Any], path: Path):
    """
    Calls `exec_fn` with a Path plus any needed keyword arguments.
    This function is top-level so it can be pickled by multiprocessing.
    """
    return get_json_from_react(path, **kwargs)


def build_janus_argparser():
    """
    Build an argument parser with arguments related to connecting to a JanusGraph
    database, including address, port, graph name, and schema.

    :return: The configured ArgumentParser instance.
    :rtype: argparse.ArgumentParser
    """
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
        default="echem",
        help=f"""Node/Edge schema to be used during the json conversion. Can be
        either a path or any of the default schemas: {','.join(SCHEMAS.keys())}.
        Defaults to echem"""
    )

    return parser


def build_parser_argparser():
    """
    Build an argument parser used for the PARSE command, which parses a set of
    JSON files and stores them in a JanusGraph database.

    :return: The configured ArgumentParser instance.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Folder where the JSON files from transform are stored."
    )

    parser.add_argument(
        "-of", "--output_file",
        type=Path,
        help=""""If set, save the graph into the specified file after updating
        the database."""
    )

    return parser



def build_transform_argparser():
    """
    Build an argument parser used for the TRANSFORM command, which converts a set
    of JSON files from DataRaider into an intermediate JSON structured format.
    Also supports RAG (Retrieval-Augmented Generation) if substitutions are given.

    :return: The configured ArgumentParser instance.
    :rtype: argparse.ArgumentParser
    """
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
        "-np", "--no_parallel",
        action="store_true",
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
        "-s", "--substitutions",
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


def load_schema(schema_name: str):
    """
    Load a Python module representing a JanusGraph schema from a file path or
    from a known default schema name.

    :param schema: A string indicating either a name in SCHEMAS or a file path.
    :type schema: str
    :return: A loaded Python module containing a Connection class for JanusGraph.
    :rtype: ModuleType
    :raises ImportError: If the module spec cannot be created.
    :raises ValueError: If the module's loader is not found.
    """
    # This is the only way I found to execute the multiprocessing
    global schema
    p: Path
    if s := SCHEMAS.get(schema_name):
        p = s
    else:
        p = Path(schema_name)

    schema = load_module("schema", p)
        
    return 
    

def build_main_argparser() -> argparse.ArgumentParser:
    """
    Build the main argument parser that includes two subparsers:
    - TRANSFORM
    - PARSE

    :return: The main ArgumentParser instance with subcommands.
    :rtype: argparse.ArgumentParser
    """
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
        arguments are only used if RAG is active (see --substitutions).""",
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
    """
    Build a dictionary of substitutions by querying the JanusGraph for each
    value's name list. The result is a dictionary mapping the original key to
    a comma-separated string of names.

    :param graph: The JanusGraph traversal source.
    :type graph: janus.GraphTraversalSource
    :param sub_dict: A dictionary where the key is the substitution keyword and
        the value is the node label to query.
    :type sub_dict: dict[str, str]
    :return: A dictionary of the same keys, where each value is a comma-separated
        string of node names retrieved from the database.
    :rtype: dict[str, str]
    """
    out_dict = {}
    for k, v in sub_dict.items():
        if (resp := ', '.join(janus.get_vnamelist_from_db(v, graph))) or None is not None:
            out_dict[k] = resp
    return out_dict


def load_module(
    module_name: str
    , module_path: Path
) -> ModuleType:
    """
    Dynamically load a Python module from a given file path.

    :param module_name: The name to assign to the loaded module.
    :type module_name: str
    :param module_path: The path to the module file.
    :type module_path: Path
    :return: The loaded module.
    :rtype: ModuleType
    :raises ImportError: If the module spec cannot be created.
    :raises ValueError: If the module's loader is missing.
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Cannot create a module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ValueError
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def dynamic_pool_execution(
    files
    , pool_sizes
    , exec_fn_args: dict[str, Any]
) -> None:
    """
    Execute a function in parallel over a list of files, dynamically batching them
    according to the provided pool_sizes. Each pool size defines the number of
    worker processes to start for that batch.

    :param files: List of file paths to process.
    :type files: list[Path]
    :param pool_sizes: A list of worker batch sizes.
    :type pool_sizes: list[int]
    :param exec_fn: The function to execute for each file, which accepts a file path.
    :type exec_fn: Callable[[str | Path], list[dict[str, str]]]
    """
    total_files = len(files)
    start_idx = 0

    results = []
    for pool_size in pool_sizes:
        if start_idx >= total_files:
            print("\nAll files processed. Exiting.\n")
            break

        batch_files = files[start_idx:start_idx + pool_size]

        print(f"\nStarting batch with {pool_size} workers, processing {len(batch_files)} files...\n")

        static_par_exec_transform(
            files_set=files
            , exec_fn_args=exec_fn_args
            , workers=pool_size
        )
        
        print(f"\nBatch of {pool_size} workers finished.\n")

        start_idx += len(batch_files)
        

def generate_pool_sizes(
    total_files: int
    , max_workers: int=30
    , steps: int=20
    , start: int=1
) -> list[int]:
    """
    Generate a list of pool sizes (number of workers) for dynamic parallel execution.
    The sizes start from 'start' and gradually increase up to 'max_workers'
    across 'steps'. If there are remaining files after these steps, 'max_workers'
    is repeated until all files are accounted for.

    :param total_files: The total number of files to process.
    :type total_files: int
    :param max_workers: The maximum number of workers allowed.
    :type max_workers: int
    :param steps: The number of steps used to interpolate from start to max_workers.
    :type steps: int
    :param start: The starting number of workers.
    :type start: int
    :return: A list of pool sizes to use for parallel execution.
    :rtype: list[int]
    """
    total = min(max_workers, total_files)
    increasing_sizes = np.round(
        np.linspace(start, total ** 0.6, steps) ** (1 / 0.6)).astype(int).tolist()
    increasing_sizes = [min(x, max_workers) for x in increasing_sizes]
    remaining_files = total_files - sum(increasing_sizes)
    if remaining_files > 0:
        increasing_sizes.extend(repeat(max_workers, remaining_files))
    if (tot := sum(increasing_sizes)) > total_files:
        increasing_sizes[-1] -= tot - total_files
    if increasing_sizes[-1] <= 0:
        pivot = increasing_sizes[-1]
        increasing_sizes = increasing_sizes[:-1]
        increasing_sizes[-1] += pivot

    return increasing_sizes


def parse_pair_sep_colon(
    s: str
) -> tuple[str, str] | None:
    """
    Parse a string in the format 'keyword:node_label' into a tuple (keyword, node_label).
    If the format is invalid, returns None.

    :param s: The input string to parse.
    :type s: str
    :return: A tuple of (keyword, node_label) or None if invalid.
    :rtype: tuple[str, str] | None
    """
    if len(l := s.split(':')) != 2:
        return None
    return (l[0], l[1])


def parse_or_skip(
    reaction: list[dict[Any, Any]]
    , conn_constructor: type[C]
) -> ParseResult[C]:
    """
    Attempt to parse a list of dictionary items into Connection objects. If a
    TypeError or KeyError is encountered, store the item in respective lists instead.

    :param reaction: A list of dictionaries to parse.
    :type reaction: list[dict[Any, Any]]
    :param conn_constructor: The constructor (class) for building Connection objects.
    :type conn_constructor: TypeVar('C', bound=janus.Connection)
    :return: A tuple of:
        ( list_of_connections, list_of_type_errors, list_of_key_errors )
    :rtype: ParseResult[C]
    """
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
    """
    Parse a JSON file from disk and insert all valid Connection objects into the
    JanusGraph database. Invalid items (TypeError/KeyError) are tracked separately.

    :param graph: The JanusGraph traversal source.
    :type graph: GraphTraversalSource
    :param file_name: Path to the JSON file to parse.
    :type file_name: Path
    :param conn_constructor: The constructor (class) for building Connection objects.
    :type conn_constructor: TypeVar('C', bound=janus.Connection)
    :return: A tuple of (list_of_connections, list_of_type_errors, list_of_key_errors),
        or None if no valid items were found.
    :rtype: ParseResult[C] | None
    """
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
    json_react_path: Path | str
    , address: str
    , port: int
    , graph_name: str
    , results_path: Path
    , substitutions: dict[str, Any] | None = None
) -> list[dict[str, str]]:
    """
    Process a JSON file (react file) to generate the final JSON output by making
    multiple iterations (optimization runs). Optionally uses RAG (if substitutions
    and graph are provided) to build a dictionary of known nodes.

    :param json_react_path: The path or name of the JSON react file.
    :type json_react_path: Path | str
    :param results_path: The output folder path to store the generated JSONs.
    :type results_path: Path
    :param substitutions: A dictionary of substitution keywords mapped to node labels,
        if RAG is desired. Defaults to None for no RAG.
    :type substitutions: dict[str, Any] | None
    :param graph: The JanusGraph traversal source. Required if RAG is active.
    :type graph: GraphTraversalSource | None
    :return: A list of the messages (dict) used during the prompt building and iteration.
    :rtype: list[dict[str, str]]
    :raises ValueError: If the schema file path is invalid (schema.__file__ is None).
    """
    graph = get_graph_from_janus(
        address=address
        , port=port
        , graph_name=graph_name
    )

    
    rag_active = substitutions is not None and graph is not None
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
    if rag_active:
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

    if rag_active:
        rag_fn = partial(
            parse_file_and_update_db
            , graph=graph
            , file_name=save_path
            , conn_constructor=schema.Connection
        )
        rag_fn()

    for n in optimization_runs[1:]:
        messages.append(build_prompt(ITERATOR_STR.format(number=n)))
        messages.append(get_response(messages))
        save_path = results_path / Path(str(json_react_path.stem) +  f'_{n}' + '.json')
        with open(save_path, 'w') as f:
            f.write(messages[-1]["content"])
        print(f"iter: {n}")
        if rag_active:
            rag_fn()
    return messages


def get_graph_from_janus(
    address: str
    , port: int
    , graph_name: str
) -> GraphTraversalSource:
    """
    Retrieve a JanusGraph traversal source given connection parameters.

    :param address: The JanusGraph server address (e.g. ws://localhost).
    :type address: str
    :param port: The JanusGraph server port (default 8182).
    :type port: int
    :param graph_name: The graph name to use (e.g. 'g').
    :type graph_name: str
    :return: A GraphTraversalSource connected to the specified JanusGraph instance.
    :rtype: GraphTraversalSource
    """
    return janus.get_traversal(
        janus.connect(
            address=address
            , port=port
            , graph_name=graph_name
        ))


def dynamic_par_exec_transform(
    files_set: Sequence
    , exec_fn_args: dict[str, Any]
    , max_workers: int=30
    , steps: int=5
    , start: int=1
):
    """
    Transform a set of files using a function, distributing them dynamically across
    processes. The number of workers increases from 'start' to 'max_workers' in
    'steps' increments.

    :param files_set: A sequence of file paths to process.
    :type files_set: Sequence[Path]
    :param exec_fn: The function to transform each file, which accepts a file path.
    :type exec_fn: Callable[[str | Path], list[dict[str, str]]]
    :param max_workers: The maximum number of worker processes allowed. Defaults to 30.
    :type max_workers: int
    :param steps: The number of steps for the size generation algorithm. Defaults to 5.
    :type steps: int
    :param start: The starting number of workers. Defaults to 1.
    :type start: int
    """
    pool_sizes = generate_pool_sizes(
        total_files=len(files_set)
        , steps=steps
        , max_workers=max_workers
        , start=start
    )
    dynamic_pool_execution(files_set, pool_sizes, exec_fn_args)


def static_par_exec_transform(
    files_set: Sequence
    , exec_fn_args: dict[str, Any]
    , workers: int=30
):
    """
    Transform a set of files using a function in parallel, with a fixed number
    of worker processes.

    :param files_set: A sequence of file paths to process.
    :type files_set: Sequence[Path]
    :param exec_fn: The function to transform each file, which accepts a file path.
    :type exec_fn: Callable[[str | Path], list[dict[str, str]]]
    :param workers: The number of parallel worker processes. Defaults to 30.
    :type workers: int
    :return: A list of results from each transformation.
    :rtype: list[Any]
    """
    with multiprocessing.Pool(processes=workers) as pool:
        results = pool.map(
            partial(get_json_from_react, **exec_fn_args)
            , files_set
        )
    return results


def sequential_exec_transform(
    files_set: Sequence
    , exec_fn_args: dict[str, Any]
):
    """
    Transform a set of files sequentially (one by one) using the given function.

    :param files_set: A sequence of file paths to process.
    :type files_set: Sequence[Path]
    :param exec_fn: The function to transform each file, which accepts a file path.
    :type exec_fn: Callable[[str | Path], list[dict[str, str]]]
    :return: A list of results from each transformation.
    :rtype: list[Any]
    """
    exec_fn_partial = partial(get_json_from_react, **exec_fn_args)
    results = list(map(exec_fn_partial, files_set))
    return results


def print_parse_summary(
    results: ParseResult
    , n_files: int | None = None
    , failing_files: list[Path | str] | None = None
) -> None:
    """
    Print a summary of parsing results, including number of connections, type
    errors, key errors, and the overall performance.

    :param results: A tuple of lists: (connections, type_errors, key_errors).
    :type results: ParseResult
    :param n_files: The number of files successfully parsed, if available.
    :type n_files: int | None
    :param failing_files: A list of files that failed to parse or had errors.
    :type failing_files: list[Path | str] | None
    """
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
    """
    Execute the PARSE command, which reads a set of JSON files in the specified
    folder, parses them into Connection objects, and writes them to the JanusGraph
    database.

    :param args: Parsed arguments from the command line, including:
        - input_dir: The folder containing the JSON files
        - address, port, graph_name: JanusGraph connection parameters
        - schema: The loaded schema module containing a Connection class
    :type args: argparse.Namespace
    """
    rfiles = list(args.input_dir.glob("*.json"))

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
    if args.output_file:
        print("")
        print(f"Saving graph file at: {args.output_file}")
        janus.save_graph(graph, args.output_file)


def exec_transform(
    args: argparse.Namespace
) -> None:
    """
    Execute the TRANSFORM command, which reads a set of JSON files from DataRaider
    and converts them into an intermediate JSON format ready to be stored in a
    database. Optionally, if substitutions are given, each resulting JSON is also
    parsed and inserted into JanusGraph via RAG.

    :param args: Parsed arguments from the command line, including:
        - input_dir: The folder containing the raw JSON files
        - output_dir: The folder where the transformed JSON files will be stored
        - no_parallel: Boolean indicating whether to run sequentially
        - workers: Fixed number of workers if given
        - dynamic_start, dynamic_steps, dynamic_max_workers: Parameters for
          dynamic parallel execution
        - substitutions: Substitutions for RAG, if any
        - address, port, graph_name: JanusGraph connection parameters
        - schema: The loaded schema module containing a Connection class
    :type args: argparse.Namespace
    """
    rfiles = list(args.input_dir.glob("*.json"))
    if args.substitutions is not None:
        graph = get_graph_from_janus(
            address=args.address
            , port=args.port
            , graph_name=args.graph_name
        )
    else:
        graph = None

    # Create output directiory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    exec_fn_args = {
        "results_path": args.output_dir
        , "substitutions": dict(args.substitutions)
        , "address": args.address
        , "port": args.port
        , "graph_name": args.graph_name
    }

    if args.no_parallel:
        sequential_exec_transform(
            files_set=rfiles
            , exec_fn_args=exec_fn_args
        )
    elif args.workers is not None:
        static_par_exec_transform(
            files_set=rfiles
            , exec_fn_args=exec_fn_args
            , workers=args.workers
        )
    else:
        dynamic_par_exec_transform(
            files_set=rfiles
            , exec_fn_args=exec_fn_args
            , max_workers=args.dynamic_max_workers
            , steps=args.dynamic_steps
            , start=args.dynamic_start
        )

def main() -> None:
    parser = build_main_argparser()
    args = parser.parse_args()
    match args.command:
        case Commands.PARSE:
            exec_parser(args)
        case Commands.TRANSFORM:
            exec_transform(args)


if __name__ == "__main__":
    main()
