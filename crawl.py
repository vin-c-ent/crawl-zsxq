import re
import requests
import json
import os
import pdfkit
from bs4 import BeautifulSoup
from urllib.parse import quote

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
<h1>{title}</h1>
<p>{text}</p>
</body>
</html>
"""
htmls = []
num = 0
def get_data(url):

    global htmls, num

    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
        'Accept':'application/json, text/plain, */*                                                   ',
        'Accept-Language':'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2                ',
        'Accept-Encoding':'gzip, deflate, br                                                          ',
        'X-Request-Id':'82907b544-1692-95f1-1d15-4ef72467968                                          ',
        'X-Version':'2.4.0                                                                            ',
        'X-Signature':'406055c21c85e1429b255dc91b98270fd045f7bf                                       ',
        'X-Timestamp':'1618231526                                                                     ',
        'Origin':'https://wx.zsxq.com                                                               ',
        'Connection':'keep-alive                                                                      ',
        'Referer':'https://wx.zsxq.com/                                                             ',
        'Cookie':'abtest_env=product; zsxq_access_token=FD8F0E69-4FCB-4130-EE20-0F80D5600E42_15ED2F52F49EA7B4',
        'TE':'Trailers                                                                                '
    }

    rsp = requests.get(url, headers=headers)
    with open('test.json', 'w', encoding='utf-8') as f:        # 将返回数据写入 test.json 方便查看
        f.write(json.dumps(rsp.json(), indent=2, ensure_ascii=False))

    with open('test.json', encoding='utf-8') as f:
        for topic in json.loads(f.read()).get('resp_data').get('topics'):
            content = topic.get('question', topic.get('talk', topic.get('task', topic.get('solution'))))
            # print(content)
            text = content.get('text', '')
            text = re.sub(r'<[^>]*>', '', text).strip()
            text = text.replace('\n', '<br>')
            title = str(num) + '. ' + text[:9]
            num += 1

            if content.get('images'):
                soup = BeautifulSoup(html_template, 'html.parser')
                for img in content.get('images'):
                    url = img.get('large').get('url')
                    img_tag = soup.new_tag('img', src=url)
                    soup.body.append(img_tag)
                    html_img = str(soup)
                    html = html_img.format(title=title, text=text)
            else:
                html = html_template.format(title=title, text=text)

            if topic.get('question'):
                answer = topic.get('answer').get('text', "")
                soup = BeautifulSoup(html, 'html.parser')
                answer_tag = soup.new_tag('p')
                answer_tag.string = answer
                soup.body.append(answer_tag)
                html_answer = str(soup)
                html = html_answer.format(title=title, text=text)

            htmls.append(html)

    next_page = rsp.json().get('resp_data').get('topics')
    if next_page:
        create_time = next_page[-1].get('create_time')
        if create_time[20:23] == "000":
            end_time = create_time[:20]+"999"+create_time[23:]
        else :
            res = int(create_time[20:23])-1
            end_time = create_time[:20]+str(res).zfill(3)+create_time[23:] # zfill 函数补足结果前面的零，始终为3位数
        end_time = quote(end_time)
        if len(end_time) == 33:
            end_time = end_time[:24] + '0' + end_time[24:]
        next_url = start_url + '&end_time=' + end_time
        print(next_url)
        get_data(next_url)

    return htmls

def make_pdf(htmls):
    html_files = []
    for index, html in enumerate(htmls):
        file = str(index) + ".html"
        html_files.append(file)
        with open(file, "w", encoding="utf-8") as f:
            f.write(html)

    options = {
        "user-style-sheet": "test.css",
        "page-size": "Letter",
        "margin-top": "0.75in",
        "margin-right": "0.75in",
        "margin-bottom": "0.75in",
        "margin-left": "0.75in",
        "encoding": "UTF-8",
        "custom-header": [("Accept-Encoding", "gzip")],
        "cookie": [
            ("cookie-name1", "cookie-value1"), ("cookie-name2", "cookie-value2")
        ],
        "outline-depth": 10,
    }
    try:
        pdfkit.from_file(html_files, "电子书.pdf", options=options)
    except Exception as e:
        pass

    for file in html_files:
        os.remove(file)

    print("已制作电子书在当前目录！")

if __name__ == '__main__':
    start_url = 'https://api.zsxq.com/v1.10/groups/28518484814451/topics?scope=all&count=20'
    make_pdf(get_data(start_url))
