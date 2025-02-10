import os
import shutil

root_dir = "./output/output-retrained486-large"
output_dir = "./output/output-retrained486-large"

for subdir_name in os.listdir(root_dir):
	subdir_path = os.path.join(root_dir, subdir_name)
	
	if os.path.isdir(subdir_path):
		for filename in os.listdir(subdir_path):
			file_path = os.path.join(subdir_path, filename)
			
			new_filename = f"{subdir_name}_{filename}"
			new_filepath = os.path.join(output_dir, new_filename)
			
			shutil.copy(file_path, new_filepath)
			
print("File renaming complete") 