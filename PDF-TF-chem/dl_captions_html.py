from bs4 import BeautifulSoup
import re
import json
import os

#To check: extract figures + schemes + tables + charts 
# To check: extract ALL footnotes (for tables and schemes)
# Gracefully skip if no captions? 

def save_captions(caption_file_dir, base_name, all_captions): 
    caption_file_path = os.path.join(caption_file_dir, f"{base_name}_captions.json")

    with open(caption_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(all_captions, json_file, ensure_ascii=False, indent=4)
        print(f"captions saved to {caption_file_path}")

# with footnotes 
def download_captions_headers_footnotes_wiley(input_file_path):
    with open(input_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")
    
    remove_phrase = "Open in figure viewerPowerPoint"
    remove_phrase2 = "Caption"

    combined_captions = []
    
    # Find all elements that could be table captions or footnotes, in the order they appear
    elements = soup.find_all(["header", "div"], class_=["article-table-caption", 
                                                        "article-section__table-footnotes"])
    
    current_caption = None

    for element in elements:
        if "article-table-caption" in element.get("class", []):
            # If it's a table caption, process it
            if current_caption:
                # If there's a previous caption without a footnote, add it to the list
                combined_captions.append(current_caption)
            
            # Prepare a new caption
            caption_text = element.get_text(strip=True).replace(remove_phrase, "")
            current_caption = caption_text
        
        elif "article-section__table-footnotes" in element.get("class", []):
            # If it's a table footnote, add it to the current caption
            if current_caption:
                footnote_text = element.get_text(strip=True).replace
                current_caption += f" {footnote_text}"
    
    # Add the last caption if it exists
    if current_caption:
        combined_captions.append(current_caption)
    
    # Extract figure captions (handled separately)
    figure_captions = soup.find_all("figcaption", class_="figure__caption")
    figure_captions_cleaned = [
        caption.get_text(strip=True).replace(remove_phrase2, " ").replace(remove_phrase,"")
        for caption in figure_captions
    ]

    # Combine table and figure captions
    all_captions = combined_captions + figure_captions_cleaned

    return all_captions


def download_captions_headers_footnotes_rsc(input_file_path):
    with open(input_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Extract figure captions
    figure_captions = soup.find_all("td", class_="image_title")
    figure_captions = [
        f"{caption.find('b').get_text(strip=True)} {caption.find('span', class_='graphic_title').get_text(strip=True)}"
        for caption in figure_captions
    ]

    # Extract table captions and corresponding footnotes
    table_captions = []
    table_captions_elements = soup.find_all("div", class_="table_caption")
    
    for caption_element in table_captions_elements:
        # Get the basic table caption text
        table_caption_text = f"{caption_element.find('b').get_text(strip=True)} {caption_element.find('span').get_text(strip=True)}"
        
        # Locate the parent of the table or <tfoot> associated with this caption
        table_wrapper = caption_element.find_next("div", class_="rtable__wrapper")
        
        # Extract footnotes from the <tfoot> if available
        footnote_texts = []
        if table_wrapper:
            tfoot = table_wrapper.find("tfoot")
            if tfoot:
                footnotes = tfoot.find_all("a", id=True)
                for footnote in footnotes:
                    # Combine the footnote marker and its content
                    marker = footnote.find("span", class_="tfootnote").get_text(strip=True)
                    content = footnote.find_next("span", class_="sup_inf").get_text(strip=True)
                    footnote_texts.append(f"[{marker}] {content}")
        
        # Combine the table caption with the footnotes, if any
        if footnote_texts:
            full_caption = f"{table_caption_text} {' '.join(footnote_texts)}"
        else:
            full_caption = table_caption_text

        table_captions.append(full_caption)

    # Combine table and figure captions
    all_captions = figure_captions + table_captions

    return all_captions


def download_captions_headers_footnotes_acs(input_file_path):
    with open(input_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()# Initialize BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    figures_schemes = []
    tables = []

    for figure in soup.find_all('figure'):
        id = figure.get('id')
        try: 
            if id.startswith('fig'):
                fig_caption = figure.find('figcaption').get_text(strip=True)
                figures_schemes.append(f"{fig_caption}")
            elif id.startswith('sch'):
                scheme_caption = figure.find('figcaption').get_text(strip=True)
                footnote_ref = figure.find_all('p')
                if footnote_ref:
                    for footnote in footnote_ref:
                        scheme_caption += f" {footnote.get_text(strip=True)}"
                figures_schemes.append(f"{scheme_caption}")  
            else: 
                continue
        except:
            continue

    for table in soup.find_all('div', class_='NLM_table-wrap'):
        table_title = table.find('div', class_='title2').text.strip()
        footnotes = table.find_all('div', class_='footnote')
        for fn in footnotes:
            table_title += f" {fn.get_text(strip=True)}"
        tables.append(table_title)
    
    all_captions = sorted(list(figures_schemes+ tables))

    return all_captions


# should i also try footnotes for figures/schemes? 
def download_captions_headers_footnots_elsevier_cellpress(input_file_path):
    
    with open(input_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    #tables and footnotes
    all_captions = []
    table_captions = soup.find_all("div", class_="tables frame-topbot colsep-0 rowsep-0")
    print(table_captions)
    
    if table_captions:
        for caption in table_captions:
            p_element = caption.find("p")
            if p_element:
                caption_text = caption.find("p").get_text(strip=True).replace("\xa0", " ")
                #do i need to find all??
                try: 
                    footnotes = caption.find("dl", class_="footnotes")
                    if footnotes:
                        footnotes_c = footnotes.get_text(strip=True)
                        caption_text += f" {footnotes_c}" 
                except: 
                    continue 
                try: 
                    additional_fn = caption.find("div",class_="u-margin-s-bottom")
                    if additional_fn: 
                        for fn in additional_fn: 
                            fn_c = fn.get_text(strip=True)
                            caption_text +=f" {fn_c}"
                except: 
                    continue
                all_captions.append(caption_text)

    #figures and schemes and footnotes
    figure_captions = soup.find_all("figure", class_="figure text-xs")
    for caption in figure_captions:
        try: 
            caption_text = caption.find("p").get_text(strip=True).replace("\xa0", " ")
            footnotes = caption.find_all("div", class_="u-margin-s-bottom")
            if footnotes:
                for footnote in footnotes:
                    footnote_a = footnote.get_text(strip=True)
                    caption_text += f" {footnote_a}" 
            all_captions.append(caption_text)
        except: 
            continue

    final_captions = sorted(list(all_captions))
    return final_captions


# Run 
input_file_dir = "../downloaded_html/electrosynthesis/"
caption_file_dir = "../downloaded_captions/electrosynthesis/"
for file in os.listdir(input_file_dir):
    if file.endswith('.json'): 
        article_name = file.removesuffix('.json') + '_with_footnotes'
        input_file_path = os.path.join(input_file_dir, file)
        if "10.1021" in file:
            all_captions = download_captions_headers_footnotes_acs(input_file_path)
            save_captions(caption_file_dir, article_name, all_captions)
        
        if "10.1002" in file:
            all_captions = download_captions_headers_footnotes_wiley(input_file_path) 
            save_captions(caption_file_dir, article_name, all_captions)

        if "10.1039" in file:
            all_captions = download_captions_headers_footnotes_rsc(input_file_path)
            save_captions(caption_file_dir, article_name, all_captions)

        if "10.1016" in file: 
            all_captions = download_captions_headers_footnots_elsevier_cellpress(input_file_path)
            save_captions(caption_file_dir, article_name, all_captions)
