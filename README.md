## MERMaid (Multimodal aid for Reaction Mining)

<img src="./Assets/MERMaid-overview.jpg" alt="Overview" width="600">

### Table of Contents  
1. [Overview](#overview)  
2. [Installation](#1-installation)  
3. [Usage](#2-usage)  

## Overview  
MERMaid is an end-to-end knowledge ingestion pipeline to automatically convert disparate information conveyed through figures, schemes, and tables across various PDFs into a coherent and machine-actionable knowledge graph. It integrates three sequential modules:  
- **VisualHeist** for table and figure segmentation from PDFs  
- **DataRaider** for multimodal analysis to extract relevant information as structured reaction schema  
- **KGWizard** for automated knowledge graph construction  

You can run MERMaid directly or use VisualHeist and DataRaider as standalone tools for their specific functionality.  

MERMaid is integrated with the OpenAI provider at present. We will extend MERMaid to support other providers and open-source VLMs in future updates.  

VisualHeist works best on systems with **high RAM**. For optimal performance, ensure that your system has sufficient memory, as running out of memory may cause the process to be terminated prematurely.  

Further usage details on KGWizard can be found in the [KGWizard README file](https://github.com/aspuru-guzik-group/MERMaid/blob/main/src/kgwizard/README.org).  

---

## 1. Installation  

### 1.1 Create a new virtual environment  
The recommended Python version is **3.9**.  

#### Using Conda:
```sh
conda create -n mermaid-env python=3.9
conda activate mermaid-env
```
#### Using venv:
```sh
python3.9 -m venv mermaid-env
source mermaid-env/bin/activate
```

### 1.2 Install RxnScribe for Optical Chemical Structure Recognition  
```sh
git clone https://github.com/thomas0809/RxnScribe.git
cd RxnScribe
pip install -r requirements.txt
python setup.py install
cd ..
```
> ⚠️ You may see a compatibility warning about `MolScribe version 1.1.1 not being compatible with Torch versions >2.0`. This can be safely ignored.  

### 1.3 Install MERMaid  
Download the repository and install dependencies:  
```sh
git clone https://github.com/aspuru-guzik-group/MERMaid/
cd MERMaid
pip install -e .
```
For the **full MERMaid pipeline**:  
```sh
pip install MERMaid[full]
```
For **individual modules**:  
```sh
pip install MERMaid[visualheist]
pip install MERMaid[dataraider]
pip install MERMaid[kgwizard]
```

---

## 2. Usage  

### 2.1 Setting Up Your Configuration File  
Define settings in `startup.json`:  
```json
{
  "pdf_dir": "/path/to/directory/storing/pdfs",
  "image_dir": "/path/to/directory/to/store/extracted/images",
  "json_dir": "/path/to/directory/to/store/json/output",
  "graph_dir": "/path/to/directory/to/store/graph/files",
  "model_size": "base",
  "keys": ["key1", "key2"],
  "new_keys": [],
  "graph_name": "your_graph_name",
  "schema": "your_schema_name"
}
```
- The in-built reaction parameter keys are in `Prompts/inbuilt_keyvaluepairs.txt`.  
- For post-processing extracted JSON reaction dictionaries:  
  - Modify `COMMON_NAMES` in `dataraider/postprocess.py` to add custom chemical names.  
  - Modify `KEYS` in `dataraider/postprocess.py` to clean specific key names.  
- Customize `filter_prompt` in `Prompts/` to filter relevant images.  

### 2.2 Setting Up API Key  
The environment variable **`OPENAI_API_KEY`** is required for **DataRaider** and **KGWizard**.  

```sh
export OPENAI_API_KEY="your-openai-api-key"
```

---

### 2.3 Running the Full MERMaid Pipeline  
Run the full pipeline with:  
```sh
mermaid
```
Intermediate files will be saved in the `Results/` directory.  

### 2.4 Running Individual Modules  

#### 2.4.1 VisualHeist – Image Segmentation from PDFs  
```sh
visualheist
```

#### 2.4.2 DataRaider – Image-to-Data Conversion  
```sh
dataraider
```
*A sample output JSON is available in the `Assets` folder.*  

#### 2.4.3 KGWizard – Data-to-Knowledge Graph Translation  
```sh
kgwizard
