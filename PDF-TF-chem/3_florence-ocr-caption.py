from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
from pathlib import Path
import os
import json

#TODO: Clean output to not output as dictionary and not include <OCR>:

model_id = 'microsoft/Florence-2-large'
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True).eval().cuda()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

def run_florence_ocr(task_prompt, 
					 image, 
					 text_input=None):
	if text_input is None:
		prompt = task_prompt
	else:
		prompt = task_prompt + text_input
	inputs = processor(text=prompt, 
					images=image, 
					return_tensors="pt")
	generated_ids = model.generate(
		input_ids=inputs["input_ids"].cuda(),
		pixel_values=inputs["pixel_values"].cuda(),
		max_new_tokens=1024,
		early_stopping=False,
		do_sample=False,
		num_beams=3
		)
	generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
	parsed_answer = processor.post_process_generation(
    	generated_text,
    	task=task_prompt,
    	image_size=(image.width, image.height)
	)
	return parsed_answer


def process_images_ocr(base_file_names: list, 
                       image_dir: Path, 
                       caption_dir: Path, 
                       task_prompt: str): 
    
    for base_file_name in base_file_names: 
        print(f"processing {base_file_name}")
        results = []
        
        for file in image_dir.iterdir():
            print(f'processing {file}')
            if file.name.startswith(base_file_name):
                image_path = file
                image = Image.open(image_path)
                response = run_florence_ocr(task_prompt, image)
                results.append(response)
        
        json_file_name = caption_dir / f"{base_file_name}.json"
        with open(json_file_name, 'w') as json_file: 
            json.dump(results, json_file, indent=4)
        print(f"Done processing {base_file_name}")
        print()
   

# Example
base_file_names = [
    'adsc_201400638', 
    'anie_201308820', 
    'anie_201405359', 
    'anie_201406393', 
    '10.1021_acs.joc.8b00486',
    '10.1021_acs.orglett.4c02846', 
    '10.1039_d1sc04180k', 
    '1-s2.0-S2451929419305583-main',
    '1-s2.0-S2589004219302299-main',
    '1-s2.0-S2589004222021691-main',
    '1-s2.0-S2666386423003818-main',
    '1-s2.0-S2666554921000818-main',
    '1-s2.0-S2666554924000966-main',
    '1-s2.0-S2773223124000165-main',
    '10.1002adsc.202100082',
    '10.1002adsc.202200003',
    '10.1002adsc.202200932',
    '10.1002adsc.202300118',
    '10.1002adsc.202301343',
    '10.1002ajoc.202100620',
    '10.1002ajoc.202200719',
    '10.1002ajoc.202300294',
    '10.1002anie.201610715',
    '10.1002anie.201700012',
    '10.1002anie.201909951',
    '10.1002anie.202013478',
    '10.1002anie.202201595',
    '10.1002anie.202207660',
    '10.1002anie.202212131',
    '10.1002asia.202200780',
    '10.1002cctc.202300258',
    '10.1002celc.201900080',
    '10.1002celc.201900138',
    '10.1002celc.202101155',
    '10.1002chem.201802832',
    '10.1002chem.202201654',
    '10.1002ejoc.201901928',
    '10.1002ejoc.202300553',
    '10.1002ejoc.202300927',
    '10.1002ejoc.202400146',
    '10.1021acs.joc.4c00501',
    '10.1021acs.orglett.2c00362',
    '10.1021acs.orglett.6b01132',
    'PIIS2666386423005271',
    'adsc202100082-sup-0001-misc',
    'anie201705333',
    'anie201802656',
    'anie201805732',
    'anie202000907',
    'anie202110257',
    'anie202217638',
    'anie202311984',
    'c5sc00238a',
    'c6ob00076b',
    'c6ob00108d',
    'c6sc03236b',
    'c8cc06451b',
    'c8cc09899a',
    'c8ob03162b',
    'c8sc04482a',
    'c9cc00975b',
    'c9cc03789f',
    'chem202104329',
    'cs0c02250',
    'cs2c00468',
    'cs2c01442',
    'cs2c03805',
    'cs2c04316',
    'cs2c04736',
    'cs3c01713',
    'cs3c02092',
    'cs3c05150',
    'cs3c05785',
    'cs4c00565',
    'cs4c02320',
    'cs4c02797',
    'cs7b00799',
    'cs8b02844',
    'cs9b00287',
    'd0sc00031k',
    'd1ob00079a',
    'd1qo00038a',
    'd1ra02225c',
    'd1sc01130h',
    'd2cc03883h',
    'd2gc00457g',
    'd2gc02086f',
    'd2gc04399h',
    'd2ob01402e',
    'd3gc02701e',
    'd3gc02735j',
    'd3gc03389a',
    'd3ob00831b',
    'd3qo00204g',
    'd3sc00803g',
    'd4ra03939d',
    'd4ra04674a',
    'd4sc00403e',
    'd4sc02969k',
    'd4sc04222k',
    'd4su00258j',
    'ejoc201900839',
    'jo3c00023' 
]
image_dir = Path("./output/2_for-ocr-captions/")
caption_dir = Path("./output/2_for-ocr-captions/")
task_prompt = '<OCR>'

process_images_ocr(base_file_names, image_dir, caption_dir, task_prompt)