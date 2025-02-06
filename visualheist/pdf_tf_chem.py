from batch_proc_pdf_to_table_figures_retrainedmodel import pdf_to_table_figures
import os

MODEL_ID = "yifeihu/TF-ID-large"
SAFETENSORS_PATH = "./model_checkpoints/epoch_12/model.safetensors" #currently stored locally on cluster, will upload to huggingface or something?

def pdf_to_figures_and_tables(input_dir: str, output_dir: str="./", batch: bool=False):
    if batch:
        for file in os.listdir(input_dir): 
            if not file.endswith("pdf"):
                print("ERROR: " + file + "is not a pdf")
                continue
            pdf_path = os.path.join(input_dir,file)
            retrieve_for_single_pdf(pdf_path, output_dir)
        return
    # otherwise input_dir is a single pdf
    file = input_dir
    if not file.endswith("pdf"):
        print("ERROR: " + file + "is not a pdf")
        return
    retrieve_for_single_pdf(file, output_dir)


def retrieve_for_single_pdf(pdf_path, output_dir: str):
    pdf_to_table_figures(pdf_path, MODEL_ID, SAFETENSORS_PATH, output_dir)