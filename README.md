## MERMaid (Multimodal aid for Reaction Mining)

<img src="./Assets/MERMaid-overview.jpg" alt="Overview" width="600">

### Table of Contents  
1. [Overview](#1-overview)  
2. [Installation](#2-installation)  
3. [Usage](#3-usage) 
4. [Running the web app](#4-running-the-mermaid-web-app-recommended-for-new-users)
5. [Adapting MERMaid to other chemical domains/tasks](#5-adapting-mermaid)

## 1. Overview  
MERMaid is an end-to-end knowledge ingestion pipeline to automatically convert disparate information conveyed through figures, schemes, and tables across various PDFs into a coherent and machine-actionable knowledge graph. It integrates three sequential modules:  
- **VisualHeist** for table and figure segmentation from PDFs  
- **DataRaider** for multimodal analysis to extract relevant information as structured reaction schema  
- **KGWizard** for automated knowledge graph construction  

You can run MERMaid directly or use VisualHeist and DataRaider as standalone tools for their specific functionality.  

> ⚠️ MERMaid is integrated with the OpenAI provider at present. Please ensure that you have **sufficient credits in your account** otherwise you will encounter [errors](https://github.com/aspuru-guzik-group/MERMaid/issues/3) (Note: running VisualHeist by itself does not require an API key). We will extend MERMaid to support other providers and open-source VLMs in future updates.  

VisualHeist works best on systems with **high RAM**. For optimal performance, ensure that your system has sufficient memory, as running out of memory may cause the process to be terminated prematurely.  

---
If you use MERMaid and its submodules in your research, please cite our [preprint](https://doi.org/10.26434/chemrxiv-2025-8z6h2). Note that this content is a preprint and has not been peer-reviewed.
```
@article{
    MERMaid,
    title = {MERMaid: Universal multimodal mining of chemical reactions from PDFs using vision-language models},
    author = {Shi Xuan Leong, Sergio Pablo-García, Brandon Wong, Alán Aspuru-Guzik},
    DOI = {10.26434/chemrxiv-2025-8z6h2},
    journal = {ChemRxiv},
    year = {2025},
}  
```
---
## 2. Installation  

### 2.1 Create a new virtual environment  
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

### 2.2 Install RxnScribe for Optical Chemical Structure Recognition  
This module is required to extract the SMILES strings of reactants and products. 
```sh
git clone https://github.com/thomas0809/RxnScribe.git
cd RxnScribe
pip install -r requirements.txt
python setup.py install
cd ..
```
> ⚠️ You may see a compatibility warning about `MolScribe version 1.1.1 not being compatible with Torch versions >2.0`. This can be safely ignored.  

### 2.3 Install/Setup of JanusGraph server
In order to run KGWizard, a running local JanusGraph server is required.

Install Java 8 SE from [Oracle](https://www.oracle.com/ca-en/java/technologies/javase/javase8-archive-downloads.html).
Install [JanusGraph](https://github.com/JanusGraph/janusgraph/releases), tested with version 1.1.0.
Unzip the JanusGraph zip file in the same folder that has `RxnScribe`. 
```bash
unzip janusgraph-1.1.0.zip
```

### 2.4 Install MERMaid  
Download the repository and install dependencies in the same folder that has both `RxnSribe` and `janusgraph-1.1.0`:  
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

## 3. Usage  

### 3.1 Setting Up Your Configuration File  


Settings can be set through a configuration file found in `scripts/startup.json` or throught a created configuration file (see 3.3.3). VisualHeist and DataRaider can be run via the configuration file or via the command line (see 3.4) whereas full MERMaid pipeline requires settings to be provided through a configuration file (see 3.3.2).

**Define custom settings in `scripts/startup.json`:** 
- `pdf_dir`: Full path to directory where PDFs are stored (required for running VisualHeist).
- `image_dir`: Full path to directory to store extracted images or where images are currently stored (required for running DataRaider).
- `json_dir`: Full path to directory to store JSON output (required for running DataRaider and/or KGWizard).
- `graph_dir`: Full path to directory to store graph files (required for running KGWizard).
- `prompt_dir`: Full path to directory containing prompt files (required for running DataRaider).
- `model_size`: Choose between 'base' or 'large' (required for running VisualHeist).
- `keys`: List of reaction parameter keys (required for running DataRaider).
- `new_keys`: Additional keys for new reactions (required for running DataRaider).
- `graph_name`: Name for the generated knowledge graph (required for running KGWizard).
- `schema`: User-prepared schema for the knowledge graph (required for running KGWizard).

**Additional notes:** 
- The in-built reaction parameter keys are in `Prompts/inbuilt_keyvaluepairs.txt`.  
- For post-processing extracted JSON reaction dictionaries:  
  - Modify `COMMON_NAMES` in `dataraider/postprocess.py` to add custom chemical names.  
  - Modify `KEYS` in `dataraider/postprocess.py` to clean specific key names.  
- Customize `filter_prompt` in `Prompts/` to filter relevant images.  
- You can use one of our prepared schema found in `src/kgwizard/graphdb/schemas`

### 3.2 Setting Up API Key  
The environment variable **`OPENAI_API_KEY`** is required for **DataRaider** and **KGWizard**. You can set this variable in your terminal session using the following command:

```sh
export OPENAI_API_KEY="your-openai-api-key"
```
This method sets the API key for the current terminal session, and the environment variable will be available to any processes started from that session. 

Alternatively, you can create a `.env` file in the root directory of the MERMaid project (the same directory where `README.md` is located) and add the following line to it: 

```sh
OPENAI_API_KEY="your-openai-api-key"
```
This will automatically set the OPENAI_API_KEY environment variable whenever you run the project.

---

### 3.3 Running the Full MERMaid Pipeline  


#### 3.3.1 Start JanusGraph Server

A running JanusGraph server is required for running the full MERMaid pipline and KGWizard (see 3.4.3)

Start the JanusGraph Server (Choose either option):
> **Note**: Server requires 2–8 GB RAM.

#### Foreground:
Open a seperate terminal and navigate into to the `janusgraph-1.1.0` folder.

To start the server:
```bash
./bin/janusgraph-server.sh ./conf/gremlin-server/gremlin-server.yaml
```
To terminate the server use Ctrl+C

#### Background:
To start the server:
```bash
cd janusgraph-1.1.0
./bin/janusgraph-server.sh start
```

To terminate the server:
```bash
./bin/janusgraph-server.sh stop
```
> The port of the running JanusGraph server is automatically set to 8182 with address ws://localhost

The full MERMaid pipeline comes with two commands

#### 3.3.2 RUN Command

Run the mermaid pipeline (visualheist, dataraider, kgwizard sequentially)

```sh
mermaid RUN   --config ./scripts/startup.json
```
| Option        | Description |
| --------       | ------- |
| `--config`     | Path to the configuration file|

Intermediate files will be saved in the `Results/` directory.  

#### 3.3.3 CFG Command
Output a configuration file of the same form as `scripts/startup.json`

```sh
mermaid CFG   --out_location ./
```
| Option        | Description |
| --------       | ------- |
| `--out_location`     | Path to save new configuration file |

### 3.4 Running Individual Modules  

#### 3.4.1 VisualHeist – Image Segmentation from PDFs

VisualHeist can be run using the settings provided in `scripts/startup.json` using:

```sh
visualheist
```

Or can be run using command line arguments with the following:
```sh
visualheist    --config ./scripts/startup.json   --pdf_dir /path/to/pdf   --image_dir /path/to/save/images   --model_size base
```

| Option        | Description |
| --------       | ------- |
| `--config`     | Path to the configuration file. If specified, ignores other arguments |
| `--pdf_dir`    | Path to the input PDF directory     |
| `--image_dir`  | Path to the output image directory    |
| `--model_size` |Model size to use, either `base` or `large`


#### 3.4.2 DataRaider – Image-to-Data Conversion  

DataRaider can be run using the settings provided in `scripts/startup.json` using:
```sh
dataraider
```

Or can be run using command line arguments with the following:
```sh
dataraider   --config ./scripts/startup.json   --image_dir /path/to/save/images   --prompt_dir ./Prompts   --json_dir ./
```

| Option        | Description |
| --------       | ------- |
| `--config`     | Path to the configuration file. If specified, ignores other arguments |
| `--image_dir`  | Directory containing images to process     |
| `--prompt_dir` | Directory containing prompt files (should point to `Prompts` directory)    |
| `--json_dir`   | Directory to save processed JSON data
| `--keys`       | List of keys to extract
| `--new_keys`   | List of new keys for data extraction

*A sample output JSON is available in the `Assets` folder.*  

#### 3.4.3 KGWizard – Data-to-Knowledge Graph Translation

KGWizard comes with two commands.

##### 3.4.3.1 Transform Command

Converts raw JSON to intermediate format, optionally performs RAG lookup and updates database.

```bash
kgwizard transform    ./input_data   --output_dir ./results   --output_file ./results/my_graph.graphml   --substitutions "material:Material" "atmosphere:Atmosphere"   --address ws://localhost   --port 8182   --schema echem   --graph_name g
```

| Option        | Description |
| --------       | ------- |
|`input_dir` (positional argument) | Folder where the JSON files from DataRaider are stored
|`--output_dir` | Folder where the generate JSON intermediate files will be stored. The folder will be automatically created. Defaults to ./results.
|`--no_parallel`  |If active, run the conversions sequentially instead of using the dynamic increase parallel algorithm. Overrides the --workers flag.
|`--workers` |If defined, use this number of parallel workers instead of the dynamic increase algorithm.
|`--substitutions` | Substitution to be made in the instructions file. The input format consists on a pair formed by the substitution keyword and the node label separated by a colon (keyword:node_name). If substitutions are not given, RAG module will not be executed.
|`--dynamic_start` | Starting number of workers for the dynamic algorithms..
|`--dynamic_steps` | Maximum number of steps of the dynamic paralelization algorithm.
|`--dynamic_max_workers` | Maximum number of workers of the dynamic paralelization algorithm.
|`--address `| JanusGraph server address. Defaults to ws://localhost.
|`--port` | JanusGraph port. Defaults to 8182.
|`--graph_name` | JanusGraph graph name. Defaults to g.
|`--schema` | Node/Edge schema to be used during the json conversion. Can be either a path or any of the default schemas: photo,org,echem. Defaults to echem
|`--output_file` |"If set, save the generated graph into the specified file after updating the database.


##### 3.4.3.2 Parse Command

Parses intermediate JSONs (from transform command) into schema-based graph and uploads to JanusGraph. It also saves a .graphml file representing the final graph state.

```bash
kgwizard parse    ./results   --address ws://localhost   --port 8182   --graph_name g   --schema /path/to/custom_schema.py   --output_file ./final_graph.graphml
```

| Option        | Description |
| --------       | ------- |
|`input_dir` (positional argument) | Folder where the JSON files from `transform` are stored
| `--address`     | JanusGraph server address. Defaults to ws://localhost |
| `--port`  | JanusGraph port. Defaults to 8182  |
| `--graph_name` | JanusGraph graph name. Defaults to g |
| `--schema`   | Node/Edge schema to be used during the json conversion. Can be either a path or any of the default schemas: photo,org,echem. Defaults to echem
| `--output_file`       | If set, save the generated graph into the specified file after updating the database


## 4. Running the MERMaid Web App (Recommended for New Users)

MERMaid comes with a web interface for running the modules interactively via a browser. 
You can configure your input folders, select extraction keys, and run modules with no coding required.

To launch the app locally:
```sh
./launch_webapp.sh
```

Then, open http://localhost:850x in your browser.

> You must have your **`OPENAI_API_KEY`** set in your .env file (or terminal) before launching the app. You can follow the instructions in [3.2 Setting Up API Key](#32-setting-up-api-key) 

> A JanusGraph server is not required for the web interface to run, but is required if using either KGWIzard or the full MERMaid pipeline throught the interface (see [3.3.1 Start JanusGraph Server](#331-start-janusgraph-server))
---

### 5. Adapting MERMaid 

For instructions on how to extend DataRaider and KGWizard for your target chemical domains, please check out the [DataRaider README file](https://github.com/aspuru-guzik-group/MERMaid/blob/main/src/dataraider/README.md) and the [KGWizard README file](https://github.com/aspuru-guzik-group/MERMaid/blob/main/src/kgwizard/README.org)