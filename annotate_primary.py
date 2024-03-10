import pandas as pd
import numpy as np
import sys

def read_input(input_filename):
    print("")

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python annotate_by_GPT.py [input_file] [output_file]")
        exit()

    # Read and process input
    df, series_list = read_input(sys.argv[1])

    # Generate output file
    df.to_csv(sys.argv[2], index=False)
    print(f"\nYou can check your result in: {sys.argv[2]}\n")


