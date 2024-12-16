import json
from pathlib import Path
from oai import build_prompt, build_prompt_from_react, build_prompt_from_react_file, get_response

DATA_FOLDER = Path("./data") / "esyn_corpus_resolved"
DATA_FILES = list(DATA_FOLDER.glob("*.json"))
RESULTS_FOLDER = DATA_FOLDER / "results"
ITERATOR_STR = "Now let's go for optimize iteration number {number}"

def get_json_from_react(
    json_react_path: Path | str
) -> list[dict[str, str]]:
    json_react_path = Path(json_react_path)
    with open(json_react_path, 'r') as f:
        react_dict = json.load(f)
    optimization_runs = list(react_dict["Optimization Runs"].keys())
    messages = [build_prompt_from_react_file(
        path=json_react_path
        , study_name=json_react_path.stem)
    ]
    messages.append(get_response(messages))
    save_path = RESULTS_FOLDER / Path(str(json_react_path.stem) +  '_1' + '.json')
    with open(save_path, 'w') as f:
        f.write(messages[-1]["content"])
    for n in optimization_runs[1:]:
        messages.append(build_prompt(ITERATOR_STR.format(number=n)))
        messages.append(get_response(messages))
        save_path = RESULTS_FOLDER / Path(str(json_react_path.stem) +  f'_{n}' + '.json')
        with open(save_path, 'w') as f:
            f.write(messages[-1]["content"])
        print(f"iter: {n}")
    return messages


for item in range(0, 40):
    get_json_from_react(DATA_FILES[item])
