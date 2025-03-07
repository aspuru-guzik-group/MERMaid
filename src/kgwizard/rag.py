# -*- coding: utf-8 -*-

import json
from typing import Type
from multiprocessing import Pool
from pathlib import Path
from itertools import chain, repeat
from parse_test import rag_exec
import multiprocessing
import time

import numpy as np
from gremlin_python.structure.graph import GraphTraversalSource
from janus import *
from schema import *
from oai import \
    ( build_prompt
    , build_prompt_from_react_file
    , get_response
    )

# DATA_FOLDER = Path("./data") / "esyn_corpus_resolved"
# DATA_FOLDER = Path("./data") / "small_datasets_resolved" / "electrosynthesis_resolved"
DATA_FOLDER = Path("./data") / "organic_synthesis_photocatalysis_resolved" / "organic_synthesis_resolved"
DATA_FILES = list(DATA_FOLDER.glob("*.json"))
RESULTS_FOLDER = DATA_FOLDER / "results"
ITERATOR_STR = "Now let's go for optimize iteration number {number}"

def build_rag_subs(graph, sub_dict):
    vname_fn = lambda x: ', '.join(get_vnamelist_from_db(x, graph)) or None
    out_dict = {}
    for k, v in sub_dict.items():
        if (resp := vname_fn(v)) is not None:
            out_dict[k] = resp
    return out_dict


def get_json_from_react(
    json_react_path: Path | str
) -> list[dict[str, str]]:
    connection = connect(
        "ws://localhost"
        , 8182
        , 'g')
    graph = get_traversal(connection)

    rag_dict = build_rag_subs(graph, {
        # "material": Material,
        "atmosphere": Atmosphere,
        # "material_family": MaterialFamily
    })
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

def generate_pool_sizes(total_files, max_workers=30, steps=20, start=1):
    increasing_sizes = np.round(
        np.linspace(start, max_workers ** 0.6, steps) ** (1 / 0.6)).astype(int).tolist()
    increasing_sizes = [min(x, max_workers) for x in increasing_sizes]
    remaining_files = total_files - sum(increasing_sizes)
    if remaining_files > 0:
        increasing_sizes.extend(repeat(max_workers, remaining_files))
    if (tot := sum(increasing_sizes)) > total_files:
        increasing_sizes[-1] -= tot - total_files

    return increasing_sizes


# def pool_proxy(n): get_json_from_react(DATA_FILES[n])

def exec(files_set, max_workers=30, steps=5, start=1):
    pool_sizes = generate_pool_sizes(
        total_files=len(files_set)
        , steps=steps
        , max_workers=max_workers
        , start=start
    )
    dynamic_pool_execution(files_set, pool_sizes)


# with Pool(30) as p:
#     p.map(
#         get_json_from_react
#         , DATA_FILES
#     )

if __name__ == "__main__":
    exec(DATA_FILES, max_workers=8, steps=12)
    # get_json_from_react(DATA_FILES[2])
