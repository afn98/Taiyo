from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from wordcloud import WordCloud
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from datetime import *
import datetime as dt
import matplotlib.pyplot as plt
import requests
import string
import numpy as np
import pandas as pd
import re

stop_words=set(stopwords.words("english"))
punctuations=list(string.punctuation)

def publishes_month(l):
    df['Published Month'] = [re.search('\d+\s(\w+)\s\d+', date).group(1) for date in l]
    df['Published Year'] = [re.search('\d+\s\w+\s(\d+)', date).group(1) for date in l]
    for year, months in df.groupby('Published Year'):
        fig = plt.figure(figsize=(12,6))
        active_month = months['Published Month'].value_counts()
        active_month.plot.bar()
        plt.xlabel('Month',fontdict={'fontsize': 14,'fontweight': 10})
        plt.ylabel('No. of tenders',fontdict={'fontsize': 14,'fontweight': 10})
        plt.title('Analysis of month with most publishes in year '+str(year)+'.',fontdict={'fontsize': 20,
            'fontweight': 8})
        plt.show()
        fig.savefig('Publishes per month in year '+str(year)+'.png')

def contract_type(l):
    fig = plt.figure(figsize=(15,5))
    df.groupby(l).size().plot(kind='pie')
    fig.savefig('Contract types.png')


def cleaned_industries(i):
    cleaned = re.sub('(http\S+)|\'|(\n)|[0-9]+',' ',i)
    tokens = word_tokenize(cleaned)
    filtered_tokens = []
    for w in tokens:
        if w not in stop_words:
            if w not in punctuations:
                filtered_tokens.append(w)
    return filtered_tokens

def text_analysis(l):
    my_tokens = cleaned_industries((" ".join(l)).lower())
    text = " ".join(my_tokens)
    word_cloud = WordCloud(collocations = False, background_color = 'white').generate(text)
    fig= plt.figure(figsize=(15,5))
    title= "Word Cloud"
    plt.title(title)
    plt.imshow(word_cloud)
    plt.axis("off")
    plt.show()
    file = 'Word_Cloud_for_Industries.png'
    fig.savefig(file)

path = r'C:\chromedriver.exe'
browser = webdriver.Chrome(executable_path=path)
browser.get('https://www.gov.uk/contracts-finder')

browser.maximize_window()
browser.find_element(By.XPATH, "//a[contains(@class, 'gem-c-button')]").click()
browser.find_element(By.XPATH, "//button[@id='adv_search']").click()
pages = int(browser.find_element(By.CSS_SELECTOR, "li[class=standard-paginate] a").text)
tenders_list = []

for i in range(1, pages):
    for t, j in enumerate(browser.find_elements(By.CSS_SELECTOR, "div.search-result")):
        tender = {}
        scraping = j.find_element(By.CSS_SELECTOR, "div h2 a").get_attribute('href')
        r = requests.get(scraping)
        sleep(2)
        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            tender['Tender Name'] = soup.find('h1').text
        except:
            continue
        url = []
        try:
            url.append(i.a['href'] for i in soup.find_all('dd'))
            tender['URLs'] = ', '.join(list(set(url)))
        except:
            if len(url)==0:
                tender['URLs'] = np.nan
        tender['Department'] = soup.find('h2', {'class': 'breadcrumb-description'}).text
        tender['Description'] = soup.find(lambda tag: tag.name=='h3' and 'Description' in tag.text).next_sibling.next_sibling.next_sibling.next_sibling.text
        tender['Notice Status'] = 'Opportunity' if soup.find(lambda tag: tag.name=='p' and 'opportunity' in tag.text) else 'Early Engagement'
        try:
            tender['Last Edited'] = soup.find(lambda tag: tag.name=='p' and 'Last edited' in tag.text).text.replace('Last edited date: ','')
        except:
            tender['Last Edited'] = np.nan
        tender['Industry'] = '. '.join(soup.find('div', {'class':'content-block'}).ul.text.strip('\n').split('\n'))
        for k in soup.find_all('h4'):
            col = k.text
            deet = k.next_sibling.next_sibling.text.strip('\n')
            if col == 'Industry':
                continue
            if col == 'Email':
                deet = deet.split()[0]
            if col == 'Address':
                addr_text = str(k.next_sibling.next_sibling)
                deet = ', '.join(re.sub('<p>|</p>','', addr_text).split('<br/>'))
            tender[col] = deet
        tenders_list.append(tender)
    print('Scraped Page: ' +str(i))
    browser.find_element(By.XPATH, "//a[contains(text(),'Next')]").click()
    sleep(1)

df = pd.DataFrame(tenders_list)

publishes_month(df['Published date'])
contract_type(df['Contract type'])
text_analysis(df['Industry'])

df.to_csv('Tenders.csv')


