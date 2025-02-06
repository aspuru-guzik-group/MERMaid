import torch
# from rxnscribe import RxnScribe #need separate installation from https://github.com/thomas0809/RxnScribe 
from huggingface_hub import hf_hub_download
import cv2
import math
import numpy as np
import os
from openai import OpenAI
import base64
import requests
import json
import json
import glob
import pubchempy as pcp
import regex as re


class RxnOptDataProcessor:
    """
    Handles image processing tasks to extract reaction optimization-related data from images.
    """
    def __init__(self, 
                 ckpt_path:str, 
                 api_key:str,
                 device='cpu'):
        self.api_key = api_key
        # self.model = RxnScribe(ckpt_path, device=torch.device(device)) # initialize RxnScribe to get SMILES 
    
    def crop_image(self, 
                   image_name:str, 
                   image_directory:str, 
                   cropped_image_directory:str, 
                   min_segment_height=120): 
        """
        Adaptively crop a given figure into smaller subfigures before 
        passing to VLM based on image length

        parameters: 
        image_name: base image name
        image_directory: root directory where original images are saved 
        cropped_image_directory: output directory to save cropped images 
        min_segment_height: minimum height of each segmented subfigure
        """
        def find_split_line(image, 
                            threshold, 
                            region_start, 
                            region_end, 
                            percentage_threshold, 
                            step_size):
            """
            Helper function to determine where to segment the figure
            """
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) # Convert the image to grayscale            
            _, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY) # Identify white pixels
            white_pixel_count = np.count_nonzero(thresh == 255, axis=1) 

            # Find the last line with >= the specified percentage of white pixels in the specified region
            split_line = region_end
            while split_line > region_start:
                min_white_pixels = int(percentage_threshold * len(thresh[split_line]))

                if white_pixel_count[split_line] >= min_white_pixels:
                    break
                split_line -= step_size

            return split_line if split_line > region_start else region_start

        def adaptive_split_lines(image, 
                                 first_split_line, 
                                 min_segment_height, 
                                 threshold, 
                                 percentage_threshold, 
                                 step_size):
            """
            Helper function to identify all the split lines for an image
            """
            
            # Calculate the remaining height after the first split line
            first_region_end = int(3/8 *len(image))
            remaining_height = image.shape[0] - first_region_end
            num_segments = math.ceil(remaining_height / min_segment_height)
            segment_height = remaining_height // num_segments  # Determine the approximate height of each segment

            split_lines = [first_split_line]  # Start with the first fixed split line
            region_start_list = [first_region_end] 

            for __ in range(1, num_segments):
                # Calculate dynamic region start and end for each segment
                region_start = region_start_list[-1]
                region_end = region_start + segment_height
                region_start_list.append(region_end)

                # Find the split line for the current region
                split_line = find_split_line(image, threshold, region_start, region_end, percentage_threshold, step_size)
                split_lines.append(split_line)

            return split_lines
        
        def segment_image(image, split_lines):
            """
            Helper function to crop image based on split lines
            """
            segments = []
            prev_line = 0

            for split_line in split_lines:
                segments.append(image[prev_line:split_line, :])
                prev_line = split_line

            segments.append(image[prev_line:, :]) # Add the final segment (from the last split line to the end of the image)

            return segments
        
        image_path = os.path.join(image_directory, f"{image_name}.png")
        image = cv2.imread(image_path)

        if image is None:
            print(f"Error: Image {image_name}.png not found.")
            return
        
        # Set parameters
        threshold = 254.8
        percentage_threshold = 0.995
        step_size = 10

        # Find the first split line within the first 1/4 of the image (usually the reaction diagram)
        region_start_1 = int(1/4 * len(image))
        region_end_1 = int(3/8 *len(image))
        first_split_line = find_split_line(image, threshold, region_start_1, region_end_1, percentage_threshold, step_size)

        try: 
            # Find adaptive split lines based on the remaining height after the first split line
            split_lines = adaptive_split_lines(image, first_split_line, min_segment_height, threshold, percentage_threshold, step_size)

            # Check if split lines are valid
            if len(split_lines) < 1:
                raise ValueError(f"Error: Unable to find valid split lines for {image_name}. Saving original image.")

            # Crop the image into segments
            segments = segment_image(image, split_lines)

            # Check if cropped segments have valid size
            valid_segments = 0
            for idx, segment in enumerate(segments): 
                if segment.size > 0:
                    cv2.imwrite(os.path.join(cropped_image_directory, f"{image_name}_{idx+1}.png"), segment)
                    valid_segments += 1
                else: 
                    print(f"Warning: Segment {idx+1} of {image_name} has zero size. Skipping.")
            
            if valid_segments == 0:
                raise ValueError(f"Error: No valid segments for {image_name}. Saving original image.")

        except Exception as e: 
            print(str(e))
            cv2.imwrite(os.path.join(cropped_image_directory, f"{image_name}_original.png"), image)

    def batch_crop_image(self, 
                         input_directory:str, 
                         cropped_image_directory:str, 
                         min_segment_height:float=120):
        """
        crop all images in a given directory 
        """
        # Create a directory to save the cropped segments
        os.makedirs(cropped_image_directory, exist_ok=True)

        for file in os.listdir(input_directory):
            if (file.endswith('.png')):
                image_name = file.removesuffix('.png')
                print(f"processing {image_name}")
                self.crop_image(image_name, input_directory, cropped_image_directory, min_segment_height)
        print(f'All images cropped and saved in {cropped_image_directory}')
    
    def reformat_json(self, 
                      input_file:str):
        """
        Clean and format JSON data by removing unwanted characters and ensuring proper JSON formatting
        """
        with open(input_file, 'r') as file:
            json_content = file.read()
            json_content = json_content.replace("\"```json\\n", '').replace('```"', '').strip()       
            json_content = json_content.replace('\\n', '').replace('\\"', '"')
            data = json.loads(json_content)
            formatted_json = json.dumps(data, indent=4)

        # Write the formatted JSON to the output file
        with open(input_file, 'w') as file:
            file.write(formatted_json)

    def adaptive_get_data(self, 
                          prompt_directory:str, 
                          get_data_prompt:str, 
                          image_name:str, 
                          image_directory:str, 
                          json_directory:str):
        """
        Outputs a reaction dictionary from all subfigures 

        Parameters: 
        prompt_directory: directory path to user message prompt
        get_data_prompt: file name of user message prompt to get reaction conditions
        image_name: base image name 
        image_directory: root directory where the original images are stored
        json_directory: output directory to save all output json files 

        """
        # Get all subfigures files 
        image_paths = glob.glob(os.path.join(image_directory, f"{image_name}_*.png"))
        if not image_paths:
            print(f"No subimages found for {image_name}")
            return
    
        base64_images = [self.encode_image(image_path) for image_path in image_paths]

        # Get user prompt file
        user_prompt_path = os.path.join(prompt_directory, f"{get_data_prompt}.txt")
        with open(user_prompt_path, "r") as file:
            user_message = file.read().strip()

        # Get image captions and response file paths
        image_caption_path = os.path.join(image_directory, f"{image_name}.txt")
        response_path = os.path.join(json_directory, f"{image_name}_response.json")
        token_path = os.path.join(f"{json_directory}/token_count/", f"{image_name}_tokencount.json") # token count is saved in a subfolder in json_directory

        # Create base message
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": user_message}]
        }]

        # Add each encoded image as a separate entry
        messages[0]["content"].extend({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
        } for base64_image in base64_images)
        
        # If the image caption file exists, append it to the messages content
        if os.path.exists(image_caption_path):
            with open(image_caption_path, "r") as file:
                image_caption = file.read().strip()
            messages[0]["content"].append({"type": "text","text": image_caption})
        else: 
            print('No caption found for ' + image_caption_path)

        # API request headers and payload
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "gpt-4o-2024-08-06",
            "messages": messages,
            "max_tokens": 4000
        }

        # Send API request
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()  # Raise error if the request failed
            reaction_data = response.json()['choices'][0]['message']['content']
            token_count = response.json()['usage']

            # Save responses
            with open(response_path, 'w') as json_file:
                json.dump(reaction_data, json_file)
            print(f"Reaction data saved to {response_path}!")

            with open(token_path, 'w') as token_file: 
                json.dump(token_count, token_file)
            print(f"Token count saved to {response_path}!")

            # Clean response: 
            try: 
                self.reformat_json(response_path)
                print(f"{response_path}: Reaction data cleaned.")

            except Exception as e: 
                print(f"{response_path}: Reaction data not cleaned. Error: {e}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")

    def update_dict(self, 
                    prompt_directory:str, 
                    update_dict_prompt:str, 
                    json_file:str, 
                    json_directory:str):
        
        # Get user prompt file
        user_prompt_path = os.path.join(prompt_directory, f"{update_dict_prompt}.txt")
        with open(user_prompt_path, "r") as file:
            user_message = file.read().strip()
        
        # Get Json file
        json_path = os.path.join(json_directory, f"{json_file}.json")
        with open(json_path, "r") as file2:
            json_dict = file2.read().strip()

        # Get response paths
        response_path = os.path.join(json_directory, f"{json_file}_updated.json")
        token_path = os.path.join(f"{json_directory}/token_count/", f"{json_file}_updated_tokencount.json")

        # Construct message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    },
                    {
                        "type": "text",
                        "text": json_dict
                    }              
                ]
            }
        ]

        # API request headers and payload
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "gpt-4o-2024-08-06",
            "messages": messages,
            "max_tokens": 4000
        }

        # Send API request
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()  # Raise error if the request failed
            reaction_data = response.json()['choices'][0]['message']['content']
            token_count = response.json()['usage']

            # Save response
            with open(response_path, 'w') as json_file:
                json.dump(reaction_data, json_file)

            print(f"Reaction data saved to {response_path}!")

            with open(token_path,'w') as token_file:
               json.dump(token_count, token_file)

            print(f"Token count saved to {token_path}!")
            
            # Clean response
            try:
                self.reformat_json(response_path)
                print(f"{response_path}: Reaction data cleaned.")
            except Exception as e:
                print(f"{response_path}: Reaction data not cleaned.Error: {e}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")

    # EDIT: Handle escape strings in smiles otherwise will have errors
    # def extract_smiles(self, 
    #                    image_name:str, 
    #                    image_directory:str, 
    #                    json_directory:str):
    #     """
    #     Use RxnScribe to get reactants and product SMILES
    #     """
    #     image_file = os.path.join(image_directory, f"{image_name}.png")
    #     reactions = []

    #     # Extract reactant and product SMILES
    #     if self.is_reaction_diagram(image_file):   
    #         try: 
    #             predictions = self.model.predict_image_file(image_file, molscribe=True, ocr=False)
            
    #             for prediction in predictions: 
    #                 #reactant_smiles = [reactant['smiles'] for reactant in prediction.get('reactants', [])]
    #                 #product_smiles = [product['smiles'] for product in prediction.get('products', [])]
    #                 reactant_smiles = [reactant.get('smiles') for reactant in prediction.get('reactants', []) if 'smiles' in reactant]
    #                 product_smiles = [product.get('smiles') for product in prediction.get('products', []) if 'smiles' in product]
    #                 reactions.append({'reactants': reactant_smiles, 'products': product_smiles})
            
    #         except Exception as e: 
    #             reactions.append({'reactants': ["N.R"], 'products': ["N.R"]})
            
    #         # Save SMILES list  
    #         smiles_path = os.path.join(json_directory, f"{image_name}_rxnsmiles.json")
    #         with open(smiles_path, 'w') as smiles_file: 
    #             json.dump(reactions, smiles_file)
    #     else:
    #         print(f"{image_name} is not a reaction diagram.")
    
    # EDIT: Handle NR SMILES dictionaries
    def update_dict_with_smiles(self, 
                                image_name:str, 
                                json_directory:str): 
        """
        Combine reaction dictionary with reaction SMILES
        """
        # load optimization runs dictionary 
        dict_path = os.path.join(json_directory, f"{image_name}_response_updated.json")
        with open(dict_path, "r") as file:
            opt_dict = json.load(file)
        opt_data = opt_dict["Optimization Runs"]

        # load reaction smiles list
        smiles_path = os.path.join(json_directory, f"{image_name}_rxnsmiles.json")
        with open(smiles_path, "r") as file2: 
            smiles_list = json.load(file2)
        
        if not smiles_list or 'NR' in smiles_list[0].get('reactants', '') or 'NR' in smiles_list[0].get('products', ''):
            reactants = 'NR' if not smiles_list or 'NR' in smiles_list[0].get('reactants', '') else smiles_list[0]['reactants']
            products = 'NR' if not smiles_list or 'NR' in smiles_list[0].get('products', '') else smiles_list[0]['products']
        else:
            reactants = smiles_list[0].get('reactants', 'NR')
            products = smiles_list[0].get('products', 'NR')

        # combine and save 
        updated_dict = {
            "SMILES": {
                "reactants": reactants, 
                "products": products
            }, 
            "Optimization Runs": opt_data
        }

        output_path = os.path.join(json_directory, f"{image_name}_full_opt_dictionary.json")
        with open(output_path, 'w') as output_file: 
            json.dump(updated_dict, output_file, indent = 4)

        print (f"Reaction optimization dictionary updated with reaction smiles for {image_name}")

    def batch_process_data(self, 
                           prompt_directory:str, 
                           get_data_prompt:str, 
                           update_dict_prompt:str, 
                           cropped_image_directory:str, 
                           json_directory:str, 
                           image_directory:str): 
        """
        Get the full reaction optimization dictionary for all images - reaction SMILES + reaction conditions        
        Should be able to streamline code further
        """
        # Extract reaction dictionary
        print('Extracting reaction dictionaries and reaction SMILES!')
        for file in os.listdir(image_directory):
            if (file.endswith(".png")):
                image_name = file.removesuffix('.png')
                print(f"processing {image_name}")
                # self.extract_smiles(image_name, json_directory)
                self.adaptive_get_data(prompt_directory, get_data_prompt, image_name, cropped_image_directory, json_directory)
        
        # Update reaction dictionary with footnote information 
        print("Updating reaction dictionaries with footnote information!")
        for file in os.listdir(json_directory):
            if (file.endswith(".json")):
                json_name = file.removesuffix('.json')
                print(f"updating {json_name}")
                self.update_dict(prompt_directory, update_dict_prompt, json_name, json_directory)

        # Update reaction dictionary with reaction SMILES
        print("Updating reaction dictionaries with reaction SMILES!") 
        for file in os.listdir(json_directory): 
            if (file.endswith("_response_updated.json")):
                file_name = file.removesuffix("_response_updated.json")
                self.update_dict_with_smiles(self, file_name, json_directory)

        print("All reaction dictionaries are extracted and saved - hopefully")
    
    def construct_intial_prompt(self, opt_run_keys: list, output_dir: str):
        """
        Creates a reaction optimization prompt with opt_run_keys key-value pairs embedded into it
        Assume that <INSERT_HERE> is the marker for inserting keys
        """
        
        marker = "<INSERT_HERE>"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        inbuilt_key_pair_file_path = os.path.join(script_dir, "../Prompts/inbuilt_keyvaluepairs.txt")
        base_prompt_file_path = os.path.join(script_dir, "../Prompts/base_prompt.txt")
        
        # get the list of optimization run dictionary key value pairs
        inbuilt_key_pair_file = open(inbuilt_key_pair_file_path, "r")
        opt_run_list = []
        for line in inbuilt_key_pair_file:
            if len(line) == 0:
                continue
            key_pattern = r'"([^"]*)"'
            possible_keys = re.findall(key_pattern, line)
            if len(possible_keys) == 0:
                continue
            key = possible_keys[0]
            if key not in opt_run_keys:
                continue
            opt_run_list.append(line)
            # append the empty string so it is easier to create new prompt file later
            opt_run_list.append("")
        inbuilt_key_pair_file.close()
        
        new_prompt_file_name = "rxn_opt_prompt"
        base_prompt_file = open(base_prompt_file_path, "r")
        new_prompt_file = open(output_dir + new_prompt_file_name + ".txt", "w")
        
        for line in base_prompt_file:
            if marker not in line:
                new_prompt_file.write(line)
            else:
                new_prompt_file.write("\n".join(opt_run_list))
            
        new_prompt_file.close()
        base_prompt_file.close()
        return new_prompt_file_name



class GraphJson(RxnOptDataProcessor):

    def pubchem_common_name_to_smiles(self, 
                                      common_name: str): 
        try: 
            c = pcp.get_cids(common_name, 'name')
            if len(c) ==1: 
                compound = pcp.Compound.from_cid(c[0])
                c_smiles = compound.isomeric_smiles
                return c_smiles, common_name
            else: 
                return None, common_name
        except: 
            return None, common_name

