import os
from TF_to_json_methods import RxnOptDataProcessor
from huggingface_hub import hf_hub_download

ckpt_path = hf_hub_download("yujieq/RxnScribe", "pix2seq_reaction_full.ckpt")
prompt_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/"
image_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST/"
json_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-cropped/"
cropped_image_directory = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-cropped"
get_data_prompt = "rxn_opt_prompt_v5_2"
update_dict_prompt = "rxn_opt_update_prompt_v3"

def main():
    processor = RxnOptDataProcessor(ckpt_path=ckpt_path, device='cpu')

    #batch crop images 
    processor.batch_crop_image(image_directory, cropped_image_directory)

    # Get reaction dictionaries
    for file in os.listdir(image_directory):
        if file.endswith('.png'):
            image_name = file.removesuffix('.png')
            print(f"Extracting SMILES from {image_name}")
            processor.batch_process_data(prompt_directory, get_data_prompt, 
                                         update_dict_prompt, cropped_image_directory, 
                                         json_directory, image_directory)


