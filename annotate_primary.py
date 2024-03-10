import pandas as pd
import numpy as np
import csv
import time
import random
import sys
import os
import subprocess

from tqdm import tqdm
import GEOparse

from openai import OpenAI


def read_input(input_filename):
    df = pd.read_csv(input_filename)

    try:
        df = df[['Series', 'Sample Name', 'Method', 'Category']]
    except:
        print("\nError! You input should have ['Series', 'Sample Name', 'Method', 'Category'] columns.\n")
        exit()

    df = df[df['Category']=='Primary'].copy()

    return df


def answer_to_dict(answer):
    result_dict = {}
    
    answers = [x for x in answer.split("\n") if len(x) > 0]

    for line in answers:
        # remove whitespace
        pair = line.strip()

        # split
        key, value = pair.split(":")

        # remove whitespace
        key = key.strip()
        value = value.strip()

        result_dict[key] = value
    
    return result_dict


def annotate(api_key, df, output_filename):
    # Organ term list
    org = pd.read_csv("/home/smcheong/scParse/Organ_list.csv")
    organ_list = org['Organ'].tolist()

    # Disease term list
    dis = pd.read_csv("/home/smcheong/scParse/Disease_list.csv")
    disease_list = dis['Disease_Cancer'].tolist()
    
    # Cancer_Tissue term list
    cancer_tissue_list = ['Tumor', 'Adjacent_Normal', 'Metastasis', 'Blood']

    assert organ_list
    assert disease_list
    assert cancer_tissue_list

    gpt_model = 'gpt-3.5-turbo'
    # gpt_model = 'gpt-4-0125-preview'

    # Dataframe with methods
    methods_df = df

    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Series', 'Sample Name', 'Organ', 'Healthy', 'Disease', 'Cancer_Tissue', 'Age', 'Sex'])

    # Create method data for each GSE as a dictionary
    gse_method_dict = methods_df.groupby('Series')['method'].first().to_dict()

    # subset GSE
    number_of_GSE = len(set(methods_df['Series']))
    print(f"Total number of GSE IDs: {number_of_GSE}")

    for gse_id, method_text in tqdm(gse_method_dict.items()):
        
        # GEOparse
        try:
            gse = GEOparse.get_GEO(geo=gse_id, silent=True)
        except Exception as e:
            print(f"Error downloading {gse_id}: {e}")
            continue
            
        context_gse_1 = " ".join(gse.metadata['summary'])
        context_gse_2 = " ".join(gse.metadata['overall_design'])

        # GPT prompt for each GSM
        for gsm_id in gse.gsms:
            
            # We only want information of GSMs in our metadata
            if gsm_id not in methods_df['Sample Name'].values:
                continue
            
            # GEOparse info for that GSM
            gsm = gse.gsms[gsm_id]
            context_gsm_1 = " ".join(gsm.metadata.get('characteristics_ch1', []))
            context_gsm_2 = " ".join(gsm.metadata.get('title', []))
            context_gsm_3 = " ".join(gsm.metadata.get('geo_accession', []))
            context_gsm_4 = " ".join(gsm.metadata.get('source_name_ch1', []))
            context_gsm_5 = " ".join(gsm.metadata.get('extract_protocol_ch1', []))
            context_gsm_6 = " ".join(gsm.metadata.get('characteristics_ch1', []))
            
            # Ask GPT with GEOparse-GSMcharacteristics and PMC-method
            
            # Introduction
            prompt = f"You are an expert biologist. You are looking at some metadata provided by Gene Expression Omnibus and the method section of the original manuscript. Please use the given metadata of the overall experiment and the metadata of the particular sample from that experiment to answer a few questions about the particular sample. You can also use the given method section of the original manuscript. "
            prompt += f"Do not be confused by the experiment metadata if the experiment mentions multiple samples. Prioritize the description about the particular sample in the experiment when answering questions. Pay special notice to metadata related to the *particular sample* if the metadata of the experiment describes multiple types of samples. "
            prompt += f"Here are the questions: \n\n"

            # Main questions
            prompt += f"\n [Organ] What organ is the sample from? Answer with one of the following options: \n {organ_list}"
            prompt += f"\n [Healthy] Is the sample from a healthy individual? Answer with *Yes* or *nan*. The cancer adjacent normal sample should be classified as *nan*. \n"
            prompt += f"\n [Disease] What type of disease is the sample from? If the sample is from a healthy individual, please answer with nan. Answer with one of the following options: \n {disease_cancer_list}"
            prompt += f"\n [Cancer_Tissue] If it is a cancer sample, which tissue the sample is from? The adjacent normal sample should not be classified as healthy but should be classified as *Adjacent_Normal*. If it is not a cancer sample, please answer with *nan*. Answer with one of the following options: \n {cancer_tissue_list}"

            # Age, Sex
            prompt += f"\n [Age] If available, what is the age of the patient the sample is derived from? Answer in years or in days and weeks. Answer with *nan* if not available."
            prompt += f"\n [Sex] Is the sample derived from a male or female patient? Answer with letter *F* or M*. Answer with nan if not available."
            
            # Tuning
            prompt += f"When a sample contains the word cortex, it may not necessarily be a brain sample. "
            prompt += f"Even if the exact matching term does not seem to be among the options provided, you *must* select the closest option from the provided list by using your medical knowledge. "
            prompt += f"If you are not sure, answer with 'Uncertain'. "
            
            # Providing data
            prompt += f"\n [1] Here are the metadata associated: \n" 
            prompt += f"[1-1] Description about the experiment: \n {context_gse_1} \n {context_gse_2}"
            prompt += f"\n [1-2] Description about the particular sample in the experiment: \n {context_gsm_1} \n {context_gsm_2} \n {context_gsm_3} \n {context_gsm_4} \n {context_gsm_5} \n {context_gsm_6}"
            prompt += f"\n [2] Method of the original manuscript: {method_text}"
            
            # Formatting output
            prompt += f"Answer in the following *exact* answer structure: \n\n Organ: [answer] \n Healthy: [answer] \n Disease: [answer] \n Cancer_Tissue: [answer] \n Age: [answer] \n Sex: [answer] \n\n"
            
            try:
                response = client.chat.completions.create(
                    model=gpt_model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                )
                answer = response.choices[0].message.content
                
            except Exception as e:
                print(f"Error processing {gsm_id}: {e}")
                answer = "Error"    
            
            with open(output_filename, 'a', newline='') as file:
                result_dict = answer_to_dict(answer)
                result_row = [gse_id, gsm_id] + list(result_dict.values())
                
                writer = csv.writer(file)
                writer.writerow(result_row)
            
            time.sleep(random.uniform(0.5, 1.5))  # Wait like a human
        

def remove_GEOparse_pybroduct():
    pwd = os.getcwd()
    if subprocess.call(f"rm {pwd}/GSE*.gz", shell=True):
        print("Error occured while removing unnecessary GEOparse byproduct files.")


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage: python annotate_primary.py [input_file] [output_file] [API key]")
        exit()
    
    # Read input and check format
    df = read_input(input_filename)

    # Run GPT
    annotate(api_key, df, output_filename)

    print(f"\nYou can check your result in: {output_filename}")

    remove_GEOparse_pybroduct()

