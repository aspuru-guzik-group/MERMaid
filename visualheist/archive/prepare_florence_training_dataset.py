import os
import json
import random
import pandas as pd
from sklearn.model_selection import train_test_split

def convert_to_florence_format(coco_json_path, florence_output_path):
	"""
	converts coco dataset to florence dataset
	"""
	print("start converting coco annotations to florence format...")

	with open(coco_json_path, 'r') as file:
		data = json.load(file)

	category_dict = {category['id']: category['name'] for category in data['categories']}
	print("labels :", category_dict)
	
	img_dict = {}
	for img in data['images']:
		img_dict[img['id']] = {
			'width': img['width'],
			'height': img['height'],
			'file_name': img['file_name'],
			'annotations': [],
			'annotations_str': ""
		}

	annotation_dict = {annotation['image_id']: annotation['bbox'] for annotation in data['annotations']}

	def format_annotation(annotation):
		category_id = annotation['category_id']
		bbox = annotation['bbox'] # coco bbox format: [x, y, width, height]
		this_image_width = img_dict[int(annotation['image_id'])]['width']
		this_image_height = img_dict[int(annotation['image_id'])]['height']
		# normalize the numbers to be between 0 and 1 then multiplied by 1000.
		# forence 2 format: label<loc_{x1}><loc_{y1}><loc_{x2}><loc_{y2}>
		x1 = int(bbox[0] / this_image_width * 1000)
		y1 = int(bbox[1] / this_image_height * 1000)
		x2 = int((bbox[0] + bbox[2]) / this_image_width * 1000)
		y2 = int((bbox[1] + bbox[3]) / this_image_height * 1000)

		return f"{category_dict[category_id]}<loc_{x1}><loc_{y1}><loc_{x2}><loc_{y2}>"

	for annotation in data['annotations']:
		try:
			annotation_str = format_annotation(annotation)
			if annotation['image_id'] in img_dict:
				img_dict[annotation['image_id']]['annotations'].append(annotation_str)
		except:
			continue

	florence_data = []
	for img_id, img_data in img_dict.items():
		annotations_str = "".join(img_data['annotations'])

		if len(annotations_str) > 0:
			florence_data.append({
				"image": img_data['file_name'],
				"prefix": "<OD>",
				"suffix": annotations_str
			})
		else:
			# OPTIONAL: some images have no annotations, you can choose to ignore them
			# only randomly sample 5% of the images without annotations
			if random.random() < 0.05:
				florence_data.append({
					"image": img_data['file_name'],
					"prefix": "<OD>",
					"suffix": ""
				})

	print("total number of images:", len(florence_data))

	# save converted json
	with open(florence_output_path, 'w') as file:
		for entry in florence_data:
			json.dump(entry, file)
			file.write("\n")
	
	print("florence data saved to ", florence_output_path)

def clean_json(florence_output_path, cleaned_output_path):
    json_data = []
    
    # Load the existing JSON content, skipping invalid or empty lines
    with open(florence_output_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    json_data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON line: {line}")
                    
    # Write the updated JSON data back to the file
    with open(cleaned_output_path, 'w') as f:
        for entry in json_data:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Images have been appended to {cleaned_output_path}.")

def add_img_w_empty_annotations_florence(florence_output_path, image_dir, augmented_output_path):
    json_data = []
    
    # Load the existing JSON content, skipping invalid or empty lines
    with open(florence_output_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    json_data.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON line: {line}")
    
    existing_images = {entry['image'] for entry in json_data}
    
    # Iterate through the images in the directory and add only new ones
    for image_name in os.listdir(image_dir):
        if image_name.endswith(".png") and image_name not in existing_images:
            new_entry = {"image": image_name, "prefix": "<OD>", "suffix": ""}
            json_data.append(new_entry)
    
    # Write the updated JSON data back to the file
    with open(augmented_output_path, 'w') as f:
        for entry in json_data:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Images have been appended to {augmented_output_path}.")

def train_test_split_florence(florence_output_path, train_jsonl_path, test_jsonl_path):
    # Load the JSONL file into a list of dictionaries
    with open(florence_output_path, 'r') as f:
        data = [json.loads(line) for line in f.readlines()]
    
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(data)

    # Create a 'label' column based on whether 'suffix' is empty or not
    df['label'] = df['suffix'].apply(lambda x: 1 if x else 0)

    # Perform the train-test split with stratification
    train_df, test_df = train_test_split(df, test_size=0.15, stratify=df['label'], random_state=20)

    # Drop the 'label' column from the DataFrames
    train_df = train_df.drop(columns=['label'])
    test_df = test_df.drop(columns=['label'])

    # Write the train DataFrame to a JSONL file
    with open(train_jsonl_path, 'w') as f:
        for record in train_df.to_dict(orient='records'):
            json.dump(record, f)
            f.write('\n')

    # Write the test DataFrame to a JSONL file
    with open(test_jsonl_path, 'w') as f:
        for record in test_df.to_dict(orient='records'):
            json.dump(record, f)
            f.write('\n')

    print(f"Train data saved to {train_jsonl_path}")
    print(f"Test data saved to {test_jsonl_path}")

'''
# Generating the dataset for Florence2 model finetuning 
coco_json_path = "<path_to_downloaded_coco_dataset_json>" 
output_dir = "<output_directory>"
florence_output_path = "<path_to_save_converted_florence_dataset_json>"
empty_annotation_dir = "<directory_to_images_with_empty_annotations>"
train_jsonl_path = "<path_to_save_train_jsonl_file>"
test_jsonl_path = "<path_to_save_test_jsonl_file"

convert_to_florence_format(coco_json_path,output_dir)
add_img_w_empty_annotations_florence(florence_output_path, empty_annotation_dir)
train_test_split_florence(florence_output_path, train_jsonl_path, test_jsonl_path)
'''