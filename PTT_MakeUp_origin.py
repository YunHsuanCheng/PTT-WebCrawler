from sqlalchemy import create_engine, Table, Column, String, MetaData
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime 
url = "https://www.ptt.cc/bbs/MakeUp/index.html"

Search = input("搜尋關鍵字:")
page_max = input("輸入搜尋的頁數:")
page = 0
engine = create_engine("mysql://root:1528mysql@127.0.0.1:3306/ptt_makeup?charset=utf8", encoding="utf-8", echo=False)
metadata = MetaData(engine)
conn = engine.connect()

PTT_MakeUp = Table('PTT_MakeUp', metadata,
        Column('title', String(400), primary_key=True),
        Column('author', String(400)),
        Column('time', String(400)),
        Column('url', String(400)),
        Column('content', String(4000)),
        )

metadata.create_all()


while (page !=  int(page_max)) :
    # 換頁機制
    page = page + 1

    # 網頁請求 成功=200
    r = requests.get(url)

    # 請求的回應以text檔案解析
    soup = BeautifulSoup(r.text, "html.parser")

    # 要找的東西在網頁的位置
    btn = soup.select('div.btn-group-paging > a')
    
    # 在長方格中四個button區0123屬於1
    up_page_herf = btn[1]['href']

    # 把前面的https加上去
    url = 'https://www.ptt.cc' + up_page_herf

    # 要找出的結果在網頁的位置
    results = soup.select("div.title")

    # import json的list
    outcomelist = []

    # 抓標題+網址+作者+發文時間+內文
    for item in results:
        a_item = item.select_one("a")
    #    print(a_item)  ##<a href="/bbs/MakeUp/M.1582783590.A.F14.html">[妝容] 粉紅眼線x大地色</a>
        # 標題
        title = item.text
    #    print(title)  ##[妝容] 粉紅眼線x大地色
        # 內文網址

        # 　是否刪文判斷，有則跳過並繼續執行
        if a_item is None:
            continue
        else:
            sub_url = 'https://www.ptt.cc'+a_item.get('href')
            sub_r = requests.get(sub_url)
            sub_soup = BeautifulSoup(sub_r.text, "html.parser")

        # 判斷搜尋字是否包含
        if (title.find(Search) != -1):
            # 標題、內文中的作者、內文中的時間

            # 選擇內文的div
            sub_content = sub_soup.select("#main-content")

            # 標題、內文中的作者、內文中的時間
            #   print("標題:",sub_soup.select('div.article-metaline > span.article-meta-value')[1].text,"\n作者:", sub_soup.select('div.article-metaline > span.article-meta-value')[0].text,"\n發文時間:",sub_soup.select('div.article-metaline > span.article-meta-value')[2].text)

            in_title = sub_soup.select(
                'div.article-metaline > span.article-meta-value')[1].text
            in_author = sub_soup.select(
                'div.article-metaline > span.article-meta-value')[0].text
            in_time = sub_soup.select(
                'div.article-metaline > span.article-meta-value')[2].text
            ## Year
            Year = in_time[20:24]
            ## Month
            Month = in_time[4:7]
            ## Day
            Day = in_time[9]
            ## Hour
            Hour = in_time[11:13]
            ## Minute
            Minute = in_time[14:16]
            ## Second 
            Second = in_time[17:19]

            dateString = Year +"-"+Month+"-"+Day+" "+Hour+":"+Minute+":"+Second
            dateFormatter  = '%Y-%b-%d %H:%M:%S'
            in_time = datetime.strptime(dateString, dateFormatter)
            in_time = str(in_time)
            #print( "formate:",datetime.strptime(dateString, dateFormatter))



            #   print("標題:",in_title,"\n作者:",in_author,"\n發文時間:",in_time)

            # 　內文網址
            #   print("網址:",sub_url)

            # 過濾掉「看板」
            target = sub_content[0].findAll(
                "div", {"class": "article-metaline-right"})
            for child in target:
                child.decompose()

            # 過濾掉「作者」、「標題」、「時間」
            target = sub_content[0].findAll("div", {"class": "article-metaline"})
            for child in target:
                child.decompose()

            # 過濾掉「圖片」
            target = sub_content[0].findAll("div", {"class": "richcontent"})
            for child in target:
                child.decompose()

            # 過濾掉「發信站（綠色字）」、「文章網址（綠色字）」、「推文編輯」
            target = sub_content[0].findAll("span", {"class": "f2"})
            for child in target:
                child.decompose()

            # 過濾掉推文
            target = sub_content[0].findAll("div", {"class": "push"})
            # print("target:",target)
            for child in target:
                child.decompose()

            # 轉換成text
            sub_content_str = sub_content[0].text
            # print("old:",sub_content_str)
            sub_content_str = sub_content_str.replace("\n", "")

            # print("new:",sub_content_str)
            # 印出內文
            #   print(sub_content_str)




            # 加入dict
            appendDict = {
                'Title': in_title,
                'Author': in_author,
                'Time': in_time,
                'Content_url': sub_url,
                'Content': sub_content_str
            }


            Dictdata = [
                in_title,
                in_author,
                in_time,
                sub_url,
                sub_content_str
            ]
        
    
            # 每一筆結果加入list
            outcomelist.append(appendDict)


                    
    ##  write to json file  ##====================
            with open('Result.json', 'w', encoding='utf-8') as f:
                json.dump(outcomelist, f, ensure_ascii=False, indent=4)

    ##　write to mysql  ##====================
            

           
            
        
            insert = PTT_MakeUp.insert(None).values(
                title = Dictdata[0],
                author = Dictdata[1],
                time = Dictdata[2],
                url = Dictdata[3],
                content = Dictdata[4],
            )
            engine.execute(insert)
            
            print("插入成功!")
            #print("插入的內容:",insert)
conn.close()
    #print(outcomelist)
