import os
import json
from methods_dataraider import RxnOptDataProcessor
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
    processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu', api_key=api_key)
    print("Constructing your custom reaction data extraction prompt")
    processor.construct_initial_prompt(keys, new_keys)
    print('######################## Starting up DataRaider ############################')
    processor.batch_process_images(image_dir, prompt_dir, get_data_prompt, update_dict_prompt, output_dir)
    print('Clearing temporary files and custom prompts')
    processor.clear_temp_files(prompt_dir, image_dir)
