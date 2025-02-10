import torch
from rxnscribe import RxnScribe #need separate installation from https://github.com/thomas0809/RxnScribe 
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
import regex as re
import mermaid.postprocess as pp
import shutil

class RxnOptDataProcessor:
    """
    Handles image processing tasks to extract reaction optimization-related data from images.
    """
    def __init__(self, 
                 ckpt_path:str, 
                 api_key:str,
                 vlm_model = "gpt-4o-2024-08-06",
                 device='cpu'):
        self.api_key = api_key
        self.vlm_model = vlm_model
        self.model = RxnScribe(ckpt_path, device=torch.device(device)) # initialize RxnScribe to get SMILES 
    
    
    #TODO
    def is_reaction_diagram(self, 
                            image_name:str, 
                            image_directory:str):
        """
        filters to see if image contains reaction information 
        """
        pass
    
    
    def crop_image(self, 
                   image_name:str, 
                   image_directory:str, 
                   min_segment_height=120): 
        """
        Adaptively crop a given figure into smaller subfigures before 
        passing to VLM based on image length

        parameters: 
        image_name: base image name
        image_directory: root directory where original images are saved 
        min_segment_height: minimum height of each segmented subfigure
        """
        cropped_image_directory = os.path.join(image_directory, "cropped_images") #create temporary directory to save cropped images
        os.makedirs(cropped_image_directory, exist_ok=True)
        
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
                self.crop_image(image_name, input_directory, cropped_image_directory, min_segment_height)
    
    
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
        image_paths = glob.glob(os.path.join(image_directory, f"cropped_images/{image_name}_*.png"))
        if not image_paths:
            print(f"No subimages found for {image_name}")
            return
    
        base64_images = [self.encode_image(image_path) for image_path in image_paths]

        # Get user prompt file
        user_prompt_path = os.path.join(prompt_directory, f"{get_data_prompt}.txt")
        with open(user_prompt_path, "r") as file:
            user_message = file.read().strip()

        # Get response file paths
        image_caption_path = os.path.join(image_directory, f"{image_name}.txt")
        response_path = os.path.join(json_directory, f"{image_name}.json")

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

        # API request headers and payload
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.vlm_model,
            "messages": messages,
            "max_tokens": 4000
        }

        # Send API request
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()  # Raise error if the request failed
            reaction_data = response.json()['choices'][0]['message']['content']

            # Save responses
            with open(response_path, 'w') as json_file:
                json.dump(reaction_data, json_file)
            print(f"Reaction dictionary extracted!")

            # Clean response: 
            try: 
                self.reformat_json(response_path)
                print(f"{response_path}: Reaction data cleaned!")

            except Exception as e: 
                print(f"{response_path}: Reaction data not cleaned. Error: {e}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")

    
    def update_dict_with_footnotes(self, 
                    prompt_directory:str, 
                    update_dict_prompt:str, 
                    image_name:str, 
                    json_directory:str):
        """
        updates the reaction dictionary with information from the footnote dictionary
        """
        # Get user prompt file
        user_prompt_path = os.path.join(prompt_directory, f"{update_dict_prompt}.txt")
        with open(user_prompt_path, "r") as file:
            user_message = file.read().strip()
        
        # Get Json file
        json_path = os.path.join(json_directory, f"{image_name}.json")
        with open(json_path, "r") as file2:
            json_dict = file2.read().strip()

        # Replace existing json file with updated json file
        response_path = json_path

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
            "model": self.vlm_model,
            "messages": messages,
            "max_tokens": 4000
        }

        # Send API request
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()  # Raise error if the request failed
            reaction_data = response.json()['choices'][0]['message']['content']

            # Save response
            with open(response_path, 'w') as json_file:
                json.dump(reaction_data, json_file)
            print(f"Reaction dictionary has been updated with footnote description!")

            # Clean response
            try:
                self.reformat_json(response_path)
                print(f"{response_path}: Updated reaction dictionary has been cleaned.")
            except Exception as e:
                print(f"{response_path}: Updated reaction dictionary not cleaned.Error: {e}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error during API request: {e}")

    
    def update_dict_with_smiles(self, 
                       image_name:str, 
                       image_directory:str, 
                       json_directory:str):
        """
        Use RxnScribe to get reactants and product SMILES and combine reaction dictionary with reaction SMILES
        """
        image_file = os.path.join(image_directory, f"{image_name}.png")
        reactions = []

        # Extract reactant and product SMILES
        try: 
            predictions = self.model.predict_image_file(image_file, molscribe=True, ocr=False)
            for prediction in predictions: 
                reactant_smiles = [reactant.get('smiles') for reactant in prediction.get('reactants', []) if 'smiles' in reactant]
                product_smiles = [product.get('smiles') for product in prediction.get('products', []) if 'smiles' in product]
                reactions.append({'reactants': reactant_smiles, 'products': product_smiles})
        
        except Exception as e: 
            reactions.append({'reactants': ["N.R"], 'products': ["N.R"]})
        
        #Clean extracted cleaned reaction SMILES 
        if not reactions or 'NR' in reactions[0].get('reactants', '') or 'NR' in reactions[0].get('products', ''):
            reactants = 'NR' if not reactions or 'NR' in reactions[0].get('reactants', '') else reactions[0]['reactants']
            products = 'NR' if not reactions or 'NR' in reactions[0].get('products', '') else reactions[0]['products']
        else:
            reactants = reactions[0].get('reactants', 'NR')
            products = reactions[0].get('products', 'NR')

        # Update reaction dictionary with reaction SMILES 
        json_path = os.path.join(json_directory, f"{image_name}.json")
        with open(json_path, 'r') as file: 
            opt_dict = json.load(file)
        opt_data = opt_dict["Optimization Runs"]

        updated_dict = {
            "SMILES": {
                "reactants": reactants, 
                "products": products
            }, 
            "Optimization Runs": opt_data
        }

        output_path = os.path.join(json_directory, f"{image_name}.json")
        with open(output_path, 'w') as output_file: 
            json.dump(updated_dict, output_file, indent = 4)
        print(f'{image_name} reaction dictionary updated with reaction SMILES')
    

    #TODO (integrate postprocess.py code here)
    def postprocess_dict(self, 
                         image_name:str,
                         json_directory:str):
        """ 
        1. converts common chemical names to smiles using pubchem and user-defined dictionary
        2. unifies format for mixed solvent systems
        """
        pass
    
    
    def process_indiv_images(self,
                            image_name:str,
                            image_directory:str,
                            prompt_directory:str,
                            get_data_prompt:str,
                            update_dict_prompt:str,
                            json_directory:str, 
                            min_segment_height:int=120):
        """ 
        Process individual images to extract reaction information
        
        """
        print(f'Extracting reaction information from {image_name}!')
        print('Cropping image...')
        self.crop_image(image_name, image_directory, min_segment_height)
        print('Images cropped. Passing subimages through DataRaider')          
        self.adaptive_get_data(prompt_directory, get_data_prompt, image_name, image_directory, json_directory)
        print('Raw reaction dictionary extracted. Updating with footnote information...')
        self.update_dict_with_footnotes(prompt_directory, update_dict_prompt, image_name, json_directory)
        print('Footnote information updated. Extracting reaction SMILES...')
        self.update_dict_with_smiles(image_name, image_directory, json_directory)
        print('Reaction SMILES extracted. Postprocessing reaction dictionary...')
        self.postprocess_dict(image_name, json_directory)
        print(f'{image_name} processed!')
        print('-----------------------------------')
    
    
    def batch_process_images(self,
                             image_directory:str,
                             prompt_directory: str, 
                             get_data_prompt:str, 
                             update_dict_prompt:str,
                             json_directory:str
                             ): 
        """
        Batch process images to extract reaction information
        """
        for file in os.listdir(image_directory):
            if (file.endswith(".png")):
                image_name = file.removesuffix('.png')
                self.process_indiv_images(image_name, image_directory, prompt_directory, get_data_prompt, update_dict_prompt, json_directory)
        print("DataRaider -- Mission Accomplished. All images processed!")
    
    
    def construct_initial_prompt(self, 
                                 opt_run_keys: list, 
                                 new_run_keys: dict):
        """
        Creates a get_data_prompt with opt_run_keys key-value pairs embedded into it
        Uses <INSERT_HERE> as the location tag for inserting keys
        Saves the new prompt to a file named get_data_prompt.txt inside the Prompts directory.
        """
        
        marker = "<INSERT_HERE>"
        package_dir = os.path.dirname(__file__)

        # retrieve all inbuilt keys
        inbuilt_key_pair_file_path = os.path.join(package_dir, "../Prompts/inbuilt_keyvaluepairs.txt")
        with open(inbuilt_key_pair_file_path, "r") as inbuilt_file:
            inbuilt_key_pair_file_contents = inbuilt_file.readlines()
        
        # get the list of optimization run dictionary key value pairs
        # add the newly defined keys first
        # opt_run_list = ["\"" + key + "\": " + new_run_keys[key] + "\n" for key in new_run_keys]
        opt_run_list = [f'"{key}": "{new_run_keys[key]}"\n' for key in new_run_keys]
        for line in inbuilt_key_pair_file_contents:
            if not line.strip():
                continue
            key_pattern = r'"([^"]*)"'
            possible_keys = re.findall(key_pattern, line)
            if not possible_keys:
                continue
            if all(key not in opt_run_keys for key in possible_keys):
                continue
            opt_run_list.append(line)
        
        base_prompt_file_path = os.path.join(package_dir, "../Prompts/base_prompt.txt")
        with open(base_prompt_file_path, "r") as base_prompt_file:
            base_prompt_file_contents = base_prompt_file.readlines()

        new_prompt_file_contents = []
        for line in base_prompt_file_contents:
            if marker in line: 
                new_prompt_file_contents.extend(opt_run_list)
            else: 
                new_prompt_file_contents.append(line)

            # if marker not in line:
            #     new_prompt_file_contents.append(line)
            # else:
            #     new_prompt_file_contents.append("\n".join(opt_run_list))
        
        # saves the defined prompt as get_data_prompt
        new_prompt_file_path = os.path.join(package_dir, "../Prompts/get_data_prompt.txt")
        with open(new_prompt_file_path, "w") as new_prompt_file:
            new_prompt_file.writelines(new_prompt_file_contents)
        print(f"Prompt file created with custom keys!")


    def clear_temp_files(self, 
                         prompt_directory:str, 
                         image_directory:str):
        """
        Removes temporary files (cropped images)
        """
        cropped_image_directory = os.path.join(image_directory, "cropped_images")
        if os.path.exists(cropped_image_directory) and os.path.isdir(cropped_image_directory):
            shutil.rmtree(cropped_image_directory)
            print("Temporary files and 'cropped_images' directory removed!")
        else:
            print("No temporary files to remove!")

        custom_prompt_path = os.path.join(prompt_directory, "get_data_prompt.txt")
        if os.path.exists(custom_prompt_path):
            os.remove(custom_prompt_path)
            print("Custom prompt file removed!")
        else:
            print("No custom prompt file to remove!")