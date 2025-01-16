# PDF-TF-chem

PDF-TF-chem is the module in MERMES2.0 that extracts figures and tables from literature.

## Instalation

Create a conda envrionment if not created already
```
conda create -n mermes python=3.10
conda activate mermes
```

Install required packages

```
sudo apt install poppler-utils
pip install pdf2image
pip install transformers
pip install torch
pip install einops timm
```

Import the necessary function
```
from PDF-TF-chem import pdf_to_figures_and_tables

```

To retrieve figures and tables from a single pdf do:
```
file = YOUR FILE HERE
pdf_to_figures_and_tables(input_dir=file)
```

To retrieve figures and tables from a directory do:
```
input_dir = YOUR DIRECTORY HERE
pdf_to_figures_and_tables(input_dir=input_dir, batch=True)
```