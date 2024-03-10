import pandas as pd
import numpy as np

import time
import re
import sys
import os
import glob
import subprocess

from tqdm import tqdm
from math import ceil, floor

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

def read_input(input_filename):
    # Read input and check format
    df = pd.read_csv(input_filename)
    try:
        df = df[['Series', 'Sample Name']].copy()
    except:
        print("Error! 'Series', 'Sample Name' columns should be in your dataframe")
        exit()
    series_list = df["Series"].to_list()
    print(f"Found {len(series_list)} samples in your file.")

    # Adding columns for later use
    df["PMID"] = None
    df["PMC"] = None

    return df, series_list


def get_pmid_list(series_list):
    # Selenium setting
    driver_path = '/usr/bin/chromedriver'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")

    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-proxy-server')

    s = Service(driver_path)
    driver = webdriver.Chrome(service=s, options=chrome_options)

    # Get ready
    base_url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={}"
    series_results = {}
    pmid_list = []

    # Scrape PMID for each GSE
    for i in tqdm(range(len(series_list))):
        
        item = series_list[i]
        
        if item not in series_results:  
            url = base_url.format(item)
            driver.get(url)
        
            t = 5
            driver.implicitly_wait(t)
            time.sleep(t)

            citations = driver.find_elements(By.XPATH, "//a[@title='Link to PubMed record']")
            if citations:
                citations = [citation.text for citation in citations]
                series_results[item] = citations  
            else:
                series_results[item] = ["None"]

        pmid_list.append(series_results[item])

    driver.quit()

    return pmid_list


if __name__ == "__main__":

    # Read and process input
    df, series_list = read_input(sys.argv[1])

    # Add PMID
    pmid_list = get_pmid_list(series_list)









