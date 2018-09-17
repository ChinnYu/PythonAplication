import requests
from selenium import webdriver
from requests.exceptions import RequestException
import time
import re
import json
from multiprocessing import Pool
def get_one_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None

def parse_one_page(html):
    pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?board-img.*?src="(.*?)".*?>.*?name"><a.*?>(.*?)</a>.*?star">(.*?)</p>'+
                         '.*?releasetime">(.*?)</p>.*?integer">(.*?)</i>.*?fraction">(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'index': item[0],
            'image': item[1],
            'title': item[2],
            'actor': item[3].strip()[3:],
            'time': item[4].strip()[5:],
            'score': item[5]+item[6]
        }

def write_to_file(content):
    with open('result.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False)+'\n')
        f.close()


def main(offset):
    url = 'https://maoyan.com/board/4?offset=' + str(offset)

    # html = get_one_page(url)
    html = jsget_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)

def jsget_one_page(url):
    try:
        browser = webdriver.Chrome()
        browser.get(url)
        browser.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        time.sleep(1)
        browser.execute_script('window.scrollTo(0,1600)')
        time.sleep(2)
        html = browser.page_source
        return html
    finally:
        browser.close()

if __name__ == '__main__':
    # for i in range(10): #單線程
    #     main(i*10)
    pool = Pool() #多線程
    pool.map(main,[i*10 for i in range(10)])