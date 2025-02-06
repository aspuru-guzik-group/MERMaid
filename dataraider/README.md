# DataRaider

DataRaider is a module of MERMES2.0 that extracts reaction information from tables and figures

## Instalation

Create a conda envrionment if not created already
```
conda create -n mermaid python=3.10
conda activate mermaid
```

Install required packages

```
cd mermaid/dataraider
pip install -r requirements.txt
sudo apt install libjpeg-dev zlib1g-dev # for RxnScribe
```

Note that installation of RxnScribe is also needed, follow installation instructions at https://github.com/thomas0809/RxnScribe


# Usage

Once installed, import and use:

```
from mermaid.dataraider import tables_figures_to_json
keys = [INSERT KEYS HERE]
new_keys = {NEW_KEY1 : NEW_TEXT1, NEW_KEY2 : NEW_TEXT2, ...}
input_dir = INSERT HERE
output_dir = INSERT HERE
api_key = INSERT HERE
tables_figures_to_json(keys=keys, new_keys=new_keys, input_dir=input_dir, output_dir=output_dir, api_key=api_key)
```

Output will be in a JSON file of the following form:

```
{
    "SMILES": {
        "reactants": [
            "CCOC(OCC)C1=NN(c2ccccc2)C(c2ccccc2)C1"
        ],
        "products": [
            "CCOC(OCC)c1cc(-c2ccccc2)n(-c2ccccc2)n1"
        ]
    },
    "Optimization Runs": {
        "1": {
            "Entry": "1",
            "Anode": "C",
            "Cathode": "Pt",
            "Electrolytes": "n-Bu4NBF4 (0.20 M)",
            "Solvents": "CH3CN:H2O (1:1, 2.0 mL)",
            "Current": "2 mA",
            "Duration": "10 h",
            "Air/Inert": "N.R.",
            "Temperature": "rt",
            "Others": "Undivided cell",
            "Yield": "3a (45)",
            "Yield type": "isolated",
            "Footnote": ""
        },
        "2": {
            "Entry": "2",
            "Anode": "C",
            "Cathode": "Pt",
            "Electrolytes": "n-Bu4NBF4 (0.20 M)",
            "Solvents": "DMF (2.0 mL)",
            "Current": "2 mA",
            "Duration": "10 h",
            "Air/Inert": "N.R.",
            "Temperature": "rt",
            "Others": "Undivided cell",
            "Yield": "3a (40)",
            "Yield type": "isolated",
            "Footnote": ""
        },
        ...
    }
}
```
