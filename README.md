## MERMaid (Multimodal aid for Reaction Mining)

<img src="./Assets/MERMaid-overview.jpg" alt="Overview" width="600">

## Note: 
* MERMaid is an end-to-end knowledge ingestion pipeline to automatically convert disparate information conveyed through figures, schemes, and tables across various PDFs into a coherent and machine-actionable knowledge graph. It integrates three seqeuntial modules: 
    * VisualHeist for table and figure segmentation from PDFs 
    * DataRaider for multimodal analysis to extract relevant information as structured reaction schema
    * KGWizard for automated knowledge graph construction
* You can run MERMaid directly or use each module as a standalone tool for its specific functionality.
* MERMaid is integrated with the OpenAI provider at present. We will extend MERMaid to support other providers and open-source VLMs in future updates. 

## 1. Installation 


### 1.1 Create a new python environment using conda. The recommended python version is 3.9.

```
conda create -n mermaid-env python=3.9
conda activate mermaid-env
```

### 1.2 Install RxnScribe using the following steps for optical chemical structure recognition:
```
git clone https://github.com/thomas0809/RxnScribe.git
cd RxnScribe
pip install -r requirements.txt
python setup.py install
cd ..
```
### 1.3 Install MERMaid using the following steps: 

#### Option 1 (quick installation) 
Directly install the package. 

For full MERMaid pipeline: 
```
pip install git+https://github.com/aspuru-guzik-group/MERMaid/git
```
OR 
```
pip install MERMaid[full]
```

For individual modules only: 
```
pip install MERMaid[visualheist]
pip install MERMaid[dataraider]
pip install MERMaid[kgwizard]
```
#### Option 2 (for development purposes)
Download the entire repository and install the requirements.
```
git clone https://github.com/aspuru-guzik-group/MERMaid/git
cd MERMaid
pip install -e .
```
Please note that you may get a compatibility warning stating that `MolScribe version 1.1.1 not being compatible with Torch versions >2.0`. You can safely ignore this warning.

## 2. Usage 
### 2.1 Setting up your plug-and-play configuration file 
* Indicate your configuration settings in `startup.json`: 
    * "pdf_dir": "/path/to/directory/storing/pdfs"
    * "image_dir": "/path/to/directory/to/store/extracted/images"
    * "json_dir": "/path/to/directory/to/store/json/output"
    * "graph_dir": "/path/to/directory/to/store/graph/files"
    * "api_key": "your_api_key_here"
    * "model_size": "model_size_here" ("base" OR "large")
    * "keys": ["key1", "key2"] (the in-built reaction parameter keys can be found in `Prompts/inbuilt_keyvaluepairs.txt`) 
    * "new_keys": define your custom keys here 

* For post-processing extracted JSON reaction dictionaries: 
    * you can add your own common chemical names by modifying the `COMMON_NAMES` constant in `dataraider/postprocess.py`
    * you can also add your own key names that you want to be cleaned by modifying the `KEYS` constant in `dataraider/postprocess.py`

* We have included an additional `filter_prompt` in `Prompts/` folder to identify only images that are relevant to your task of interest. You are highly encouraged to specify your own task and keys. 

### 2.2 Running the end-to-end MERMaid pipeline 
The main command to launch and run MERMaid is: 
```
mermaid
```
All intermediate files from each module will be saved in the `Results` folder of your root directory by default.

### 2.3 Running individual modules 
#### 2.3.1 VisualHeist for image segmentation from scientific PDF documents 
The main command to launch and run VisualHeist is: 
```
visualheist
```

#### 2.3.2 DataRaider for image-to-data conversion into JSON dictionaries 
The main command to launch and run DataRaider is: 
```
dataraider
```
A sample output json dictionary can be found in `Assets` folder. 

#### 2.3.3 KGWizard for data-to-knowledge graph translation 
The main command to launch and run KGWizard is: 
```
kgwizard
```

## 3. Data Visualization 
<Coming Soon!>
