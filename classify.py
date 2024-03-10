import pandas as pd
import numpy as np
import csv
import time
import random
import sys

from tqdm import tqdm
import GEOparse

from openai import OpenAI

def read_input(input_filename):
    df = pd.read_csv(input_filename)

    try:
        df = df[['Series', 'Sample', 'Sample Name', 'Method']]
    except:
        print("\nError! You input should have ['Series', 'Sample', 'Sample Name', 'Method'] columns.\n")
        exit()

    return df


def classify_category(api_key, gpt_model, df, output_filename):

    client = OpenAI(
        api_key=api_key,
    )

    gpt_model = 'gpt-3.5-turbo'
    # gpt_model = 'gpt-4-0125-preview' 
    
    methods_df = df

    with open(output_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Series', 'Sample Name', 'Category'])

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
            prompt = f"You are an expert biologist. You are looking at some metadata provided by Gene Expression Omnibus and the method section of the original manuscript. Please use the given metadata of the overall experiment and the metadata of the particular sample from that experiment to answer a few questions about the particular sample. "
            prompt += f"Based on its characteristics and method, classify the sample with one of the following options - [Cultured, Fetal, Primary]. If the sample is an in vitro sample, classify as Cultured. If the sample is from fetal tissue, classify as Fetal. If the sample is none of those, answer with Primary. Isolation of a specific cell type from blood and direct sequencing is not treated as cultured. Do not classify samples derived from the mother as fetal. Please use the given metadata of the overall experiment and the metadata of the particular sample from that experiment to answer a few questions about the particular sample. Do not be confused by the experiment metadata if the experiment mentions multiple samples. Prioritize the description about the particular sample in the experiment when answering questions."
            prompt += f"Please respond with one word only. "
            prompt += f"\n Here are the metadata associated: \n\n Description about the experiment: \n {context_gse_1} \n {context_gse_2}"
            prompt += f"\n Description about the particular sample in the experiment: \n {context_gsm_1} \n {context_gsm_2} \n {context_gsm_3} \n {context_gsm_4} \n {context_gsm_5} \n {context_gsm_6}"
            prompt += f"\n Method of the original manuscript: {method_text}"
            
            try:
                response = client.chat.completions.create(
                    model=gpt_model,
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0,
                )
                answer = response.choices[0].message.content
                
            except Exception as e:
                print(f"Error processing {gsm_id}: {e}")
                answer = "Error"    
            
            with open(output_filename, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([gse_id, gsm_id, answer])
            
            time.sleep(random.uniform(0.5, 1.5))  # Wait like a human


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage: python classify.py [input_file] [output_file] [API key]")
        exit()
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    api_key = sys.argv[3]

    # Read input and check format
    df = read_input(input_filename)

    # Run GPT
    classify_category(api_key, df, output_filename)
    print(f"\nYou can check your result in: {output_filename}\n")


