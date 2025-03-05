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

### Option 1 (quick installation) 
Directly install the package to your pip environment. 

For full MERMaid pipeline: 
```
pip install git+https://github.com/aspuru-guzik-group/MERMaid/git
```

For individual modules: 
```
pip install XXXXXXXXXXXXXXXX
```
### Option 2 (for development purposes)
Download the entire repository and install the requirements 
```
git clone https://github.com/aspuru-guzik-group/MERMaid/git
cd MERMaid
pip install -e .
```

## 2. Usage 
### 2.1 Setting up your plug-and-play configuration file 
* Fill in your customized details in `mermaid/startup.json` to configure it (e.g. directory paths, reaction parameter key selection etc.)  
* The in-built reaction parameter keys can be found in `Prompts/inbuilt_keyvaluepairs.txt`. 
* For post-processing extracted JSON reaction dictionaries: 
    * you can add your own common chemical names by modifying the `COMMON_NAMES` constant in `mermaid/postprocess.py`
    * you can also add your own key names that you want to be cleaned by modifying the `KEYS` constant in `mermaid/postprocess.py`


### 2.2 Running the end-to-end MERMaid pipeline 
The main command to launch and run MERMaid is: 
```
python mermaid/main.py
```
All intermediate files from each module will be saved in your pdf directory by default.

### 2.3 Running individual modules 
#### 2.3.1 VisualHeist for image segmentation from scientific PDF documents 
The main command to launch and run VisualHeist is: 
```
python mermaid/run_visualheist.py
```
The extracted image files will be saved to an `extracted_images` subfolder in your pdf directory by default. 

#### 2.3.2 DataRaider for image-to-data conversion into JSON dictionaries 
The main command to launch and run DataRaider is: 
```
python mermaid/run_dataraider.py
```
The extracted json dictionaries will be saved to `json_files` subfolder in your image directory by default. 
A sample output json dictionary can be found in `Examples` folder. 

#### 2.3.3 KGWizard for data-to-knowledge graph translation 
The main command to launch and run KGWizard is: 
```
XXXXXXXXXXXXX
```

## 3. Data Visualization 
The knowledge graphs can be visualized using XXXXXXXXXXX. 