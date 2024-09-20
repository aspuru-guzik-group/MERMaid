'''
Function to download Wiley articles in PDF
'''
import os
import requests
import time
import csv

def download_pdfs_from_dois(csv_file, download_directory, headers):
    """
    Reads DOIs from a CSV file, constructs URLs, and downloads PDFs, saving them with DOIs as filenames.
    
    Args:
        csv_file (str): Path to the CSV file containing DOIs in the first column.
        download_directory (str): Path to the directory where PDFs will be saved.
        headers (dict): Headers to be included in the HTTP request.
    """
    base_url = "https://api.wiley.com/onlinelibrary/tdm/v1/articles/"

    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row:
                doi = row[0]
                url = f"{base_url}{doi}"
                print(f"Downloading: {url}")

                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    file_path = os.path.join(download_directory, f"{doi.replace('/', '_')}.pdf")
                    with open(file_path, 'wb') as pdf_file:
                        pdf_file.write(response.content)
                    print(f"File downloaded successfully to: {file_path}")
                else:
                    print(f"Error {response.status_code} for DOI: {doi}")

                time.sleep(15)  # 15-second delay between requests

if __name__ == "__main__":
    csv_file_path = "path/to/your/csvfile.csv"  # Update this with the path to your CSV file
    download_directory = "path/to/your/download/directory"  # Update this with your desired download directory
    headers = {
        'Wiley-TDM-Client-Token': 'ca1a2f65-a6c2-4caf-9225-4f3aabf33165',  # Replace with your actual Clickthrough Client token
    }

    download_pdfs_from_dois(csv_file_path, download_directory, headers)
