# TF-to-JSON

TF-to-JSON is a module of MERMES2.0 that extracts reaction information from reaction diagrams

## Instalation

Create a conda envrionment if not created already
```
conda create -n mermes python=3.10
conda activate mermes
```

Install required packages

```
cd MERMES2.0/TF_to_json
pip install -r requirements.txt
sudo apt install libjpeg-dev zlib1g-dev # for RxnScribe
```

Note that installation of RxnScribe is also needed, follow installation instructions at https://github.com/thomas0809/RxnScribe


# Usage

Once installed, import and use:

```
From TF_to_json import tf_to_json
keys = INSERT KEYS HERE
input_dir = INSERT HERE
outpur_dir = INSERT HERE
tf_to_json(keys=keys, input_dir=input_dir, output_dir=output_dir)
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
