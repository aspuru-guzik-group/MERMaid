import json
from itertools import chain
from pathlib import Path
from schema import *
from janus import *

DATA_FOLDER = Path("./data") / "esyn_corpus_resolved"
RESULTS_FOLDER = DATA_FOLDER / "results"
RESULT_FILES = list(RESULTS_FOLDER.glob("*.json"))

def read_and_clean_file(
    path: Path | str
) -> str:
    with open(path, 'r') as f:
         return json.loads(''.join(f.readlines()[1:-1]))

def parse_or_skip(
    reaction: list[str]
) -> Connection | None:
    try:
        return list(map(Connection.from_dict, reaction))
    except TypeError:
        print(f"Reaction {reaction[0]} failed, skipping")
    except KeyError:
        print(f"Reaction {reaction[0]} failed, skipping")
    return None
    
    

rfiles = list(map(read_and_clean_file, RESULT_FILES))
conns = list(chain.from_iterable(filter(lambda x: x is not None,
               (map(parse_or_skip, rfiles)))))

connection = connect(
    "ws://localhost"
    , 8182
    , 'g')
graph = get_traversal(connection)

for item in conns:
    try:
        add_connection(item, graph)
    except TypeError:
        add_connection(item, graph)
    except:
        continue
