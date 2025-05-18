import pubchempy as pcp
import re
import json 
import os
from pathlib import Path

"""
File containing post processing functions
"""

COMMON_NAMES = {"nBu4NBF4": "Tetrabutylammonium tetrafluoroborate", 
                "n-Bu4NBF4": "Tetrabutylammonium tetrafluoroborate",
                "Bu4NBF4": "Tetrabutylammonium tetrafluoroborate",
                "nBu4NCl": "Tetrabutylammonium chloride", 
                "n-Bu4NCl": "Tetrabutylammonium chloride",
                "Bu4NCl": "Tetrabutylammonium chloride", 
                "TBAC": "Tetrabutylammonium chloride",
                "nBu4NPF6": "Tetrabutylammonium hexafluorophosphate",
                "n-Bu4NPF6": "Tetrabutylammonium hexafluorophosphate",
                "nBu4NPF6": "Tetrabutylammonium hexafluorophosphate",
                "Bu4NPF6": "Tetrabutylammonium hexafluorophosphate",
                "nBu4NI": "Tetrabutylammonium iodide",
                "n-Bu4NI": "Tetrabutylammonium iodide",
                "Bu4NI": "Tetrabutylammonium iodide",
                "nBu4NClO4": "Tetrabutylammonium perchlorate",
                "n-Bu4NClO4": "Tetrabutylammonium perchlorate",
                "Bu4NClO4": "Tetrabutylammonium perchlorate", 
                "TBAB": "Tetrabutylammonium bromide", 
                "n-Bu4NBr": "Tetrabutylammonium bromide", 
                "nBu4NBr": "Tetrabutylammonium bromide", 
                "Bu4NBr": "Tetrabutylammonium bromide", 
                "IPA": "2-Propanol",
                "DCM": "Dichloromethane"} 

KEYS =  ['Catalyst', 'Ligand', 'Solvents', 'Chemicals', 'Additives', 'Electrolytes']

def split_chemicals(value:str):
    """
    Splits a string containing chemical information into components and their associated quantities.

    :param value: A string containing chemicals and their quantities (e.g., 'Tetrabutylammonium chloride (2.5 g), IPA (10 mL)').
    :type value: str
    
    :return: A list of tuples where each tuple contains the chemical name and its quantity.
    :rtype: list[tuple[str, str]]
    """
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
    """
    Loads a JSON file from the specified path.

    :param file_path: Path to the JSON file.
    :type file_path: str
    
    :return: Parsed JSON content.
    :rtype: dict
    """
    file_path = Path(file_path)
    with open(file_path, "r") as file:
        return json.load(file)


def pubchem_to_smiles(chemical: str, 
                      max_retries:int=1): 
    """
    Retrieves the SMILES representation of a given chemical name or formula from PubChem.
    Implements a retry mechanism in case of random errors during the PUG REST call.

    :param chemical: The common name or chemical formula to search for.
    :type chemical: str
    :param max_retries: Number of retries if the first attempt fails, defaults to 1.
    :type max_retries: int
    
    :return: SMILES representation of the chemical, or the original chemical name if not found.
    :rtype: str
    """
    def get_smiles(chemical):
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
        return None
    
    for _ in range(max_retries + 1):  
        smiles = get_smiles(chemical) 
        if smiles:
            return smiles
    return chemical


def _split_chemical(value: str, common_names: dict):
    """
    Helper function to split chemical (quantity) pairs and resolve all chemical entities.

    :param value: The string containing chemicals and their associated quantities.
    :type value: str
    :param common_names: A dictionary of common names for chemicals to resolve ambiguous entries.
    :type common_names: dict

    :return: A list of tuples where each tuple contains the resolved chemical name and its quantity.
    :rtype: list[tuple[str, str]]
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
    Resolves mixed chemical systems by replacing them with their SMILES representations or common names.
    NOTE: cannot tackle delimiter - because it will mess up names like n-Bu4NBr or 1,2-DCE
    :param common_names: A dictionary of common names for chemicals to resolve ambiguous entries.
    :type common_names: dict
    :param chemicals: The string containing mixed chemical systems to resolve.
    :type chemicals: str
    
    :return: The resolved string of chemicals with SMILES or common names.
    :rtype: str
    """
    if ":" in chemicals or "/" in chemicals or "–" in chemicals:
        chemicals = re.sub(r"[:/–]", ":", chemicals)
        delimiter = ":"
        components = chemicals.split(delimiter)
        resolved_components = [_replace_chemical(common_names, comp) for comp in components]
        resolved_components = [pubchem_to_smiles(comp) for comp in resolved_components]
        return delimiter.join(resolved_components)
    else:
        chemicals = _replace_chemical(common_names, chemicals)
        return pubchem_to_smiles(chemicals)


def _replace_chemical(common_names:dict, chemical:str):
    """
    Replaces a chemical with its resolved name from a dictionary of common names.

    :param common_names: A dictionary of common names for chemicals.
    :type common_names: dict
    :param chemical: The chemical name to resolve.
    :type chemical: str
    
    :return: The resolved chemical name.
    :rtype: str
    """
    try:
        value = common_names[chemical]
        return value
    except:
        return chemical


def _entity_resolution_entry(entry: dict, keys: list, common_names: dict):
    """
    Resolves and updates chemical entities for a given entry.

    :param entry: The dictionary representing a single entry (e.g., reaction or compound).
    :type entry: dict
    :param keys: The list of keys in the entry that represent chemical entities to resolve.
    :type keys: list[str]
    :param common_names: A dictionary of common names for chemicals.
    :type common_names: dict
    
    :return: The updated entry with resolved chemical entities.
    :rtype: dict
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


def _entity_resolution_rxn_dict_old(rxn_dict: dict, keys: list, common_names: dict):
    """
    Resolves and updates chemical entities for a reaction dictionary, including consolidating mixed solvent systems.

    :param rxn_dict: The dictionary representing a reaction with optimization runs and chemical entities.
    :type rxn_dict: dict
    :param keys: The list of keys representing chemical entities.
    :type keys: list[str]
    :param common_names: A dictionary of common names for chemicals.
    :type common_names: dict
    
    :return: The updated reaction dictionary with resolved chemical entities.
    :rtype: dict
    """
    opt_runs = rxn_dict.get("Optimization Runs", {})
    for entry_id, rxn_entry in opt_runs.items():
        rxn_dict["Optimization Runs"][entry_id] = _entity_resolution_entry(rxn_entry, keys, common_names)

        solvents = rxn_entry.get("Solvents", None)
        if solvents and len(solvents) > 1:
            names = ":".join(str(s[0]) for s in solvents)
            values = ":".join(str(s[1]) for s in solvents)
            values = None if all(v == "None" for v in values.split(":")) else values
            rxn_entry['Solvents'] = [[names, values]]

        rxn_dict["Optimization Runs"][entry_id] = rxn_entry
    return rxn_dict

def _entity_resolution_rxn_dict(rxn_dict: dict, keys: list, common_names: dict):
    """
    Resolves and updates chemical entities for a reaction dictionary, including consolidating mixed solvent systems.

    :param rxn_dict: The dictionary representing a reaction with optimization runs and chemical entities.
    :type rxn_dict: dict
    :param keys: The list of keys representing chemical entities.
    :type keys: list[str]
    :param common_names: A dictionary of common names for chemicals.
    :type common_names: dict
    
    :return: The updated reaction dictionary with resolved chemical entities.
    :rtype: dict
    """
    opt_key = next((k for k in rxn_dict if "optimization" in k.lower()), None)
    if opt_key is None:
        print("WARNING: Could not find optimization runs. Dictionary will not be cleaned.\n")
        return rxn_dict
    opt_runs = rxn_dict.get(opt_key, {})
    for entry_id, rxn_entry in opt_runs.items():
        rxn_entry = _entity_resolution_entry(rxn_entry, keys, common_names)

        solvents = rxn_entry.get("Solvents", None)
        if solvents and len(solvents) > 1:
            names = ":".join(str(s[0]) for s in solvents)
            values = ":".join(str(s[1]) for s in solvents)
            values = None if all(v == "None" for v in values.split(":")) else values
            rxn_entry['Solvents'] = [[names, values]]

        rxn_dict[opt_key][entry_id] = rxn_entry
    return rxn_dict


def _save_json(file_path:str, data:dict):
    """
    Saves the given data to a JSON file at the specified path.

    :param file_path: The path where the JSON file should be saved.
    :type file_path: str
    :param data: The data to save to the JSON file.
    :type data: dict
    
    :return: Nothing, all information saved to the JSON at file_path
    :rtype: None
    """    
    file_path = Path(file_path)
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def _process_raw_dict(image_name:str, 
                      json_directory:str, 
                      keys=KEYS, 
                      common_names=COMMON_NAMES):
    """ 
    Processes the extracted reaction dictionary, resolving chemical entities and updating the file.

    :param image_name: The name of the image associated with the JSON data.
    :type image_name: str
    :param json_directory: The directory where the JSON file is located.
    :type json_directory: str
    :param keys: List of keys representing the chemical entities to resolve, defaults to KEYS.
    :type keys: list[str]
    :param common_names: Dictionary of common names to replace ambiguous chemicals, defaults to COMMON_NAMES.
    :type common_names: dict
    
    :return: Nothing, all file saved to the JSON at file_path
    :rtype: None
    """
    json_directory = Path(json_directory)
    file_path = json_directory / f"{image_name}.json"
    rxn_dict = load_json(file_path)
    resolved_dict = _entity_resolution_rxn_dict(rxn_dict, keys, common_names)
    _save_json(file_path, resolved_dict)


