import argparse
from pathlib import Path
import json
import subprocess
import os
#from enum import auto, StrEnum
from enum import Enum, auto 

from shutil import copyfile

SCRIPT_PATH = Path(os.path.abspath(__file__))
CFG_PATH = SCRIPT_PATH.parent / "startup.json"

# class Commands(StrEnum):
#     RUN = auto()
#     CFG = auto()

class Commands(Enum):
    RUN = auto()
    CFG = auto()
    
    def __str__(self):
        return self.name

def run_subprocess(module_name, opt_args=None, python=True):
    """
    Runs a Python script as a subprocess.

    :param module_name: Name of the module to run.
    :type module_name: str
    :param opt_args: List of command-line arguments to pass to the script (optional).
    :type opt_args: list, optional
    :param python: Wether or not use python to execute the script
    :type python: bool, optional
    :return: None
    """
    if python:
        cmd = ["python", module_name]
    else:
        cmd = [module_name]
    if opt_args:
        cmd += opt_args
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(f"\n===== {module_name} Output =====\n")
    print(result.stdout)

    if result.stderr:
        print(f"\n===== {module_name} Errors =====\n")
        print(result.stderr)


def load_json_config(json_path):
    """Load argument settings from a JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def json_to_arg_list(config):
    """Convert JSON config to a list mimicking CLI arguments."""
    arg_list = []
    for key, value in config.items():
        key_arg = f"--{key}"  # Convert to argparse format
        if isinstance(value, list):  # Handle list arguments
            arg_list.extend([key_arg] + [str(v) for v in value])
        elif isinstance(value, bool):  # Handle boolean flags
            if value:
                arg_list.append(key_arg)
        else:  # Normal key-value pairs
            arg_list.extend([key_arg, str(value)])
    return arg_list

    
def build_main_argparser() -> argparse.ArgumentParser:
    main_parser = argparse.ArgumentParser(description="Mermaid runs.")
    subparsers = main_parser.add_subparsers(
        title="Commands",
        description="Available commands",
        help="Description",
        dest="command",
        required=True
    )
    subparsers.required = True

    run_parser = subparsers.add_parser(
        Commands.RUN.name,
        help="Run mermaid pipeline (visualheist, dataraider, kgwizard sequentially)"
    )

    run_parser.add_argument(
        "-c", "--config",
        type=Path,
        default=CFG_PATH,
        help="Path to the configuration file"
    )

    cfg_parser = subparsers.add_parser(
        Commands.CFG.name,
        help="Output a configuration file"
    )

    cfg_parser.add_argument(
        "out_location",
        type=Path,
        help="Path to the configuration file"
    )

    return main_parser

def exec_cfg(args):
    copyfile(CFG_PATH, args.out_location)

def exec_run(args):
    cfg = load_json_config(args.config)

    # print("\n### Running VisualHeist ###\n")
    # run_subprocess("scripts/run_visualheist.py", python=True)
    # print("\n### Done running VisualHeist ###\n")
    
    # print("\n### Running DataRaider ###\n")
    # run_subprocess("scripts/run_dataraider.py", python=True)
    # print("\n### Done running DataRaider ###\n")
    
    kgwizard_args = [
        "transform",
        cfg["json_dir"],
        "--output_dir", cfg["json_dir"] + "results/",
        "--output_file", cfg["graph_dir"] + f"/{cfg['kgwizard']['graph_name']}.graphml",
    ]
    kgwizard_args += json_to_arg_list(cfg["kgwizard"])

    print("\n### Running KGWizard ###\n")
    run_subprocess("kgwizard", kgwizard_args, python=True)
    print("\n### Done running KGWizard ###\n")


def main():
    """
    Runs VisualHeist, DataRaider and KGWizard sequentially.

    :return: None
    """
    parser = build_main_argparser()
    args = parser.parse_args()

    if args.command == Commands.RUN.name:
        exec_run(args)
    elif args.command == Commands.CFG.name:
        exec_cfg(args)


    # match args.command:
    #     case Commands.RUN:
    #         exec_run(args)
    #     case Commands.CFG:
    #         exec_cfg(args)

if __name__ == "__main__":
    main()
