from rxnscribe import RxnScribe
import torch

"""
Contains DataRaiderInfo class, global information shared throughout different files of dataraider module
"""

class DataRaiderInfo():
    
    """
    Stores global information required for DataRaider processing
    
    :param api_key: OpenAI API key
    :type api_key: str
    :param model: RxnScribe instance, used to extract reaction information
    :type model: RxnScribe
    :param vlm_model: Model id of OpenAI model to use, defaults to "gpt-4o-2024-08-06"
    :type vlm_model: str
    
    """
    
    def __init__(self,  
                 api_key:str,
                 vlm_model = "gpt-4o-2024-08-06",
                 device='cpu', 
                 ckpt_path:str=None):
        """Constructor method

        :param api_key: OpenAI API key
        :type api_key: str
        :param vlm_model: Model id of OpenAI model to use, defaults to "gpt-4o-2024-08-06"
        :type vlm_model: str, optional
        :param device: Specifies whether to use CPU or GPU, defaults to 'cpu'
        :type device: str, optional
        :param ckpt_path: Specifies ckpt path, defaults to None
        :type ckpt_path: str, optional
        """
        self.api_key = api_key
        self.vlm_model = vlm_model
        self.model = RxnScribe(ckpt_path, device=torch.device(device)) # initialize RxnScribe to get SMILES 
