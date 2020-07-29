import requests
import re
import csv
from threading import Thread
import gevent
from gevent import monkey


#待拼接的url  这里以猫眼top100为例
url0 = 'https://maoyan.com/board/4?offset='

#定义头文件，默认只要ua，不同情况可加上不同的头文件字段，部分反爬是需要处理请求头的
headers = {
    #cookie
    #referer
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.26 Safari/537.36'
    }

#若为post请求则加上data
#data={}

#Ps:若data里面的字段或拼接url有参数需要js解密则扣js进行解密处理


#针对不同的url构造，有些是直接根据page翻页，有些是根据page*offset进行翻页
page = 10   #总页数
offset = 20   #每页偏移量

#采用线程+协程进行高效率爬取，即总并发数为：线程数*协程数
thread_num = 10   #开启的线程数量
gevent_num = 10   #开启的协程数量

f = open ('result.csv','w',encoding='utf-8',newline='')
writer = csv.writer(f,delimiter=',')
list0 = ['电影','主演','上映时间','评分']   #写入第一行，根据不同需求修改即可


def write_csv(list1):
    writer.writerow(list1)


#提取想要字段，不同网页无论是ajax，还是直接翻页的等等，都可进行抓包获取其翻页返回的数据，用re、json等等提取都按个人所好
def get_info(i):
    try:
        name = re.findall('title="(.*?)"',i,re.S)[0].strip()   #电影名
        actor = re.findall('主演：(.*?)</p>',i,re.S)[0].strip()   #主演
        releasetime = re.findall('上映时间：(.*?)</p>',i,re.S)[0].strip()   #上映时间
        score = re.findall('<p class="score">(.*?)</p>',i,re.S)[0].strip()
        score = re.sub('<.*?>','',score)   #评分

        #简单4个字段，不同网页只不过是字段不同，最多加上里层再次请求，那就拼接或者匹配出url进行再次请求进行提取即可，统一放list1
        list1 = [name,actor,releasetime,score]

        return list1
    except:
        return []


#发起请求和提取字段写入csv
def do_it(index):
    try:
        if index >=page:   #一般不需这个操作，意为超出我们要的页数就跳出
            return
        url = url0+str(index)
        html = requests.get(url,headers=headers,timeout=5)
        text = html.text

        #每一页有多行内容，把每行所在节点用findall匹配
        moban1 = re.findall('<i class="board-index board-index(.*?)</dd>',text,re.S)   #不同网页的每行匹配规则不一样

        for i in moban1:
            list1 = get_info(i)
            print(list1)    #实时打印
            if list1 == []:
                continue
            write_csv(list1)  #写入csv
    except:
        pass


def run_gevent(num):
    jobs = []
    for i in range(num*gevent_num,(num+1)*gevent_num):
        jobs.append(gevent.spawn(do_it,i))
    gevent.joinall(jobs)


def run_thread(num):
    listt = []
    for i in range(num*thread_num,(num+1)*thread_num):
        t = Thread(target=run_gevent,args=(i,))
        t.start()
        listt.append(t)
    for t in listt:
        t.join()

for i in range(int(page/thread_num/gevent_num)+1):
    run_thread(i)

f.close()   #关闭csv
