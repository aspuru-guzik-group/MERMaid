# KGWizard

## Automated Database Parser and Transformer

KGWizard is a Python command-line tool designed to:
- Transform JSONs from DataRaider into an intermediate format.
- Parse that intermediate format and optionally upload it to a JanusGraph database.
- Support dynamic and static parallelism for efficient processing.
- Perform RAG (Retrieval-Augmented Generation) lookups against an existing graph to substitute known nodes.

## Table of Contents
1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
   - [Transform Command](#transform-command)
   - [Parse Command](#parse-command)
5. [Environment Variables](#environment-variables)
6. [Extending KGWizard](#extending-kgwizard)
   - [Use echem.py as your template](#use-echem-py-as-your-template)
   - [Add your domain-specific classes](#add-your-domain-specific-classes)
   - [Select your schema at run time](#select-your-schema-at-run-time)
   - [Adjusting the LLM instructions](#adjusting-the-llm-instructions)
7. [Contributing](#contributing)
<!-- 8. [License](#license) -->

## Features

- **Dynamic Parallel Execution** using Python’s `multiprocessing` to speed up large-scale transformations.
- **RAG Integration** to retrieve existing nodes in the JanusGraph database for substituting references.
- **Modular** with separate subcommands for transformation and parsing.
- **Schema Loading** at runtime, either from built-in defaults or user-provided schema files.
- **Fallback for Older Typing Features** ensures compatibility with Python 3.9+.

## Requirements

- **Python 3.9 or higher**
- External libraries (auto-installed via `pip`):
  - [numpy](https://pypi.org/project/numpy/)
  - [gremlin_python](https://pypi.org/project/gremlinpython/)
  - [openai](https://pypi.org/project/openai/)

> A running JanusGraph server is needed for uploading data (instructions below).

## Installation

```bash
git clone https://github.com/aspuru-guzik-group/MERMaid.git
cd MERMaid
pip install -e .[kgwizard]
```
Use the ~-e~ flag command to make changes on the prompt files inside ~prompt/assets~.

Install the package in editable mode (~pip install -e .[kgwizard]~) so new schema files are auto-discovered.

### JanusGraph Setup

1. Install Java 8 SE from [Oracle](https://www.oracle.com/ca-en/java/technologies/javase/javase8-archive-downloads.html).
2. Install [JanusGraph](https://github.com/JanusGraph/janusgraph/releases), tested with version 1.1.0.
3. Unzip the JanusGraph zip file. 
```bash
unzip janusgraph-1.1.0.zip
cd janusgraph-1.1.0
```

3. Start JanusGraph Server (Choose either option):

Foreground:
```bash
./bin/janusgraph-server.sh ./conf/gremlin-server/gremlin-server.yaml
```

Background:
```bash
./bin/janusgraph-server.sh start
```

Terminate (background):
```bash
./bin/janusgraph-server.sh stop
```
- if you are running in the foreground, terminate using Ctrl+C. 

> **Note**: Server requires 2–8 GB RAM.

## Usage

```bash
kgwizard <command> [options]
```

### Transform Command

Converts raw JSON to intermediate format, optionally performs RAG lookup and updates database.

```bash
kgwizard transform ./input_data   --output_dir ./results   --output_file ./results/my_graph.graphml   --substitutions "material:Material" "atmosphere:Atmosphere"   --address ws://localhost   --port 8182   --schema echem   --graph_name g
```

Options include:
- `--no_parallel` (run sequentially)
- `--workers N` (use a fixed number of parallel workers)
> If neither ~--no_parallel~ nor ~--workers~ is set, kgwizard applies *dynamic parallel execution*.
- `--substitutions token:NodeType` (replaces the ~token~ in the prompt files (marked as ~{token}~)  by the unique nodes of ~NodeType~ found in the janus database. Note that lines in ~instructions~ that are contain a token and are not succesfully replaced are removed from the final prompt.)
- `--schema`, `--output-dir`, `--output-file` (define the output directory of the intermediate JSONs and the path of the generated graph database respectively)

### Parse Command

Parses intermediate JSONs (from transform command) into schema-based graph and uploads to JanusGraph. It also saves a .graphml file representing the final graph state.

```bash
kgwizard parse ./results   --address ws://localhost   --port 8182   --graph_name g   --schema /path/to/custom_schema.py   --output_file ./final_graph.graphml
```

## Environment Variables

The OpenAI API key is needed to run `transform`:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## Extending KGWizard

### Use `echem.py` as your template

Found at `graphdb/schemas/echem.py`, includes:
- `VertexBase`, `EdgeBase`, `Connection`
- Generic vertices/edges (Reaction, Compound, ...)
- Utility functions

Copy and edit for custom schemas.

### Add your domain-specific classes
Append only the *new* vertices and edges that are unique to your chemistry domain.  The generic bases are already in *echem.py*.

Key points: 
- *Class names become Gremlin labels*.  
  If your vertex class is ~IrradiationConditions~, then the JSON must contain ~"label": "IrradiationConditions"~.

- *EdgeBase generics link edges to the correct vertices*.
  Example from the current schema:
  
  ```python  
  @dataclass
  class HasConditions(EdgeBase[Reaction, IrradiationConditions]):
      pass
  ```
  In this example, *source* must be a ~Reaction~, *target* must be an ~IrradiationConditions~.  Python type checkers catch mistakes, and the LLM sees these hints inside the ~{code}~ block of the prompt, so it generates the right connections.

- *Extra fields on an edge become edge properties*.  
  Edge ~HasPhotocatalyst~ illustrates this:
  ```python
  @dataclass
  class HasPhotocatalyst(EdgeBase[Reaction, Compound]):
      value: Optional[float] = None
      unit:  Optional[str]  = None
 ```
  The JSON for this edge must supply *value* and *unit* as numeric or text properties, not embed them in the vertex name.

Example: adding a pressure vertex and edge

```python
@dataclass
class Pressure(VertexBase):
    unit: str
    value: float

@dataclass
class HasPressure(EdgeBase[Reaction, Pressure]):
    measured_with: Optional[str] = None
```

> What the typing achieves

  1. *Parsing*  
    Labels in the incoming JSON are looked up in ~VERTEX_CLASSES~ and ~EDGE_CLASSES~.  If they do not match, parsing fails, which protects the database from bad entries.

  2. *Prompt generation*  
    The complete schema file is inserted into the prompt through the ~{code}~ token.  The LLM therefore sees every type hint and knows automatically that, for instance, ~Pressure.value~ must be convertible to float. This tight coupling of schema and prompt improves generation quality.

Checklist:
- Pick clear, unique class names.  
- Fix the generics on every edge, for example ~EdgeBase[Study, Reaction]~.  
- Keep all code in one file so the LLM sees the entire schema.

### Select your schema at run time
If you saved the modified file as, say, =graphdb/schemas/photo.py=:

```bash
kgwizard transform ... --schema photo
kgwizard parse ... --schema /absolute/path/photo.py
```

### Adjusting the LLM instructions

Prompt templates live in `kgwizard/prompt/assets/`:

- `header` — intro text
- `instructions` — bullet list for LLM
- `tail` — closing instructions

Substitutions & RAG
- Add ~--substitutions "token:VertexLabel"~ at the CLI. This *enables Retrieval-Augmented Generation (RAG)*: kgwizard queries the connected JanusGraph for *unique* vertex names of *VertexLabel* and replaces ~{token}~ with the *comma-separated list* it finds.
- If a token is *not listed* in ~--substitutions~, or the query returns *no vertices*, every line in =instructions= still containing that token is *deleted* before the prompt is sent. This keeps the prompt compact and avoids confusing the model.


> Tokens `{token}`, `{json}`, and `{code}` are auto-replaced by the builder logic in `kgwizard/prompt/builder.py`

## Contributing

1. Fork or clone repo.
2. Create a feature branch.
3. Submit a pull request after testing.

Contributions welcome for:
- New schemas
- Performance/parallelism improvements
- Enhanced RAG logic
- New LLM connectors

## License

Distributed under the MIT License.