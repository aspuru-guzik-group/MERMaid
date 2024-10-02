import json
import os

def combine_json_files(folder_path, output_filename):
    with open(os.path.join(folder_path, output_filename), 'a') as output_file:
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                with open(os.path.join(folder_path, filename), 'r') as file:
                    output_file.write(file.read())
                    output_file.write('\n')  # Add a newline between each JSON object
    
    print(f"Combined data saved to {os.path.join(folder_path, output_filename)}")

# Example usage
folder_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/TF_to_json/TEST-cropped/output_v5/token_count/"
output_filename = 'get_data_combined_token_count.json'
combine_json_files(folder_path, output_filename)
