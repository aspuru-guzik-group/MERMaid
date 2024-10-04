## Overview

<img src="https://github.com/user-attachments/assets/d080fe59-ca1b-4078-a7e0-f2bdf3bdb3a5" alt="Overview" width="300">

## To-do list
https://docs.google.com/document/d/1iAGIeJCTBxmFWBWQFyuIKfXRWN62dHpRuKNJdAsAN4A/edit 

## Folder description

PDF-TF-chem : detect and saves figures and tables from pdfs (Missing caption retrieval module)

TF_to_json: processes the figures and table images

Prompts: currently contains two-step prompt for data extraction: step1 prompt to get rxn conditions, step 2 prompt to update rxn conditions with footnote dictionary


## For Brandon
#### To-do and progress log
https://docs.google.com/document/d/1yM1FouFpXCQ3gdKxlpcvkXmApNxV_wq-ibLNyMGouww/edit?usp=sharing

<b> Prepare training set for Florence-2 model finetuning using <code>prepare-florence-training-set.py</code>: </b>
1) Convert COCO dataset to Florence dataset
2) Augment Florence dataset with non-annotated images
3) Stratified split into train and test.jsonl files 
