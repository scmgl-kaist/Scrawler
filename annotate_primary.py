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

