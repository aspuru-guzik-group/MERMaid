import os
from TF_to_json_methods import RxnOptDataProcessor
from huggingface_hub import hf_hub_download
import tempfile

ckpt_path = hf_hub_download("yujieq/RxnScribe", "pix2seq_reaction_full.ckpt")

def tables_figures_to_json(keys: list, new_keys: dict, input_dir: str, output_dir: str, api_key: str):
    """
    Performs reaction optimization to retrieve the reaction optimization dictionary, SMILES and reaction conditions
    Args:
        keys (list): reaction keys for reaction optimization dictionary
        new_keys (dict): new reaction keys that can be added, once added does not need to be added again
        input_dir (str): input directory for where raw images are located
        output_dir (str): output directory for reaction information
        api_key (str): api key for openai chatgpt
    """
    processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu', api_key=api_key)    
    new_prompt_contents, data_prompt_file_name = processor.construct_intial_prompt(keys, new_keys, output_dir)
    package_dir = os.path.dirname(__file__)  # This points to the current file's directory
    # Define where to store temporary files inside a subdirectory, e.g., "temp_files"
    temp_dir = os.path.join(package_dir, "temp_files")
    # Create the subdirectory if it doesn't exist
    os.makedirs(temp_dir, exist_ok=True)
    
    with tempfile.NamedTemporaryFile(mode="w+", dir=temp_dir, delete=True) as temp_file:
        temp_file.write("\n".join(new_prompt_contents))
        prompt_directory = temp_dir
        update_dict_prompt = os.path.join(package_dir, "../Prompts/update_dict_prompt")
        # assume cropped_images exists, we will clean it out later
        cropped_image_directory = os.path.join(package_dir, "cropped_images")
        
        processor.batch_crop_image(input_dir, cropped_image_directory)
        for file in os.listdir(input_dir):
            if file.endswith('.png'):
                image_name = file.removesuffix('.png')
                print(f"Extracting SMILES from {image_name}")
                processor.batch_process_data(prompt_directory, data_prompt_file_name, 
                                            update_dict_prompt, cropped_image_directory, 
                                            output_dir, output_dir)
        
        # clean up the cropped image directory
        for filename in os.listdir(cropped_image_directory):
            file_path = os.path.join(cropped_image_directory, filename)
            # Check if it's a file (and not a subdirectory)
            if os.path.isfile(file_path):
                os.remove(file_path)
        

if __name__ == "__main__":
    keys = ["Entry", "Catalyst", "Ligand", "Cathode", "Solvents"]
    new_keys = {"Products" : "This is place holder text"}
    input_dir = "directory/to/input/"
    output_dir = "directory/to/output/"
    tables_figures_to_json(keys=keys, new_keys=new_keys, input_dir="./test/", output_dir="./", api_key="...")


