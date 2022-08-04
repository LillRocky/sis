#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import sys, getopt
import time
from bs4 import BeautifulSoup
from enum import Enum, unique
from tqdm import tqdm

@unique
class Cata(Enum):
    RenQi = '279'
    LuanLun = '83'
    ChangPian = '334'
    WenXue = '322'
    YuanChuang = '383'
    DaBao = '500'
    JiuWen = '359'

base_url = 'https://sis001.com/forum/'

proxie = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'}

cookie = {
    'cdb2_cookietime': '315360000',
    'cdb2_smile': '1D1',
    'cdb2_auth': 'IemroLFVHaq%2FYAv3YothpxwI%2F9jbKbOvHLgY6v5YHbvSbfa08BSOYKX6vqbAC9Hm%2BoeUr%2BG7nIoj4Fyk',
    'cdb2_sid': 'hdVFSb',
    'cdb2_uvStat': '1658800113',
    'cdb2_readapmid': '400D435D331',
}

# cookie = 'cdb2_cookietime=2592000; cdb2_smile=1D1; cdb2_auth=Krv89rxVSKi%2FYAv3YothpxwI%2F9jbKbOvHLgY6v5YHbvSbfa08BSOYKX6vqbAC9Hm%2BoeUr7K7wY5%2F4l7x; cdb2_sid=hdVFSb; cdb2_uvStat=1658374728; cdb2_readapmid=400D435D331; cdb2_oldtopics=D11357358D11326935D;'

search_base_url = base_url + '/search.php'
fidList = [member.value for name, member in Cata.__members__.items()]
fids = '_'.join(fidList)

def get_cli():
    opts, args = getopt.getopt(sys.argv[1:], 'k:f:n:di', ['keyword', 'fids', 'name', 'desc', 'in'])
    keyword = ''
    sort = 'asc'
    name = ''
    f = fids
    out = True
    for op, value in opts:
        if op in ('-k', '--keyword'):
            keyword = value
        elif op in ('-f', '--fids'):
            f = value
        elif op in ('-n', '--name'):
            name = value
        elif op in ('-d', '--desc'):
            sort = 'desc'
        elif op in ('-i', '--in'):
            out = False
    return (keyword, sort, name, f, out)
    

def search(keyword, asc, name='', fid='all'):
    res = requests.get(search_base_url, headers=headers, cookies=cookie, proxies=proxie, params={
        'before': '',
        'srchfrom': 0,
        'special': '',
        'srchfilter': 'all',
        'srchtxt': keyword,
        'srchuname': name,
        'orderby': 'dateline',
        'ascdesc': asc,
        'searchsubmit': 'yes',
        'srchfid': fid,
        'page': 1
    })
    link_list = get_link_list(res)
    html = BeautifulSoup(res.text, 'lxml')
    pages = html.find('div', class_='pages')
    if not pages:
        print('仅一页')
    else:
        target = pages.find('a', class_='next')
        last = target.find_next('a', class_='last')
        if last: 
            last = last['href']
        else:
            last = target.find_previous_sibling('a')['href']
        (pre, middle, post) = last.rpartition('=')
        post = int(post)
        if (post <= 6):
            for i in range(2, post + 1):
                ress = requests.get(base_url + pre + middle + str(i), headers=headers, cookies=cookie, proxies=proxie)
                link_list = link_list + get_link_list(ress)
                time.sleep(1)
    return link_list

def get_link_list(res):
    html = BeautifulSoup(res.text, 'lxml')
    a_list = html.find('table', attrs={'summary': '搜索'}).select('th > a')
    link_list = list(map(lambda x: {'title': x.get_text(), 'url': base_url + x['href']}, a_list))
    return link_list

def down_content(link):
    res = requests.get(link, headers=headers, cookies=cookie, proxies=proxie)
    html = BeautifulSoup(res.text, 'lxml')
    content = html.find('div', class_='t_msgfont noSelect')
    list = content.find_all(['table', 'strong', 'i'])
    for tag in list:
        tag.clear()
    return content.get_text()

def get_choose_list(link_list, out):
    if out:
        s = '排除'
    else:
        s = '下载'
    choose = input('请输入要%s的编号，多选用单个空格分隔：' % s)
    if choose.strip() == '':
        print('未输入任何编号，程序退出')
        exit()
    elif choose.strip() == 'all':
        final_list = link_list
    else:
        choose_list = choose.strip().split(' ')
        choose_list = list(map(lambda x: int(x), choose_list))
        if out:
            final_list = [link_list[i] for i in range(len(link_list)) if i not in choose_list]
        else:
            final_list = [link_list[i] for i in range(len(link_list)) if i in choose_list]
    return final_list

def save_content(content, name):
        with open(name + '.txt', 'a', encoding="utf-8") as f:
            f.write(content + '\n')

if __name__ == '__main__':
    keyword, sort, name, fid, out = get_cli()
    link_list = search(keyword, sort, name, fid)
    for i in range(len(link_list)):
        print(i, link_list[i]['title'])
    final_list = get_choose_list(link_list, out)
    # content = down_content(link_list[0]['url'])
    # print(content.get_text())
    for link in tqdm(final_list):
        content = down_content(link['url'])
        save_content(content, keyword)
        time.sleep(10)
    print("finished")
