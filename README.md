## MERMaid (Multimodal aid for Reaction Mining)

<img src="/home/sleong/MERMES2.0/Examples/MERMaid-overview.jpg" alt="Overview" width="300">

Note: 
* MERMaid is integrated with the OpenAI provider at present. We will extend MERMaid to support other providers and open-source VLMs in future updates. 
* Please note that a GPU is required to run VisualHeist locally. 

## 1. Installation 

### Option 1 (quick installation) 
Directly install the package to your pip environment. 
```
For full MERMaid pipeline: 
pip install git+https://github.com/aspuru-guzik-group/MERMaid/git

For individual modules: 
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

### 2.2 Running the end-to-end MERMaid pipeline 
The main command to launch and run MERMaid is: 
```
python -m mermaid.main
```
All intermediate files from each module will be saved in your stipulated output directory. 

### 2.3 Running individual modules 
#### 2.3.1 VisualHeist for image segmentation from scientific PDF documents 
The main command to launch and run VisualHeist is: 
```
python -m mermaid.run_visualheist
```
The extracted image files will be saved to `extracted_images ` subfolder in your stipulated output directory by default. 

#### 2.3.2 DataRaider for image-to-data conversion into JSON dictionaries 
The main command to launch and run DataRaider is: 
```
python -m mermaid.run_dataraider
```
The extracted json dictionaries will be saved to `json_files` subfolder in your stipulated output directory by default. 
A sample output json dictionary can be found in `Examples` folder. 

#### 2.3.3 KGWizard for data-to-knowledge graph translation 
The main command to launch and run KGWizard is: 
```
XXXXXXXXXX
```

## 3. Data Visualization 
The knowledge graphs can be visualized using XXXXXXXXXXX. 