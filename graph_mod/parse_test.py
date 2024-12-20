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
) -> str | None:
    try:
        with open(path, 'r') as f:
            return json.loads(''.join(f.readlines()[1:-1]))
    except:
        return None

FAILED_TYPE=[]
FAILED_KEY=[]
def parse_or_skip(
    reaction: list[dict[Any, Any]]
) -> list[Connection] | None:
    connections = []
    for item in reaction:
        try:
            connections.append(Connection.from_dict(item))
        except TypeError:
            print(f"Reaction {item} failed, skipping")
            FAILED_TYPE.append(item)
            continue
        except KeyError:
            print(f"Reaction {item} failed, skipping")
            FAILED_KEY.append(item)
            continue
    return connections

def filter_none(xs): return filter(lambda x: x is not None, xs)
    

rfiles = list(filter_none(map(read_and_clean_file, RESULT_FILES)))
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
