import json
import os
import re
from urllib.parse import urlencode
import codecs
from hashlib import md5
import pymongo
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
import requests
from  multiprocessing import Pool
from selenium import webdriver
import time
from config import *
from json.decoder import JSONDecodeError
client = pymongo.MongoClient(MONGO_URL, connect=False) # connect 是為了多線程
db = client[MONGO_DB]

def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('儲存成功',result)
        return True
    return False

def jsget_one_page(url):
    try:
        browser = webdriver.Chrome()
        browser.get(url)
        # browser.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        time.sleep(1)
        #browser.execute_script('window.scrollTo(0,1600)')
        #time.sleep(2)
        html = browser.page_source
        return html
    finally:
        browser.close()

def get_page_insex(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'cur_tab': 3,
        'from': 'gallery'
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return  response.text
        return None
    except RequestException:
        print('請求失敗')
        return None

def parse_page_index(html):
    try:
        data = json.loads(html)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                yield item.get('article_url')
    except JSONDecodeError:
        pass

def get_page_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return  response.text
        return None
    except RequestException:
        print('請求失敗',url)
        return None

def parse_page_detail(html,url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('title')[0].get_text()
    print(title)
    images_pattern = re.compile('parse.*?"(.*?)]}', re.S)
    result = re.search(images_pattern, html)
    result = result.group(1) + ']}'
    result = codecs.escape_decode(result)
    # result.decode('unicode_escape')
    #print(result[0].decode("utf-8"))
    if result:
        data = json.loads(result[0].decode("utf-8"))
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images:
                # print(image)
                download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }

    # result = re.sub('\\\\','', result)
    # print(result)

def download_image(url):
    print('正在下載', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except RequestException:
        print('請求圖片失敗', url)
        return None

def save_image(content):
    file_path = '{0}\{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html = get_page_insex(offset, KEYWORD)
    print(html)
    for url in parse_page_index(html):
        # url='https://www.toutiao.com/a6601289695366218254/'
        # html = get_page_detail(url)
        html = jsget_one_page(url)
        if html:
            # result = parse_page_detail(html,url)
            # print(result)
            result = parse_page_detail(html, url)
            # print(result)
            save_to_mongo(result)
        break

if __name__ == '__main__':

    # 單線程
    # main()
    # 多線程
    groups = [x*20 for x in range(GROUP_START, GROUP_END+1)]
    pool = Pool()
    pool.map(main, groups)
    print('OK了')