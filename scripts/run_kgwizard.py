import json
import argparse
from pathlib import Path
import subprocess


def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    config_file = Path(config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)
    script_dir = config_file.parent
    parent_dir = script_dir.parent
    for key in ['default_image_dir', 'default_json_dir', 'default_graph_dir']:
        val = config.get(key)
        if val and not Path(val).is_absolute():
            config[key] = str((parent_dir / val).resolve())
    return config

def main():
    """
    This function orchestrates loading the configuration, constructing custom prompts of KGWizard
    """
    parser = argparse.ArgumentParser(description="Convert information into a graph databse with KGWIzard.")
    parser.add_argument("--config", type=str, help="Path to the configuration file", default=None)
    
    cli_args = parser.parse_args()
    
    if cli_args.config:
        config = load_config(Path(cli_args.config))

    else:
        package_dir = Path(__file__).resolve().parent.parent
        config_path = package_dir / "scripts" / "startup.json"
        config = load_config(config_path) if config_path.exists() else {}
    
    kgwizard_config = config.get("kgwizard")
    command = kgwizard_config.get("command")
    
    if command == "transform":
        json_dir = config.get('json_dir')
        output_file = kgwizard_config.get("output_file")
        output_dir = kgwizard_config.get("output_dir")
        schema = kgwizard_config.get("schema")
        sub_dict = kgwizard_config.get("substitutions")
        substitutions = [f"{k}:{v}" for k, v in sub_dict.items()]
        
        cli_args = [command, json_dir, "--output_file", output_file, "--output_dir", output_dir, "--schema", schema]
        if len(substitutions) > 0:
            cli_args += ["--substitutions"] + substitutions
    
    else: # command == "parse"
        output_file = kgwizard_config.get("output_file")
        output_dir = kgwizard_config.get("output_dir")
        schema = kgwizard_config.get("schema")

        cli_args = [command, output_dir, "--output_file", output_file, "--schema", schema]

    subprocess.run(["kgwizard"] + cli_args)
    

if __name__ == "__main__":
    main()