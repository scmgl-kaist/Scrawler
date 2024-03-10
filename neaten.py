import pandas as pd
import numpy as np

from openai import OpenAI


def read_input(input_filename):
    df = pd.read_csv(input_filename)

    try:
        df = df[['Series', 'Sample Name', 'Organ', 'Healthy', 'Disease', 'Cancer_Tissue', 'Age', 'Sex']]
    except:
        print("\nError! You input should have ['Series', 'Sample Name', 'Organ', 'Healthy', 'Disease', 'Cancer_Tissue', 'Age', 'Sex'] columns.\n")
        exit()

    return df


def answer_to_dict(answer):
    result_dict = {}
    
    answers = [x for x in answer.split("\n") if len(x) > 0]

    for line in answers:
        # remove whitespace
        pair = line.strip()

        # split
        try:
            key, value = pair.split(":")
        except:
            print("Something when wrong while formatting GPT output.")
            print("Output looks like this:")
            print(answer)
            exit()

        # remove whitespace
        key = key.strip()
        value = value.strip()

        result_dict[key] = value
    
    return result_dict


def neaten_up(api_key, df):
    # Disease term list
    dis = pd.read_csv("/home/smcheong/SCraper/Disease_list.csv")
    disease_list = dis['Disease_Cancer'].tolist()

    # unorganized words -> target words
    target_words = disease_list
    unorganized_words = sorted(set(df[~df['Disease'].isna()]['Disease']))

    # GPT
    client = OpenAI(
        api_key=api_key,
    )

    assert unorganized_words
    assert target_words
    assert client

    gpt_model = 'gpt-3.5-turbo'
    # gpt_model = 'gpt-4-0125-preview'

    # Intro
    prompt = "You are an expert biologist looking at some human diseases. "
    prompt += "Don't say anything else, just include the mapping results in your answer. "

    # Main task
    prompt += "Given two sets, A and B, where both A and B represent sets of diseases, your task is to replace the elements in set A with their corresponding elements in set B. "
    prompt += "Since the terms in set A are redundant and irregular, we are tyring to map them to the organized terms in set B. "
    prompt += " In other words, create a mapping such that each element in set A is replaced with the matching element in set B based on their respective disease names. "

    # Tuning
    prompt += "Even if the exact matching term does not seem to be among the options provided, you *must* select the closest option from the provided list by using your medical knowledge. "
    prompt += "Nevertheless, if mapping a word from set A to set B is seems impossible, the mapping should be done using the format: `Other_{original word in A}`. "

    # Inputs
    prompt += "\n\n Here are the sets: "
    prompt += f"\n\n[A]: {unorganized_words}"
    prompt += f"\n\n[B]: {target_words}"

    # Formatting output
    prompt += "\n\n You must include every words in set A in your answer. Answer in the following *exact* answer structure: \n\n word in A: word in B ..."

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

    # Mapping
    mapping = answer_to_dict(answer)
    mapping[np.nan] = np.nan
    swapped_df = df.copy()
    swapped_df['Disease'] = [mapping[x] for x in swapped_df['Disease']]
    
    return swapped_df


def split_cancer(swapped_df):
    # Cancer_Type term list
    can = pd.read_csv("/home/smcheong/SCraper/Cancer_list.csv")
    cancer_list = can['Cancer_type'].tolist()

    # Split Cancer Types from Disease
    swapped_df['Cancer_Type'] = np.nan
    swapped_df.loc[swapped_df['Disease'].isin(cancer_type_list), 'Cancer_Type'] = swapped_df['Disease']
    swapped_df.loc[swapped_df['Disease'].isin(cancer_type_list), 'Disease'] = 'Cancer'

    neat_df = swapped_df.copy()

    return neat_df


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage: python neaten.py [input_file] [output_file] [API key]")
        exit()
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    api_key = sys.argv[3]
    
    # Read input and check format
    df = read_input(input_filename)

    # Run GPT
    swapped_df = neaten_up(api_key, df)

    # Split Cancer
    neat_df = split_cancer(swapped_df)

    # Tidy up healthy columns
    neat_df.loc[~neat_df['Disease'].isna(), 'Healthy'] = np.nan
    neat_df.loc[~neat_df['Cancer_Type'].isna(), 'Healthy'] = np.nan
    neat_df = neat_df[['Series', 'Sample Name', 'Organ', 'Healthy', 'Disease', 'Cancer_Tissue', 'Cancer_Type', 'Age', 'Sex']].copy()

    # Write final output
    neat_df.to_csv(output_filename, index=False)

    print(f"\nYou can check your result in: {output_filename}")



    