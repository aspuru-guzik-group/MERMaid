import os
import json
import argparse
# from methods_dataraider import RxnOptDataProcessor
from dataraider.processor_info import DataRaiderInfo
from dataraider.reaction_dictionary_formating import construct_initial_prompt
from dataraider.process_images import batch_process_images, clear_temp_files
from huggingface_hub import hf_hub_download


ckpt_path = hf_hub_download("yujieq/RxnScribe", "pix2seq_reaction_full.ckpt")
package_dir = os.path.dirname(__file__)  # This points to the current file's directory
        
def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    with open(config_file, 'r') as f:
        return json.load(f)
    
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
    parser.add_argument("--api_key", type=str, help="API key", default=None)
    
    args = parser.parse_args()

    if args.config:
        config = load_config(args.config)
    else:
        package_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(package_dir, 'startup.json')
        config = load_config(config_path) if os.path.exists(config_path) else {}

    image_dir = args.image_dir or config.get('image_dir', config.get('default_image_dir'))
    prompt_dir = args.prompt_dir or config.get('prompt_dir', "./Prompts")
    json_dir = args.json_dir or config.get('json_dir', config.get('default_json_dir'))
    keys = args.keys or config.get('keys', ["Entry", "Catalyst", "Ligand", "Cathode", "Solvents"])
    new_keys = args.new_keys or config.get('new_keys', None)
    api_key = args.api_key or config.get('api_key', None)

    info = DataRaiderInfo(api_key=api_key, device="cpu", ckpt_path=ckpt_path)
    print(f'keys are {keys}')
    # Construct the initial reaction data extraction prompt
    print("Constructing your custom reaction data extraction prompt")
    construct_initial_prompt(keys, new_keys)
    print()
    print('############################ Starting up DataRaider ############################ ')
    batch_process_images(info, image_dir, prompt_dir, "get_data_prompt", "update_dict_prompt", json_dir)
    print()
    print('Clearing temporary files and custom prompts')
    clear_temp_files(prompt_dir, image_dir)


if __name__ == "__main__":
    main()


    # # Load the configuration from the file
    # config = load_config('./mermaid/startup.json')

    # # Use the default configuration in the function call if unspecified 
    # image_dir = config.get('image_dir', config.get('default_image_dir'))
    # prompt_dir = config.get('prompt_dir', "./Prompts")
    # get_data_prompt = "get_data_prompt"
    # update_dict_prompt = "update_dict_prompt"
    # output_dir = config.get('json_dir', config.get('default_json_dir'))
    # keys = config.get('keys', ["Entry", "Catalyst", "Ligand", "Cathode", "Solvents"])
    # new_keys = config.get('new_keys', None)
    # api_key = config.get('api_key', None)

    # # Use the loaded configuration in the function call
    # info = DataRaiderInfo(api_key=api_key, device="cpu", ckpt_path=ckpt_path)
    # # processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu', api_key=api_key)
    # print("Constructing your custom reaction data extraction prompt")
    # construct_initial_prompt(keys, new_keys)
    # # processor.construct_initial_prompt(keys, new_keys)
    # print('######################## Starting up DataRaider ############################')
    # batch_process_images(info, image_dir, prompt_dir, get_data_prompt, update_dict_prompt, output_dir)
    # # processor.batch_process_images(image_dir, prompt_dir, get_data_prompt, update_dict_prompt, output_dir)
    # print('Clearing temporary files and custom prompts')
    # clear_temp_files(prompt_dir, image_dir)
    # # processor.clear_temp_files(prompt_dir, image_dir)
