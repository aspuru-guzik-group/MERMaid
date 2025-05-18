import os
import json
import argparse
import sys
from pathlib import Path
# from methods_dataraider import RxnOptDataProcessor
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataraider.processor_info import DataRaiderInfo
from dataraider.reaction_dictionary_formating import construct_initial_prompt
from dataraider.process_images import batch_process_images, clear_temp_files
from dataraider.filter_image import filter_images
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

load_dotenv()
ckpt_path = hf_hub_download("yujieq/RxnScribe", "pix2seq_reaction_full.ckpt")
# package_dir = os.path.dirname(__file__)  # This points to the current file's directory
        
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
    This function orchestrates loading the configuration, initializing the DataRaider info object,
    constructing custom prompts, and processing the reaction images. Temporary files are cleared
    at the end of the processing.

    :return: None
    """
    parser = argparse.ArgumentParser(description="Run DataRaider to process reaction data from images.")

    parser.add_argument("--config", type=str, help="Path to the configuration file", default=None)
    parser.add_argument("--image_dir", type=str, help="Directory containing images to process", default=None)
    parser.add_argument("--prompt_dir", type=str, help="Directory containing prompt files", default=None)
    parser.add_argument("--json_dir", type=str, help="Directory to save processed JSON data", default=None)
    parser.add_argument("--keys", type=str, nargs='+', help="List of keys to extract", default=None)
    parser.add_argument("--new_keys", type=str, nargs='+', help="List of new keys for data extraction", default=None)
    # parser.add_argument("--api_key", type=str, help="API key", default=None)
    
    args = parser.parse_args()

    if args.config:
        config = load_config(Path(args.config))
    else:
        package_dir = Path(__file__).resolve().parent.parent
        config_path = package_dir / "scripts" / "startup.json"
        config = load_config(config_path) if config_path.exists() else {}

    image_dir = Path(args.image_dir) if args.image_dir else Path(config.get('image_dir') or config.get('default_image_dir'))
    prompt_dir = Path(args.prompt_dir) if args.prompt_dir else Path(config.get('prompt_dir', "Prompts"))
    json_dir = Path(args.json_dir) if args.json_dir else Path(config.get('json_dir') or config.get('default_json_dir'))
    
    keys = config.get('keys', ["Entry", "Catalyst", "Ligand", "Cathode", "Solvents", "Footnote"])
    new_keys = config.get('new_keys', None)
    # api_key = config.get('api_key', None)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("API key not found. Please set the OPENAI_API_KEY environment variable.")
        return

    info = DataRaiderInfo(api_key=api_key, device="cpu", ckpt_path=ckpt_path)
    
    # Construct the initial reaction data extraction prompt
    print('\n############################ Starting up DataRaider ############################ ')
    print("Constructing your custom reaction data extraction prompt")
    construct_initial_prompt(prompt_dir, keys, new_keys)
    print('Filtering relevant images.')
    filter_images(info, prompt_dir, "filter_image_prompt", image_dir)
    print('\nProcessing relevant images.\n')
    batch_process_images(info, image_dir, prompt_dir, "get_data_prompt", "update_dict_prompt", json_dir)
    print()
    print('\nClearing temporary files and custom prompts')
    clear_temp_files(prompt_dir, image_dir)


if __name__ == "__main__":
    main()