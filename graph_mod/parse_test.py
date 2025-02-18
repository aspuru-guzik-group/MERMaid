import json
from itertools import chain, product
from pathlib import Path
from schema import *
from janus import *

# DATA_FOLDER = Path("./data") / "esyn_corpus_resolved"
# DATA_FOLDER = Path("./data") / "electrosynthesis_resolved"
DATA_FOLDER = Path("./data") / "organic_synthesis_photocatalysis_resolved" / "organic_synthesis_resolved"
# DATA_FOLDER = Path("./data") / "small_datasets_resolved" / "organic_synthesis_resolved"
# DATA_FOLDER = Path("./data") / "organic_synthesis_photocatalysis_resolved" / "photocatalysis_resolved"

DATA_FILES = list(DATA_FOLDER.glob("*.json"))
RESULTS_FOLDER = DATA_FOLDER / "results"
RESULT_FILES = list(RESULTS_FOLDER.glob("*.json"))


def skip_file(item):
    return any(map(
        lambda xs: xs[0] in xs[1]
        , product(
            (item.stem,)
            , map(lambda p: p.stem, RESULT_FILES))))

def read_and_clean_file(
    path: Path | str
) -> str | None:
    try:
        with open(path, 'r') as f:
            lines = f.readlines()
        for n, l in enumerate(lines):
            if "```json" in l:
                start = n + 1
            if "```" in l:
                stop = n
        return json.loads(''.join(lines[start:stop]))
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

def rag_exec(
    graph
    , file_name
):
    r_file = read_and_clean_file(file_name)
    if not r_file: return None
    if parsed := parse_or_skip(r_file):
        conns = list(filter(lambda x: x is not None, parsed))
        for item in conns:
            try:
                add_connection(item, graph)
            except TypeError:
                add_connection(item, graph)
            except:
                with open("errors.dat", 'w') as f:
                    f.write(f"{file_name}\n")
                continue

if __name__ == "__main__":
    rfiles = list(filter_none(map(read_and_clean_file, RESULT_FILES)))
    conns = list(chain.from_iterable(filter(lambda x: x is not None,
                   (map(parse_or_skip, rfiles)))))

    connection = connect(
        "ws://localhost"
        , 8182
        , 'g')
    graph = get_traversal(connection)

    for n, item in enumerate(conns):
        print(f"{n}/{len(conns)}")
        try:
            add_connection(item, graph)
        except TypeError:
            try:
                add_connection(item, graph)
            except:
                continue
        except:
            continue
