from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import pandas as pd
import time
import unidecode
import csv
import sys
import numpy as np

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 1, "profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.cookies": 1}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver


def scrape_interestingliterature():

    start = time.time()
    print('-'*75)
    print('Scraping interestingliterature.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # scraping books urls
    links = []
    driver.get("https://interestingliterature.com/list-of-best-poems-by-theme/")
    div = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@class='entry-content']")))
    tags = wait(div, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "p")))

    ncats = 0
    for tag in tags:
        try:
            a = wait(tag, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
            cat = a.get_attribute('textContent')
            link = a.get_attribute('href')
            links.append((link, cat))
            ncats += 1
            print(f'Scraping the url for category {ncats}')
        except:
            pass

    nbooks = 0
    for link in links:

        homepage = link[0]
        cat = link[1]
        #if cat == 'Boyfriend poems':
        #    debug = True
        #else:
        #    continue
        driver.get(homepage)
        # handling lazy loading
        while True:
            try:
                height1 = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script(f"window.scrollTo(0, {height1})")
                time.sleep(1)
                height2 = driver.execute_script("return document.body.scrollHeight")
                if int(height2) == int(height1):
                    break
            except Exception as err:
                continue

        # scraping books details
        print('-'*75)
        print(f'Scraping Poems Info For Category: {cat}')
        try:
            sections = wait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "p")))
        except:
            continue
        for sec in sections:
            try:
                strongs = wait(sec, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "strong")))
            except:
                continue
            if not strongs: continue

            # validating the strong tag
            content = strongs[0].get_attribute('textContent')
            if not content[0].isnumeric():
                try:
                    skip = False
                    children = wait(strongs[0], 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "*")))
                    for child in children:
                        if child.tag_name != 'a':
                            skip = True
                            break
                    if skip: continue
                except:
                    pass

            try:     
                details = {}
                title, title_link, author = '', '', ''
                try:
                    text = strongs[0].get_attribute('textContent').split('/>')[-1]
                    if '‘' not in text and '’' not in text and ',' not in text and not text[0].isnumeric(): 
                        continue
                    elems = text.split(',')
                    if len(elems) == 2:
                        name = elems[0]
                    elif len(elems) > 2:
                        name = ','.join(elems[:-1])

                    if name[1] == '.' or name[2] == '.':
                        author = '.'.join(name.split('.')[1:])
                    else:
                        author = name

                    if 'image' in author.lower(): continue
                    try:
                        if len(strongs) == 1:
                            a = wait(strongs[0], 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))[-1]
                        else:
                            a = wait(strongs[1], 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))[-1]
                        title = a.get_attribute('textContent')
                        title_link = a.get_attribute('href')    
                    except:
                        if len(strongs) == 1:
                            title = text.split(',')[1].replace('‘', '').replace('’', '').replace('.', '').strip()
                        else:
                            title = strongs[1].get_attribute('textContent').split(',')[1].replace('‘', '').replace('’', '').replace('.', '').strip()
                except:
                    pass

                if title == '' or author == '': continue
                if  title_link == '':
                    title_link = homepage
                nbooks += 1

                print(f'Scraping the info for poem {nbooks}')
                details['Title'] = title
                details['Title Link'] = title_link
                details['Author'] = author
                details['Category'] = cat
  
                # appending the output to the datafame            
                data = data.append([details.copy()])
                # saving data to csv file each 100 links
                if np.mod(nbooks, 100) == 0:
                    print('Outputting scraped data to Excel sheet ...')
                    data.to_excel('interestingliterature_data.xlsx', index=False)
            except:
                pass

    # optional output to Excel
    data.to_excel('interestingliterature_data.xlsx', index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'interestingliterature.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    data = scrape_interestingliterature()

