"""
Contains code for evaluation of text from papers
"""
import numpy as np
import json
import os

###############################
# CONSTANTS
###############################

CATEGORIES = {"electrosynthesis", "organic_synthesis", "photocatalysis"}
SYNTHESIS_COMPLETED = {'c6ob00076b', '10.1021acs.orglett.2c00362', '10.1002adsc.202100082', 'c6ob00108d', 'd1sc01130h', 'd1ra02225c', '10.1021acs.joc.4c00501', 'PIIS2666386423005271', 'c5sc00238a', '1-s2.0-S2666554924000966-main', '10.1021acs.orglett.6b01132', '1-s2.0-S2666386423003818-main', 'd4ra04674a', 'd3sc00803g', 'd4ra03939d', 'd3gc02735j', '1-s2.0-S2773223124000165-main', 'd4sc00403e', '1-s2.0-S2666554921000818-main', 'd0sc00031k', 'd4sc02969k', '1-s2.0-S2451929419305583-main', '10.1002ejoc.202400146', 'd4su00258j', 'c6sc03236b', 'c8sc04482a'}
SYNTHESIS_ERRORS = {'1-s2.0-S2589004219302299-main.pdf', 'd4sc04222k.pdf', 'adsc202100082-sup-0001-misc_information.pdf', '1-s2.0-S2589004222021691-main.pdf'}

ELECTROSYNTHESIS_COMPLETED = {'10.1002anie.202212131', '10.1002asia.202200780', 'd3ob00831b', '10.1002chem.202201654', 'c8ob03162b', 'd2cc03883h', '10.1002anie.202201595', 'd2gc00457g', 'c8cc09899a', '10.1002ajoc.202200719', '10.1002adsc.202301343', 'c8cc06451b', 'd2ob01402e', 'd1ob00079a', '10.1002anie.201909951', '10.1002anie.201610715', '10.1002anie.201700012', '10.1002chem.201802832', '10.1002adsc.202300118', '10.1002ejoc.201901928', '10.1002celc.202101155', 'd2gc04399h', 'c9cc03789f', '10.1002celc.201900080', 'c9cc00975b', 'd3qo00204g', '10.1002ejoc.202300553', '10.1002celc.201900138', '10.1002cctc.202300258', '10.1002adsc.202200003', '10.1002anie.202207660', '10.1002adsc.202200932', '10.1002ajoc.202100620', 'd2gc02086f', '10.1002ajoc.202300294', 'd1qo00038a', '10.1002ejoc.202300927', '10.1002anie.202013478', 'd3gc02701e'}
ELECTROSYNTEHSIS_ERRORS = {'d3gc03389a.pdf'}

PHOTOCATALYSIS_COMPLETED = {'cs2c04316', 'anie201705333', 'adsc_201400638', 'cs3c02092', 'cs3c05785_si_001', 'anie202000907-sup-0001-misc_information', 'anie201805732', 'cs2c00468', 'cs3c01713', 'cs4c00565_si_001', 'anie_201406393', 'cs2c01442', 'cs4c02320', 'jo3c00023', 'cs3c05150', 'anie201805732-sup-0001-misc_information', 'cs9b00287', 'anie202217638', 'anie201802656', 'anie202110257', 'anie_201308820_sm_miscellaneous_information', 'anie_201405359_sm_miscellaneous_information', 'cs2c04736', 'anie202000907', 'cs0c02250', 'anie_201405359', 'cs2c01442_si_001', 'ejoc201900839', 'cs4c00565', 'cs4c02797', 'cs3c05785', 'adsc_201400638_sm_miscellaneous_information', 'anie_201308820', 'anie202311984', 'cs7b00799', 'cs2c03805'}
PHOTOCATALYSIS_ERRORS = {'anie202110257-sup-0001-misc_information.pdf', 'ejoc201900839-sup-0001-supmat.pdf', 'anie_201406393_sm_miscellaneous_information.pdf', 'cs2c04736_si_001.pdf', 'cs8b02844_si_001.pdf', 'chem202104329-sup-0001-misc_information.pdf', 'jo3c00023_si_001.pdf', 'cs9b00287_si_001.pdf', 'chem202104329.pdf', 'cs4c02320_si_001.pdf', 'cs3c01713_si_001.pdf', 'anie201705333-sup-0001-misc_information.pdf', 'cs8b02844.pdf', 'anie201802656-sup-0001-misc_information.pdf', 'cs3c05150_si_001.pdf', 'cs0c02250_si_001.pdf', 'cs2c04316_si_001.pdf', 'cs2c00468_si_001.pdf', 'cs3c02092_si_001.pdf', 'anie202311984-sup-0001-misc_information.pdf', 'cs4c02797_si_001.pdf', 'cs2c03805_si_001.pdf', 'anie202217638-sup-0001-misc_information.pdf', 'cs7b00799_si_001.pdf'}


###############################
# EVALUATION METRICS
###############################

def calculate_ter_score(generated: str, 
                        ground_truth: str):
    edits = edit_distance(ground_truth, generated)
    ref_length = len(ground_truth.split())

    ter_score = edits / ref_length if ref_length > 0 else float('inf')
    return ter_score


def edit_distance(ref, hyp):
    ref_words = ref.split()
    hyp_words = hyp.split()

    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1,   
                           d[i][j - 1] + 1,    
                           d[i - 1][j - 1] + cost)  
    ter_score = d[len(ref_words)][len(hyp_words)]

    return round(ter_score, 3)

#normalized TER
def calculate_normalized_ter(generated: str, 
                             ground_truth: str):
    """Calculate the normalized Translation Edit Rate (TER)."""
    gt_tokens = ground_truth.split()
    generated_tokens = generated.split()

    # Calculate the Levenshtein distance
    edit_distance = levenshtein_distance(gt_tokens, generated_tokens)

    # Calculate normalized TER
    if len(gt_tokens) + edit_distance == 0:  # To avoid division by zero
        return 0.0
    normalized_ter = edit_distance / (len(gt_tokens) + edit_distance)

    return round(normalized_ter, 3)

def levenshtein_distance(gt_tokens, ocr_tokens):
    """Calculate the Levenshtein distance between two lists of tokens."""
    if len(gt_tokens) < len(ocr_tokens):
        return levenshtein_distance(ocr_tokens, gt_tokens)

    # Create a distance matrix
    distances = np.zeros((len(gt_tokens) + 1, len(ocr_tokens) + 1))

    # Initialize the distance matrix
    for i in range(len(gt_tokens) + 1):
        distances[i][0] = i
    for j in range(len(ocr_tokens) + 1):
        distances[0][j] = j

    # Compute the distances
    for i in range(1, len(gt_tokens) + 1):
        for j in range(1, len(ocr_tokens) + 1):
            cost = 0 if gt_tokens[i - 1] == ocr_tokens[j - 1] else 1
            distances[i][j] = min(
                distances[i - 1][j] + 1,    # Deletion
                distances[i][j - 1] + 1,    # Insertion
                distances[i - 1][j - 1] + cost  # Substitution
            )

    return distances[len(gt_tokens)][len(ocr_tokens)]


def jaccard_similarity(str1, str2):
    set1, set2 = set(str1), set(str2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    similarity = intersection / union if union > 0 else 0.0
    return (round(similarity, 2))

###############################
# TEXT EVALUATION CODE
###############################

TP_THRESHOLD = 0.70
FP_THRESHOLD = 100

def evaluate_text() -> None:
    """Performs text evaluation on the retreived categories
    """
    for category in CATEGORIES:
        print("Evaluating category " + category)
        # directory in results folder for current category
        result_dir = "../openchemie/" + category
        # directory for the ground truth labels for current category
        ground_truth_dir = "../ocr_eval_results/captions_groundtruth/" + category
        # store uncompared results 
        uncompared_articles = []
        # list of all the different paper names in current result category
        directories = [f for f in os.listdir(result_dir)]
        for dir in directories:
            if not dir.endswith(".json") and dir != "eval":
            
            # if there was no error meaning we extracted text and figure properly
                if dir not in ELECTROSYNTEHSIS_ERRORS.union(PHOTOCATALYSIS_ERRORS).union(SYNTHESIS_ERRORS):
                    print("Evaluating paper " + dir)
                    
                    # get the generated text
                    retrieved_text_file = result_dir + "/" + dir + "/retrieved_text.json"

                    try: 
                        with open(retrieved_text_file, "r") as json_file:
                            generated_text = json.load(json_file)
                        gen_keys = [gen_key for gen_key, gen_value in generated_text.items()]

                        # find the matching ground truth json file
                        ground_truth_text = None
                        try: 
                            ground_truth_file = ground_truth_dir + "/" + dir + "_cleaned.json"
                            with open(ground_truth_file, "r") as json2_file: 
                                ground_truth_text = json.load(json2_file)
                            
                            # evaluate
                            evaluation_results = {}
                            (evaluation_results["total"], 
                                evaluation_results["TP"], 
                                evaluation_results["FN"], 
                                evaluation_results["FP"]) = len(ground_truth_text), 0, 0, 0
                            
                            uncompared_gt = {}
                            uncompared_generated ={}
                            tracked = set()
                            
                            for key, value in ground_truth_text.items(): 
                                if key not in gen_keys: 
                                    evaluation_results["FN"] += 1
                                    uncompared_gt[key]= value
                                    
                                # elif len(generated_text[key]) - FP_THRESHOLD > len(ground_truth_text[key]): 
                                #     evaluation_results["FP"] += 1
                                #     tracked.add(key)
                                
                                similarity_score = jaccard_similarity(ground_truth_text[key], generated_text[key])
                                tracked.add(key)
                                if similarity_score > TP_THRESHOLD and len(generated_text[key]) - FP_THRESHOLD > len(ground_truth_text[key]):
                                    evaluation_results["FP"] += 1
                                elif similarity_score < TP_THRESHOLD: 
                                    evaluation_results["FN"] += 1
                                else:
                                    evaluation_results["TP"] += 1
                            
                            for key, value in generated_text.items():
                                if key not in tracked: 
                                    uncompared_generated[key]= value 

                            # write evaluation results
                            results = [evaluation_results, uncompared_gt, uncompared_generated]
                            with open(result_dir + "/eval/" + dir + "_caption_evaluation.json", "w") as eval_json:
                                json.dump(results, eval_json, indent=4)
                            print(f"{dir} has been evaluated.")
                            print()
                            
                            # track uncompared results
                            # uncompared_results = [uncompared_gt, uncompared_generated] 
                            # with open(result_dir + "/eval/" + dir + "_uncompared_captions.json", "w") as file: 
                            #     json.dump(uncompared_results, file, indent = 4)
                            # print(f"{dir} has been evaluated.")
                            # print()

                        except Exception as e:
                            print(f"{dir} is not evaluated. Check again.")
                            print()
                            uncompared_articles.append((dir, str(e)))
                            continue
                    except Exception as e:
                        print(f"result file for {dir}. Check again.")
                        print()
                        uncompared_articles.append((dir, str(e)))
                        continue

        with open(result_dir + "/unprocessed articles.json", "w") as unprocessed_json: 
            json.dump(uncompared_articles, unprocessed_json, indent=4)
            print("Unprocessed articles have been saved.")

        
if __name__ == "__main__":    
    evaluate_text()