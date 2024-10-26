import prepare_florence_training_dataset as prep_files
import json
import os

coco_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/caption-annotate3.json"
flor_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/florence_format_capt_train.json"
cleaned_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/florence_format_capt_train_clean.json"
image_dir = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/caption_retrieval_model_train/"
augmented_output_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/florence_format_capt_train_aug_clean.json"
train_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/caption_retrieval_train.jsonl"
test_path = "/mnt/c/Users/Shi Xuan/OneDrive - University of Toronto/Project_MERLIN/Project_Digital esyn corpus/caption_retrieval/caption_retrieval_test.jsonl"

#prep_files.convert_to_florence_format(coco_path,flor_path)
#prep_files.clean_json(flor_path, cleaned_path)
#prep_files.add_img_w_empty_annotations_florence(cleaned_path,image_dir, augmented_output_path)
prep_files.train_test_split_florence(augmented_output_path,train_path, test_path)
