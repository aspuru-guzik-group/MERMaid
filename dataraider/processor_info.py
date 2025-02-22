#from rxnscribe import RxnScribe #need separate installation from https://github.com/thomas0809/RxnScribe 

"""
Contains DataRaiderInfo class
"""

class DataRaiderInfo():
    
    """
    Stores global information required for DataRaider processing
    
    :param api_key: OpenAI API key
    :type api_key: str
    :param model: RxnScribe instance, used to extract reaction information
    :type model: RxnScribe
    :param vlm_model: model id of OpenAI model to use, defaults to gpt-4o-2024-08-06
    :type vlm_model: str
    
    """
    
    def __init__(self,  
                 api_key:str,
                 vlm_model = "gpt-4o-2024-08-06",
                 device='cpu', 
                 ckpt_path:str=None):
        self.api_key = api_key
        self.vlm_model = vlm_model
        # TODO fix rxnscribe compatibility issue
        self.model = None
        #self.model = RxnScribe(ckpt_path, device=torch.device(device)) # initialize RxnScribe to get SMILES 
