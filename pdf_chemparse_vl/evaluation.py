"""
Contains the code from evaluation.ipynb but in a python file instead
"""
import torch
import re
import json
from PyPDF2 import PdfReader, PdfWriter
from openchemie import OpenChemIE
from os import listdir, mkdir, path
from os.path import isfile, join


CATEGORIES = {"electrosynthesis", "organic_synthesis", "photocatalysis"}
# CATEGORIES = {"organic_synthesis"}
# CATEGORIES = {"photocatalysis"}
# SEEN = set()
SYNTHESIS_COMPLETED = {'c6ob00076b', '10.1021acs.orglett.2c00362', '10.1002adsc.202100082', 'c6ob00108d', 'd1sc01130h', 'd1ra02225c', '10.1021acs.joc.4c00501', 'PIIS2666386423005271', 'c5sc00238a', '1-s2.0-S2666554924000966-main', '10.1021acs.orglett.6b01132', '1-s2.0-S2666386423003818-main', 'd4ra04674a', 'd3sc00803g', 'd4ra03939d', 'd3gc02735j', '1-s2.0-S2773223124000165-main', 'd4sc00403e', '1-s2.0-S2666554921000818-main', 'd0sc00031k', 'd4sc02969k', '1-s2.0-S2451929419305583-main', '10.1002ejoc.202400146', 'd4su00258j', 'c6sc03236b', 'c8sc04482a'}
SYNTHESIS_ERRORS = {'1-s2.0-S2589004219302299-main.pdf', 'd4sc04222k.pdf', 'adsc202100082-sup-0001-misc_information.pdf', '1-s2.0-S2589004222021691-main.pdf'}

ELECTROSYNTHESIS_COMPLETED = {'10.1002anie.202212131', '10.1002asia.202200780', 'd3ob00831b', '10.1002chem.202201654', 'c8ob03162b', 'd2cc03883h', '10.1002anie.202201595', 'd2gc00457g', 'c8cc09899a', '10.1002ajoc.202200719', '10.1002adsc.202301343', 'c8cc06451b', 'd2ob01402e', 'd1ob00079a', '10.1002anie.201909951', '10.1002anie.201610715', '10.1002anie.201700012', '10.1002chem.201802832', '10.1002adsc.202300118', '10.1002ejoc.201901928', '10.1002celc.202101155', 'd2gc04399h', 'c9cc03789f', '10.1002celc.201900080', 'c9cc00975b', 'd3qo00204g', '10.1002ejoc.202300553', '10.1002celc.201900138', '10.1002cctc.202300258', '10.1002adsc.202200003', '10.1002anie.202207660', '10.1002adsc.202200932', '10.1002ajoc.202100620', 'd2gc02086f', '10.1002ajoc.202300294', 'd1qo00038a', '10.1002ejoc.202300927', '10.1002anie.202013478', 'd3gc02701e'}
ELECTROSYNTEHSIS_ERRORS = {'d3gc03389a.pdf'}

PHOTOCATALYSIS_COMPLETED = {'cs2c04316', 'anie201705333', 'adsc_201400638', 'cs3c02092', 'cs3c05785_si_001', 'anie202000907-sup-0001-misc_information', 'anie201805732', 'cs2c00468', 'cs3c01713', 'cs4c00565_si_001', 'anie_201406393', 'cs2c01442', 'cs4c02320', 'jo3c00023', 'cs3c05150', 'anie201805732-sup-0001-misc_information', 'cs9b00287', 'anie202217638', 'anie201802656', 'anie202110257', 'anie_201308820_sm_miscellaneous_information', 'anie_201405359_sm_miscellaneous_information', 'cs2c04736', 'anie202000907', 'cs0c02250', 'anie_201405359', 'cs2c01442_si_001', 'ejoc201900839', 'cs4c00565', 'cs4c02797', 'cs3c05785', 'adsc_201400638_sm_miscellaneous_information', 'anie_201308820', 'anie202311984', 'cs7b00799', 'cs2c03805'}
PHOTOCATALYSIS_ERRORS = {'anie202110257-sup-0001-misc_information.pdf', 'ejoc201900839-sup-0001-supmat.pdf', 'anie_201406393_sm_miscellaneous_information.pdf', 'cs2c04736_si_001.pdf', 'cs8b02844_si_001.pdf', 'chem202104329-sup-0001-misc_information.pdf', 'jo3c00023_si_001.pdf', 'cs9b00287_si_001.pdf', 'chem202104329.pdf', 'cs4c02320_si_001.pdf', 'cs3c01713_si_001.pdf', 'anie201705333-sup-0001-misc_information.pdf', 'cs8b02844.pdf', 'anie201802656-sup-0001-misc_information.pdf', 'cs3c05150_si_001.pdf', 'cs0c02250_si_001.pdf', 'cs2c04316_si_001.pdf', 'cs2c00468_si_001.pdf', 'cs3c02092_si_001.pdf', 'anie202311984-sup-0001-misc_information.pdf', 'cs4c02797_si_001.pdf', 'cs2c03805_si_001.pdf', 'anie202217638-sup-0001-misc_information.pdf', 'cs7b00799_si_001.pdf'}

def divide_pdf(pdf_path: str, output_path: str) -> set:
    """divides a pdf from pdf_path into chunks of new pdfs each 10 pages long

    Args:
        pdf_path (str): path to pdf to divide up
        pdf_path (str): path of where to send outputted choped up pdf

    Returns:
        set: paths of all of the newly created pdfs
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    new_paths = set()
    
    if total_pages < 20:
        new_paths.add(pdf_path)
        return new_paths
    
    if not path.exists(output_path):
        mkdir(output_path)
    # Determine how many chunks are needed
    for start_page in range(0, total_pages, 20):
        # Create a new PDF writer for each chunk
        writer = PdfWriter()
        # Define the range for the current chunk
        end_page = min(start_page + 20, total_pages)
        for page_number in range(start_page, end_page):
            writer.add_page(reader.pages[page_number])
        # Save the chunk as a new PDF
        save_output_path = f"{output_path}/pages_{start_page + 1}_to_{end_page}.pdf"
        with open(save_output_path, "wb") as output_file:
            writer.write(output_file)
        new_paths.add(save_output_path)
    return new_paths
        

def get_text(title: str, text: dict) -> None:
    """ Gets the text of a title and saves in text

    Args:
        title (str): title text of a pdf
        text (dict): dict of all figure/table/etc. title to text pairs

    Returns:
        None
    """
    
    full_title_pattern = r"\b(Table|Scheme|Figure)\s*(\d+)"
    full_title_match = re.finditer(full_title_pattern, title)
    for match in full_title_match:
        full_match = match.group() 
        title_text = match.group(1)
        number_text = match.group(2)
    text[title_text + " " + number_text] = title.replace(full_match, "")


def save_figure_and_table_images(pdf_path: str, pdf_name: str, category: str, model: OpenChemIE, figure_index: int, table_index: int) -> tuple[int, int]:
    """Saves the images of figures and tables to proper folder in results

    Args:
        pdf_path (str): path to the pdf
        pdf_name (str): name of the pdf (just can be deduced from the path)
        category (str): one of {"organic_electrosynthesis", "organic_synthesis", "photocatalysis"}
    """
    text = {}
    
    print("starting " + pdf_name)
    figures = model.extract_figures_from_pdf(pdf_path, output_bbox=True, output_image=True)
    print("Retrieved figures")
    tables = model.extract_tables_from_pdf(pdf_path, output_bbox=True, output_image=True)
    print("Retrieved tables")
    
    if not path.exists("results/" + category + "/" + pdf_name):
        mkdir("results/" + category + "/" + pdf_name)
    for i in range(0, len(figures)):
        title = figures[i]["title"]["text"]
        if len(title) != 0:
            get_text(title, text)
        figures[i]["figure"]["image"].save("results/" + category + "/" + pdf_name + "/figure" + str(figure_index + i + 1) + ".png")
    print("Saved figures")
    
    for i in range(0, len(tables)):
        title = tables[i]["title"]["text"]
        if len(title) != 0:
            get_text(title, text)
        tables[i]["figure"]["image"].save("results/" + category + "/" + pdf_name + "/table" + str(table_index + i + 1) + ".png")
    print("Saved tables")
    
    return len(figures), len(tables), text


def evaluate_categories() -> None:
    """Runs OpenChemIE on all of the papers in the three categories and saves the images appropriatly
    """
    model = OpenChemIE(device=torch.device('cuda')) # change to cuda for gpu, cpu for cpu
    for category in CATEGORIES:
        pdf_files = [f for f in listdir(category) if isfile(join(category, f))]
        num_files_done = 0
        for file in pdf_files:
            pdf_name = file.replace(".pdf", "")
            if ".pdf" in file and pdf_name not in PHOTOCATALYSIS_COMPLETED:
                pdf_paths = divide_pdf(category + "/" + file, "divided_pdf/" + category + "/" + pdf_name)
                try:
                    figure_index, table_index = 0, 0
                    text = {}
                    for path in pdf_paths:
                        figure_index, table_index, new_text = save_figure_and_table_images(path, pdf_name, category, model, figure_index, table_index)
                        text.update(new_text)
                    with open("results/" + category + "/" + pdf_name + "/retrieved_text" + ".json", "w") as json_file:
                        json.dump(text, json_file, indent=4)
                    PHOTOCATALYSIS_COMPLETED.add(pdf_name)
                except:
                    print("ERROR with pdf " + category + "/" + file)
                    PHOTOCATALYSIS_ERRORS.add(category + "/" + file)
                print("completed " + pdf_name)
                print("completed " + str(num_files_done + 1) + "/" + str(len(pdf_files)))
                print(PHOTOCATALYSIS_COMPLETED)
                print("ERRORS")
                print(PHOTOCATALYSIS_ERRORS)
                num_files_done += 1
            # sleep(60)
        print("############")
        print("COMPLETED CATEGORY " + category)
        print("############")


if __name__ == "__main__":
    evaluate_categories()