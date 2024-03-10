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
from selenium.common.exceptions import TimeoutException


def read_input(input_filename):
    # Read input and check format
    df = pd.read_csv(input_filename)
    try:
        df = df[['Series', 'Sample Name']].copy()
    except:
        print("Error! 'Series', 'Sample Name' columns should be in your dataframe")
        exit()
    series_list = df["Series"].to_list()
    print(f"\nFound {len(series_list)} samples in your file.\n")

    # Sorting
    df = df.sort_values(["Series", 'Sample Name'])

    # Adding columns for later use
    df["PMID"] = None
    df["PMC"] = None

    return df, series_list


def get_pmid_list(series_list):
    # Selenium setting
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")

    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-proxy-server')

    # Get ready
    driver_path = '/usr/bin/chromedriver'
    s = Service(driver_path)
    driver = webdriver.Chrome(service=s, options=chrome_options)

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


def get_pmc_list(pmid_list):
    # Selenium setting
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")

    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-proxy-server')

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")

    # Get ready
    driver_path = '/usr/bin/chromedriver'
    s = Service(driver_path)
    driver = webdriver.Chrome(service=s, options=chrome_options)

    base_url = "https://pubmed.ncbi.nlm.nih.gov/{}"
    xpath = '//*[@id="full-view-identifiers"]/li[2]/span/a'

    pmid_results = {}
    pmc_list = []
    t = 5

    # Scrape PMC for each PMID
    for i in tqdm(range(len(pmid_list))):
            
        item = pmid_list[i]
        
        try:
            # If multiple PMIDs
            item_key = str(item) if isinstance(item, list) else item

            if item_key not in pmid_results:
                url = base_url.format(item_key)
                driver.get(url)
                time.sleep(t)
                element = driver.find_element(By.XPATH, xpath)
                            
                if element:
                    pmid_results[item_key] = element.text
                else:
                    pmid_results[item_key] = "None"
        
        except:
            print('exception for', item)
            pmid_results[str(item)] = "None"  # List type of item

        pmc_list.append(pmid_results[str(item)])

    driver.quit()

    return pmc_list


def get_methods(pmc_list):
    # Selenium setting
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")

    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-proxy-server')

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
    
    # Get ready
    driver_path = '/usr/bin/chromedriver'
    s = Service(driver_path)
    driver = webdriver.Chrome(service=s, options=chrome_options)

    base_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/{}/"
    method_text = []
    pmc_results = {}
    crawlcount = 0
    t = 5

    # Scrape Methods for each PMCs
    for i in tqdm(range(len(pmc_list))):
        
        item = pmc_list[i]
        
        if item not in pmc_results:
            
            div_content = None

            try:
                url = base_url.format(item)    
                driver.get(url)
                time.sleep(t)
                page_html = driver.page_source

                soup = BeautifulSoup(page_html, 'html.parser')            
                h2_with_text = soup.find('h2', string=lambda text: text and 'method' in text.lower())
                
                if h2_with_text:
                    parent_div = h2_with_text.find_parent('div')
                    if parent_div and parent_div.has_attr('id'):
                        div_content = soup.find('div', {'id': parent_div['id']})

                if div_content:
                    
                    for tag in div_content.find_all():
                        tag.append(" ")

                    extracted_text = ' '.join(div_content.get_text().split())
                    pmc_results[item] = extracted_text
                else:
                    pmc_results[item] = "None"      
                    
            except:
                print(f"An error occurred")
                pmc_results[item] = "None"  
            
        # If it's already scraped
        method_text.append(pmc_results[item])

    driver.quit()

    return method_text


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: python get_methods.py [input_file] [output_file]")
        exit()

    # Read and process input
    df, series_list = read_input(sys.argv[1])

    # Add PMID
    pmid_list = get_pmid_list(series_list)
    pmid_list = [item[0] if len(item) == 1 else item for item in pmid_list]
    print(f"\nPMIDs for {len(pmid_list)} samples scraped.\n")
    df['PMID'] = pmid_list

    # Add PMC
    pmc_list = get_pmc_list(pmid_list)
    print(f"\nPMCs for {len(set(pmc_list))} samples scraped.\n")
    df['PMC'] = pmc_list

    # Add Methods
    df['Method'] = get_methods(pmc_list)
    print(f"\nMethods for {len(set(pmc_list))} samplesscraped.\n")

    # Generate output file
    df.to_csv(sys.argv[2], index=False)
    print(f"\nYou can check your result in: {sys.argv[2]}\n")








