import os
from TF_to_json_methods import RxnOptDataProcessor
from huggingface_hub import hf_hub_download

ckpt_path = hf_hub_download("yujieq/RxnScribe", "pix2seq_reaction_full.ckpt")

def tf_to_json(keys: list, input_dir: str, output_dir: str, api_key: str):
    """
    Performs reaction optimization to retrieve the reaction optimization dictionary, SMILES and reaction conditions
    Args:
        keys (list): reaction keys for reaction optimization dictionary
        input_dir (str): input directory for where raw images are located
        output_dir (str): output directory for reaction information
        api_key (str): api key for openai chatgpt
    """
    processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu', api_key=api_key)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    get_data_prompt = processor.construct_intial_prompt(keys, output_dir)
    prompt_directory = output_dir
    update_dict_prompt = os.path.join(script_dir, "../Prompts/update_dict_prompt.txt")
     # assume cropped_images exists, we will clean it out later
    cropped_image_directory = os.path.join(script_dir, "../cropped_images")
    
    processor.batch_crop_image(input_dir, cropped_image_directory)
    for file in os.listdir(input_dir):
        if file.endswith('.png'):
            image_name = file.removesuffix('.png')
            print(f"Extracting SMILES from {image_name}")
            processor.batch_process_data(prompt_directory, get_data_prompt, 
                                         update_dict_prompt, cropped_image_directory, 
                                         output_dir, output_dir)

if __name__ == "__main__":
    tf_to_json(["Entry", "Reactants"], "../test/", "./")


# def main():
#     processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu')

#     #batch crop images 
#     processor.batch_crop_image(image_directory, cropped_image_directory)

#     # Get reaction dictionaries
#     for file in os.listdir(image_directory):
#         if file.endswith('.png'):
#             image_name = file.removesuffix('.png')
#             print(f"Extracting SMILES from {image_name}")
#             processor.batch_process_data(prompt_directory, get_data_prompt, 
#                                          update_dict_prompt, cropped_image_directory, 
#                                          json_directory, image_directory)


