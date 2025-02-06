# VisualHeist

VisualHeist is the module in MERMaid that extracts figures and tables from literature.

Note that you must have a GPU to run locally

## Instalation

Create a conda envrionment if not created already
```
conda create -n mermaid python=3.10
conda activate mermaid
```

Install required packages

```
cd mermaid/visualheist
sudo apt install poppler-utils
pip install -r requirements.txt
```

Import the necessary function
```
from visualheist import pdf_to_figures_and_tables

```

To retrieve figures and tables from a single pdf execute:
```
file = YOUR FILE HERE
pdf_to_figures_and_tables(input_dir=file)
```

To retrieve figures and tables from a directory execute:
```
input_dir = YOUR DIRECTORY HERE
pdf_to_figures_and_tables(input_dir=input_dir, batch=True)
```