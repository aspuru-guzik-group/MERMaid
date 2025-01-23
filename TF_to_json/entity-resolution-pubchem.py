import pubchempy as pcp
import re
import json 
import os

def split_chemicals(value:str):
    components = [comp.strip() for comp in value.split(',')]
    result = []

    for component in components:
        print(component)
        match = re.match(r'(.+?)(\s*(\([^\)]+\)|\[[^\]]+\]))?\s*$', component)
        if match:
            chemical_name = match.group(1).strip()
            quantity = match.group(2).strip().replace('(', '').replace(')', '').replace('[', '').replace(']', '') if match.group(2) else None
        
            result.append((chemical_name, quantity))
        
    return result


def load_json(file_path:str): 
    with open(file_path, "r") as file:
        return json.load(file)


def pubchem_to_smiles(chemical: str): 
    """
    Helper function to replace a given common name/ chemical formula with the SMILES using Pubchempy, if found
    TODO: Should we implement for chemical formula -- usually there's multiple identifiers. 
    """
    try: 
        c = pcp.get_cids(chemical, 'name')
        if len(c) != 0: 
            compound = pcp.Compound.from_cid(c[0])
            c_smiles = compound.isomeric_smiles
            return c_smiles
    except:
        pass
    try: 
        c = pcp.get_compounds(chemical, 'formula')
        if len(c) != 0:
            c_smiles = c[0].isomeric_smiles
            return c_smiles
    except:
        pass
    
    return chemical


def _split_chemical(value: str, common_names: dict):
    """
    Helper function to split chemical (quantity) pairs and resolve all chemical entities 
    """
    components = [] 
    current_component = []
    bracket_level = 0
    result = []
    for char in value:
        if char in "([":
            bracket_level += 1
        elif char in ")]":
            bracket_level -= 1

        if char == ',' and bracket_level == 0:
            components.append(''.join(current_component).strip())
            current_component = []
        else:
            current_component.append(char)
    if current_component:
        components.append(''.join(current_component).strip())

    for component in components:
        match = re.match(r'(.+?)(\s*(\([^\)]+\)|\[[^\]]+\]))?\s*$', component)
        if match:
            chemical_name = match.group(1).strip()
            chemical_name = _process_mixed_chemicals(common_names, chemical_name)
            quantity = match.group(2).strip().replace('(', '').replace(')', '').replace('[', '').replace(']', '') if match.group(2) else None

            result.append((chemical_name, quantity))
    return result
         

def _process_mixed_chemicals(common_names:dict, chemicals:str):
    """
    Helper function to resolve mixed chemical systems.
    """
    if ":" in chemicals or "/" in chemicals: 
        delimiter = ":" if ":" in chemicals else "/"
        components = chemicals.split(delimiter)
        resolved_components = [_replace_chemical(common_names, comp) for comp in components]
        resolved_components = [pubchem_to_smiles(comp) for comp in resolved_components]
        return delimiter.join(resolved_components)
    else:
        chemicals = _replace_chemical(common_names, chemicals)
        return pubchem_to_smiles(chemicals)


def _replace_chemical(common_names:dict, chemical:str):
    """
    Helper function to replace a chemical with a Pubchem common name using a customized list to cover commonly missed chemicals
    """
    try:
        chemical = chemical.replace('TBA', 'nBu4N')
        value = common_names[chemical]
        return value
    except:
        return chemical


def _entity_resolution_entry(entry: dict, keys: list, common_names: dict):
    """
    Resolves and updates chemical entities for a given entry
    """
    for key in keys: 
        try: 
            value = entry.get(key, None)
            if value: 
                split_value = _split_chemical(value, common_names)
                entry[key] = split_value
        except:
            pass
    return entry


def _entity_resolution_rxn_dict(rxn_dict: dict, keys: list, common_names: dict):
    """
    Resolves and updates chemical entities for a given reaction dictionary
    """
    opt_runs = rxn_dict.get("Optimization Runs", {})
    for entry_id, rxn_entry in opt_runs.items():
        rxn_dict["Optimization Runs"][entry_id] = _entity_resolution_entry(rxn_entry, keys, common_names)
    return rxn_dict


def _save_json(file_path:str, data:dict):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)

COMMON_NAMES = {"nBu4NBF4": "Tetrabutylammonium tetrafluoroborate", 
                "n-Bu4NBF4": "Tetrabutylammonium tetrafluoroborate",
                "nBu4NCl": "Tetrabutylammonium chloride", 
                "n-Bu4NCl": "Tetrabutylammonium chloride",
                "nBu4NPF6": "Tetrabutylammonium hexafluorophosphate",
                "n-Bu4NPF6": "Tetrabutylammonium hexafluorophosphate",
                "nBu4NI": "Tetrabutylammonium iodide",
                "n-Bu4NI": "Tetrabutylammonium iodide",
                "nBu4NClO4": "Tetrabutylammonium perchlorate",
                "n-Bu4NClO4": "Tetrabutylammonium perchlorate"} 

KEYS =  ['Catalyst', 'Ligand', 'Solvents', 'Chemicals', 'Additives', 'Electrolytes']


def batch_proc_articles(input_dir, output_dir, keys=KEYS, common_names=COMMON_NAMES):
    for file in os.listdir(input_dir):
        try: 
            file_path = os.path.join(input_dir, file)
            output_path = os.path.join(output_dir, file)
            rxn_dict = load_json(file_path)
            resolved_dict = _entity_resolution_rxn_dict(rxn_dict, keys, common_names)
            _save_json(output_path, resolved_dict)
        except Exception as e: 
            continue


input_dir = "../extracted_rxn_dictionaries/organic_synthesis/"
output_dir = "../extracted_rxn_dictionaries/organic_synthesis_resolved/"
custom_keys = []
custom_common_names = {}        