from flashtext import KeywordProcessor
import math
import requests
import bs4
from datetime import datetime, date
import json
import csv
import calendar
from asks.sessions import Session
import os
import trio
from alive_progress import alive_bar
progress_writer = open('progress.txt', 'a')
count = 0
os.makedirs('data', exist_ok=True)

keywords = ('table of contents', "credit agreement", "loan agreement", "credit facility", "loan and security agreement", "loan & security agreement", "revolving credit",
            "financing and security agreement", "financing & security agreement", "credit and guarantee agreement", "credit & guarantee agreement")
tally_keywords = ' OR '.join(
    [f'"{i}"' for i in keywords if i != 'table of contents'])
session = requests.Session()
kp = KeywordProcessor()


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def read_csv(filename='csvfile.csv'):
    data = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append((row['CIK'], row["DATE"]))
    return data


async def fetch(s, url, parameter=""):
    """
    Retrieve content from a url.
    """
    HEADERS = {
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
        "Referer": "https://www.sec.gov/edgar/search/?r=el",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
    resp = await s.post(url, data=json.dumps(parameter), headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()


async def _make_request(s, params):
    return await fetch(
        s,
        url="https://efts.sec.gov/LATEST/search-index",
        parameter=params,
    )


def date_to_text(_date):
    obj = datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
    return obj.strftime("%B %d, %Y")


def date_to_fn(_date):
    obj = datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
    return obj.strftime("%m%d%Y")


def custom_date_generator(_date):
    '''Given a start date, adds one year to it and formats it according to sec.gov requirement.'''
    obj = datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
    return obj.strftime("%Y-%m-%d"), add_months(obj, 18).strftime("%Y-%m-%d")


async def make_search(s, _cik, start_date, end_date):
    extracted_urls = []
    keywords = tally_keywords

    params = {"q": keywords, "dateRange": "custom", "ciks": [
        _cik],
        "startdt": start_date, "enddt": end_date,
        "forms": ["10-K", "10-Q", "8-K", "10-K405"]}

    # r = session.post(URL, data=json.dumps(params))
    resp = await _make_request(s, params)

    async def _write_resp(resp):
        try:
            for entity in resp["hits"]["hits"]:
                ciks = entity["_source"]["ciks"][0]
                _id = entity["_id"]
                before, after = _id.split(':')
                before = before.replace("-", "")
                before = before.replace(":", "/")
                _id = before+'/'+after
                url = f"https://www.sec.gov/Archives/edgar/data/{ciks}/{_id}"
                extracted_urls.append(url)
        except Exception as e:
            pass

    try:
        items_per_page = 100
        total_pages = math.ceil(
            int(resp["hits"]["total"]["value"]) / items_per_page)

        for i in range(1, total_pages + 1):
            try:
                if i == 1:
                    await _write_resp(resp)
                else:
                    params["page"] = str(i)
                    params["from"] = str(i * 100 - 100)
                    resp = await _make_request(s, params)
                    await _write_resp(resp)
            except Exception as e:
                continue
    except Exception as e:
        pass
    return extracted_urls


def is_valid(keywords):
    _keyword = 'table of contents'
    valid = _keyword in keywords
    return valid and keywords.index(_keyword) != 0


async def grabber(s, url, _cik, _date):
    try:
        global count
        resp = await s.get(url)
        text = resp.text
        found_keywords = kp.extract_keywords(text)
        result = is_valid(found_keywords)
        filename = f'{_cik}_{_date}'
        if result:
            print(filename)
            file_path = os.path.join('data', filename+'.txt')
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write(text)
                count += 1
        progress_writer.write(f"{filename},{url}\n")
    except Exception as e:
        print("Some problem occurred")


async def main():
    s = Session(connections=50)
    input_data = read_csv()
    with alive_bar(len(input_data), title="Total Progress") as total_bar:
        for _cik, _date in input_data:
            start_date, end_date = custom_date_generator(_date)
            extracted_urls = await make_search(s, _cik, start_date, end_date)
            extracted_urls = [i for i in extracted_urls if i.endswith('txt')]
            text_date = date_to_text(_date)
            kp.add_keywords_from_list(list(keywords))
            kp.add_keyword(text_date)
            _urls_length = len(extracted_urls)
            if not _urls_length:
                continue
            async with trio.open_nursery() as n:
                for url in extracted_urls:
                    n.start_soon(grabber, s, url, _cik, date_to_fn(_date))
            kp.remove_keyword(_date)
            total_bar()
            break
    progress_writer.close()
trio.run(main)
