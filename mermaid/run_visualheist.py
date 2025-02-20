import json
from methods_visualheist import batch_pdf_to_figures_and_tables
import os

def load_config(config_file):
    """Load configurations from config_file

    :param config_file: Path to config file
    :type config_file: str
    :return: Returns a dictionary of fields from config_file
    :rtype: dict
    """
    with open(config_file, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    # Load the configuration from the file
    package_dir = os.path.dirname(__file__)
    config = load_config(package_dir + '/../mermaid/startup.json')

    # Use the default configuration in the function call if unspecified 
    input_dir = config.get('pdf_dir', "./pdfs")
    output_dir = config.get('image_dir', config.get('default_image_dir'))
    model_size = "large" == config.get('model_size')
    # Use the loaded configuration in the function call
    batch_pdf_to_figures_and_tables(input_dir, output_dir, large_model=model_size)