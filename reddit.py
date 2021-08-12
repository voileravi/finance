from selenium import webdriver
from collections import Counter
import numpy as np
from datetime import datetime, date, timedelta
from dateutil.parser import parse 
import requests
import csv
import pandas as pd
#import pygsheets

def grab_html():
#    url = 'https://www.reddit.com/r/wallstreetbets/search/?q=flair%3A%22Daily%20Discussion%22&restrict_sr=1&sort=new'
    url = 'https://www.reddit.com/r/wallstreetbets/search?q=flair_name%3A%22Daily%20Discussion%22&restrict_sr=1&sort=new'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("headless")
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    driver = webdriver.Chrome(executable_path=r'/home/voileravi/chromedriver', options=chrome_options)
    driver.get(url)
    return driver

def grab_link(driver):
    yesterday = datetime.today() - timedelta(days=1)
    
    links = driver.find_elements_by_xpath('//*[@class="_eYtD2XCVieq6emjKBH3m"]')

    for a in links:
        if a.text.startswith('Daily Discussion Thread'):
            pos = a.text.index('2021')
            tex = a.text[:pos+4]
 #           date = "".join(a.text.split(' ')[pos-2:pos+1])
            date = "".join(tex.split(' ')[-3:])
            parsed = parse(date) 
            if parse(str(yesterday.date())) == parsed:
                link = a.find_element_by_xpath('../..').get_attribute('href')
        if a.text.startswith('Weekend'):
            weekend_date = a.text.split(' ')
            parsed_date = weekend_date[-3] + ' ' + weekend_date[-2] + weekend_date[-1] 
            parsed = parse(parsed_date) 
            saturday = weekend_date[-3] + ' ' +  str(int(weekend_date[-2].replace(',','')) - 1) + ' ' + weekend_date[-1] 
         
            if parse(str(yesterday.date())) == parsed: 
                link = a.find_element_by_xpath('../..').get_attribute('href')
            elif parse(str(yesterday.date())) == parse(str(saturday)):
                link = a.find_element_by_xpath('../..').get_attribute('href') 

    stock_link = link.split('/')[-3]

    return stock_link

def grab_commentid_list(stock_link):
    html = requests.get(f'https://api.pushshift.io/reddit/submission/comment_ids/{stock_link}')
    raw_comment_list = html.json()
    driver.close() 
    return raw_comment_list

def grab_stocklist():
    """
    r = requests.get('https://finnhub.io/api/v1/stock/symbol?exchange=US&token=')
    stocks = r.json()
    stocks_list = []
    for a in stocks:
        stocks_list.append(' ' + a['symbol'] + ' ')
    """
    stocks_list = []
    with open('stockslist.txt', 'r') as w:
        stocks = w.readlines()
        for a in stocks:
            a = a.replace('\n','')
            stocks_list.append(' ' + a + ' ')
    return stocks_list

def get_comments(comment_list):
    html = requests.get(f'https://api.pushshift.io/reddit/comment/search?ids={comment_list}&fields=body&size=1000')
 
    newcomments = html.json()
    return newcomments

def get_stock_list(newcomments,stocks_list):
    stock_dict = Counter()
    for a in newcomments['data']:
        for ticker in stocks_list:
            if ticker in a['body']:
                stock_dict[ticker]+=1
    return stock_dict

def grab_stock_count(stock_dict,raw_comment_list):
    orig_list = np.array(raw_comment_list['data'])
    comment_list = ",".join(orig_list[0:2000])
    remove_me = slice(0,2000)
    cleaned = np.delete(comment_list, remove_me)
    i = 0
    while i < len(cleaned):
        print(len(cleaned))
        cleaned = np.delete(cleaned, remove_me)
        new_comments_list = ",".join(cleaned[0:2000])
        newcomments = get_comments(new_comments_list)
        get_stock_list(newcomments,stock_dict)
    stock = dict(stock_dict) 
    return stock

if __name__ == "__main__":
    driver = grab_html()
    stock_link = grab_link(driver)
    raw_comment_list = grab_commentid_list(stock_link) 
    stockslist = grab_stocklist()
    orig_list = np.array(raw_comment_list['data'])
    comment_list = ",".join(orig_list[0:1000])
    new_comments = get_comments(comment_list)
    stock_dict = get_stock_list(new_comments,stockslist)
    stock = grab_stock_count(stock_dict, raw_comment_list)

    data = list(sorted(stock.items(), key=lambda x: x[1], reverse=True))
#    data = list(zip((stock.keys()),sorted(stock.values())))
    with open('stock.csv','w') as w:
        writer = csv.writer(w, lineterminator='\n')
        writer.writerow(['Stock','Number of Mentions'])
        for a in data:
            writer.writerow(a)
'''
    df = pd.DataFrame.from_dict(data)
    gc = pygsheets.authorize(client_secret='client_secret_1.json')
    key = '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCRMp0q8KDZpFRK\nz7NP0jZwFHYZshFF1jxeEkP0W/MrBxy+D1LNmMylAwAIiKLhyMCxOS2sqLMxjOWv\nGaG2XpkG7yYWyA1TjM2EXNukgyvMXDO+RHJPPvDCQ00Qa9bmwubGKm/bGurzA+7I\n+veUW0DLAUaPMbGqTSCTMoDYBYDzKlJs6AUo1vD5+KN8cQnwv72ozMbxP4e7FW8u\nb2Fhtytv0Z3chLq2q/9w7PMdxOoIjxgOJpewpxXoEnzsAw0XTcErdsAAiQU7SkOv\ng+K7/bpvj7ulyAbPBqnCRVVG911Hmrq6r2R9bxIERtp6tGZnAnyVOMBezJmx00Mf\nSFXtjOftAgMBAAECggEAAWN5Rs+ZzjMI3lVJqvYA8MX1Ui4WhbM0jRbCIRxfATaW\ncwfc/BvduydB8RLzcdLUau13zxqm6g6lpKzLU93oOz1+wQGFRRsH3R/xNsvNV607\nDnMDn9fjgAwaONG7MqZDBDqkKrWBcTUEq9Xgl8HepwJaXSS1xQHrUZUOT+KPluO5\nSVZb9Qer8MgkDtD6NJGfwZeYCvh54g0BdxRlv0wGxZpyincCcWE87Hf5I23iVXlx\nO//wK0D6hgUYrHwrTYg9tQLCnv0PgHs7LBY/ajA7+v3WxuofHd76A7OjkqZ9LidH\n2jfPyQ3pHMfK4+X8HyVWf2Hm6VtHigVdiUaJ09opEQKBgQDE5yz26XgiULnfSBuj\nik0qSbxMDTekIzK93azD5mYLYDmO1oT4fTt3VF6yLLjMWa6x7heclczBi5iUk6Hk\n/8H6KRs9Y5Q83ExNXoqn45nDG/m1VQFLwIdO1lyXB3xQYhmGgNdLR/Vuxm3ULF6Q\ntUBJknfKYN8+yJCyYE9qHzli3QKBgQC8xrfFE7cLvo3EHqvHmArmMx1KkH5msmDm\nLPlrQ6ewmfiZhqRnfXnNXNPaDOpPkpSLhcu4jNqf7R91IJZXsm9k4HgMXZI/HNQ8\npSX0g8d1WFtnUo28//WMRZrR8J+TBCelxwA6WTy1pW4kwpeWiNPOcMWJv1r3VFCI\nHGBSER0gUQKBgEiaSR0eBxr4EyE+cFqD82IFYDXWpc6S3/HcXAi72qKVL4P4m30Y\niCW+6U/fZ6CJ7P1UokYtghtXgsI+EXLjzz2TjKS9I/qw7D2W/59aL+ceWJvBJUIu\nUnYCWo+hxffJxEmxFjF+7gOTjQmv9op7GqJGLH9l6ss2nwv2sTGbI8jNAoGAWmfo\nto88iHlXt2bg6ZOdFKXCD2Wnw1MGKPW89WvPMTpr3kqnDZD/9iPQqYqp5DXUwgTv\njZCXWyPafuN+XL1tr6f4liNx2Jvb4LdOuA0sRrxr+c2FZ9BFLkpfXM+Z/HRu8Guf\nZlI6StvRJfWzVzpsBV/ompFz5SMR9j1wu5zKkCECgYEAj0WEPKPZvQnOsMuFX3cw\nUwwHsq5EdHP3pXl07HDLDMSaQ7SOot23M5Tj62T9fSaSchvXKl1kZkLdYsh8HuWu\nopGqXWz3d1/88IzNJOeWWB2Ci1GsgIZUclbtuCLzuzo5DCfVm1LF2cWWTx19XUWC\n20Vwt8dcPxjs3c8N7e4PBdM=\n-----END PRIVATE KEY-----\n'
    sheet = gc.open_by_key(key)
    worksheet = sheet.add_worksheet("Stock list")
    worksheet.set_dataframe(df,'A1')  
'''
