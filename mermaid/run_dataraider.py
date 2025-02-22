import os
import json
# from methods_dataraider import RxnOptDataProcessor
from dataraider.processor_info import DataRaiderInfo
from dataraider.reaction_dictionary_formating import construct_initial_prompt
from dataraider.process_images import batch_process_images, clear_temp_files
from huggingface_hub import hf_hub_download


ckpt_path = hf_hub_download("yujieq/RxnScribe", "pix2seq_reaction_full.ckpt")
package_dir = os.path.dirname(__file__)  # This points to the current file's directory
        
def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)
    

if __name__ == "__main__":
    # Load the configuration from the file
    config = load_config('./mermaid/startup.json')

    # Use the default configuration in the function call if unspecified 
    image_dir = config.get('image_dir', config.get('default_image_dir'))
    prompt_dir = config.get('prompt_dir', "./Prompts")
    get_data_prompt = "get_data_prompt"
    update_dict_prompt = "update_dict_prompt"
    output_dir = config.get('json_dir', config.get('default_json_dir'))
    keys = config.get('keys', ["Entry", "Catalyst", "Ligand", "Cathode", "Solvents"])
    new_keys = config.get('new_keys', None)
    api_key = config.get('api_key', None)

    # Use the loaded configuration in the function call
    info = DataRaiderInfo(api_key=api_key, device="cpu", ckpt_path=ckpt_path)
    # processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu', api_key=api_key)
    print("Constructing your custom reaction data extraction prompt")
    construct_initial_prompt(keys, new_keys)
    # processor.construct_initial_prompt(keys, new_keys)
    print('######################## Starting up DataRaider ############################')
    batch_process_images(info, image_dir, prompt_dir, get_data_prompt, update_dict_prompt, output_dir)
    # processor.batch_process_images(image_dir, prompt_dir, get_data_prompt, update_dict_prompt, output_dir)
    print('Clearing temporary files and custom prompts')
    clear_temp_files(prompt_dir, image_dir)
    # processor.clear_temp_files(prompt_dir, image_dir)
