from flashtext import KeywordProcessor

import trio
import csv
import requests
from datetime import datetime
from asks import Session
import bs4

import os


keywords = ('table of contents', "credit agreement", "loan agreement", "credit facility", "loan and security agreement", "loan & security agreement", "revolving credit",
            "financing and security agreement", "financing & security agreement", "credit and guarantee agreement", "credit & guarantee agreement")
# today = datetime.date.today()
# margin = datetime.timedelta(days=3)
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
}
years = ('1996', '1997', '1998')
kp = KeywordProcessor()


def read_csv(filename='csvfile.csv'):
    data = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["DATE"].split('-')[0] in years:
                data.append((row['CIK'], row["DATE"]))
    return data


# https://sec.report/CIK/0000001750/38#documents
root_url = "https://sec.report"
url = "https://sec.report/CIK/0000001750/1#documents"


def get_total_pages(_cik):
    r = session.get(f"{root_url}/CIK/{_cik}/1#documents", headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"})
    soup = bs4.BeautifulSoup(r.content, 'lxml')
    pages = soup.findAll('a')
    links = []
    for i in pages:
        if i.get('href'):
            if i.get('href').endswith('#documents'):
                links.append(i.get('href'))
    return len(links)




def is_valid(keywords):
    _keyword = 'table of contents'
    valid = _keyword in keywords
    return valid and keywords.index(_keyword) != 0


def grab(_cik, _date):

    for page in range(get_total_pages(_cik), get_total_pages(_cik)-6, -1):
        r = session.get(f"{root_url}/CIK/{_cik}/{page}#documents", headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"})
        soup = bs4.BeautifulSoup(r.content, 'lxml')
        _date = _date.split()[0]
        target_date = datetime.strptime(_date, "%Y-%m-%d")
        table = soup.find('div', class_='panel panel-default',
                          attrs={'id': 'documents'}).find('table')

        for entry in table.findAll('tr')[1:][::-1]:
            form, info = entry.findAll('td')
            link = f"{root_url}{info.find('a').get('href')}"
            txt_file = link.split('/')[-2]
            headers["Referer"] = txt_file
            link = link + txt_file + '.txt'
            date = info.find('small').text
            date = date.split()[0].strip()
            print(str(target_date).split('-')[0], str(date).split('-')[0])
            target_year, target_month, target_day = str(target_date).split('-')
            current_year, current_month, current_day = str(date).split('-')
            
            if target_year != current_year and (target_month != current_month and f"{int(target_month)+1}" != current_month):
                print("Returning")
                continue
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            found_year, *extra_date = date.split('-')
            
            if form.text in ["10-K", "10-Q", "8-K", "10-K405"]:
                print(form.text, link, date)

            r.encode = 'utf-8'
            # print(str(r.content, 'utf-8', errors='replace'))
            text = session.get(link, headers=headers,
                               allow_redirects=True).text

            found_keywords = kp.extract_keywords(text)
            result = is_valid(found_keywords)
            filename = f'{_cik}_{date}'

            with open(f"old_data/{filename}.txt", 'w') as f:
                f.write(text)


def date_to_text(_date):
    obj = datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
    return obj.strftime("%B %d, %Y")


def main():
    for _cik, _date in read_csv():
        try:
            text_date = date_to_text(_date)
            kp.add_keywords_from_list(list(keywords))
            kp.add_keyword(text_date)
            grab(_cik, _date)
            kp.remove_keyword(_date)
            kp.remove_keyword(text_date)
        except Exception as e:
            print(e)


main()