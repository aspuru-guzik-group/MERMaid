import os
from .processor_info import DataRaiderInfo
from .image_cropping import crop_image
from .api_access import adaptive_get_data, update_dict_with_footnotes
from .reaction_dictionary_formating import update_dict_with_smiles, postprocess_dict
import shutil
"""
Contains high level functions that process images
"""

    
def process_indiv_images(
                        info: DataRaiderInfo,
                        image_name:str,
                        image_directory:str,
                        prompt_directory:str,
                        get_data_prompt:str,
                        update_dict_prompt:str,
                        json_directory:str, 
                        min_segment_height:int=120):
    """Process individual images to extract reaction information

    :param image_name: Name of image
    :type image_name: str
    :param image_directory: Root directory where the original images are stored
    :type image_directory: str
    :param prompt_directory: Directory path to user message prompt
    :type prompt_directory: str
    :param get_data_prompt: File name of user message prompt to get reaction conditions
    :type get_data_prompt: str
    :param update_dict_prompt: Directory path to update message prompt
    :type update_dict_prompt: str
    :param json_directory: Path to directory of reaction dictionary
    :type json_directory: str
    :param min_segment_height: Minimum height of each segmented subfigure, defaults to 120, defaults to 120
    :type min_segment_height: int
    
    :return: Returns nothing, all data saved in JSON
    :rtype: None
    """
    
    print(f'Extracting reaction information from {image_name}.')
    print('Cropping image...')
    crop_image(image_name, image_directory, min_segment_height)
    print('Images cropped. Passing subimages through DataRaider...')          
    adaptive_get_data(info, prompt_directory, get_data_prompt, image_name, image_directory, json_directory)
    print('Updating with footnote information...')
    update_dict_with_footnotes(info, prompt_directory, update_dict_prompt, image_name, json_directory)
    print('Extracting reaction SMILES...')
    update_dict_with_smiles(info, image_name, image_directory, json_directory)
    print('Postprocessing reaction dictionary...')
    postprocess_dict(image_name, json_directory)
    print(f'{image_name} cleaned and saved.')
    print('-----------------------------------')


def batch_process_images(
                        info: DataRaiderInfo,
                        image_directory:str,
                        prompt_directory: str, 
                        get_data_prompt:str, 
                        update_dict_prompt:str,
                        json_directory:str
                        ): 
    """
    Batch process images to extract reaction information
    
    :param image_directory: Root directory where the original images are stored
    :type image_directory: str
    :param prompt_directory: Directory path to user message prompt
    :type prompt_directory: str
    :param get_data_prompt: File name of user message prompt to get reaction conditions
    :type get_data_prompt: str
    :param update_dict_prompt: Directory path to update message prompt
    :type update_dict_prompt: str
    :param json_directory: Path to directory of reaction dictionary
    :type json_directory: str
    
    :return: Returns nothing, all data saved in JSON
    :rtype: None
    """
    for file in os.listdir(image_directory):
        if (file.endswith(".png")):
            image_name = file.removesuffix('.png')
            try: 
                process_indiv_images(info, image_name, image_directory, prompt_directory, get_data_prompt, update_dict_prompt, json_directory)
            except: 
                continue
    print()
    print("DataRaider -- Mission Accomplished. All images processed!")

def clear_temp_files(
                    prompt_directory:str, 
                    image_directory:str):
    """Removes temporary files (cropped images)

    :param prompt_directory: Directory path to user message prompt
    :type prompt_directory: str
    :param image_directory: Root directory where the original images are stored
    :type image_directory: str
    """
    cropped_image_directory = os.path.join(image_directory, "cropped_images")
    if os.path.exists(cropped_image_directory) and os.path.isdir(cropped_image_directory):
        shutil.rmtree(cropped_image_directory)
        print("Temporary files and 'cropped_images' directory removed.")
    else:
        print("No temporary files to remove.")

    custom_prompt_path = os.path.join(prompt_directory, "get_data_prompt.txt")
    if os.path.exists(custom_prompt_path):
        os.remove(custom_prompt_path)
        print("Custom prompt file removed.")
    else:
        print("No custom prompt file to remove.")