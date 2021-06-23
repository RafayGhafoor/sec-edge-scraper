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

os.makedirs('new_data', exist_ok=True)

# keywords to be searched in the first 60 lines of loan contract, if found, mark it as a loan contract.
keywords = ("CREDIT AGREEMENT", "LOAN AGREEMENT", "CREDIT FACILITY", "LOAN AND SECURITY AGREEMENT", "LOAN & SECURITY AGREEMENT", "REVOLVING CREDIT",
            "FINANCING AND SECURITY AGREEMENT", "FINANCING & SECURITY AGREEMENT", "CREDIT AND GUARANTEE AGREEMENT", "CREDIT & GUARANTEE AGREEMENT")

# keywords to be searched for minimizing the search context.
tally_keywords = ' OR '.join(
    [f'"{i}"' for i in keywords if i != 'table of contents'])


session = requests.Session()

kp = KeywordProcessor()
# adding keywords to keyword processor for searching in the document text.
kp.add_keywords_from_list(list(keywords))


def add_months(sourcedate, months):
    # Add months to provided date and returns new date.
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
    '''Converts date of YEAR-MONTH-DAY HOUR:MINUTE:SECOND to text format.'''
    obj = datetime.strptime(_date, '%m/%d/%Y')
    return obj.strftime("%B %d, %Y")


def date_to_fn(_date):
    '''Converts date to filename format.'''
    obj = datetime.strptime(_date, '%m/%d/%Y')
    return obj.strftime("%m%d%Y")


def custom_date_generator(_date):
    '''Given a start date, adds one year to it and formats it according to sec.gov requirement.'''
    obj = datetime.strptime(_date, '%m/%d/%Y')
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
                try:
                    ciks = int(entity["_source"]["ciks"][0])
                    file_cik = entity["_source"]["ciks"][0]
                    file_date = entity["_source"]["file_date"]
                    sequence = entity["_source"]["sequence"][0]
                    _id = entity["_id"]
                    before, after = _id.split(':')
                    before = before.replace("-", "")
                    before = before.replace(":", "/")
                    _id = before+'/'+after
                    url = f"https://www.sec.gov/Archives/edgar/data/{ciks}/{_id}"
                    extracted_urls.append((f"{file_cik}_{file_date}_{sequence}",url))
                except Exception as e:
                    print(e)
                    continue
        except Exception as e:
            print(e)

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
        print(e)
    return extracted_urls


# def is_valid(keywords):
#     _keyword = 'table of contents'
#     valid = _keyword in keywords
#     return valid and keywords.index(_keyword) != 0


async def grabber(s, url, _cik, fn):
    '''Retrieve text of the documents and searches the keywords in the document. 
    If keyword is found, search in the next 60 lines of the keyword, the term "TABLE OF CONTENTS"
    and if the term found, download the contract otherwise ignore the contract.
    '''
    try:
        global count
        resp = await s.get(url)
        text = resp.text
        lines = '\n'.join(text.split('\n'))
        found_keywords = kp.extract_keywords(lines)
        index_found  = -1
        
        for keyword in found_keywords:
            index_found = text.find(keyword)
            break
        
        valid_contract = False

        if index_found != -1:
            next_text = text[index_found:]
            tokens_by_newline = next_text.split('\n')
            followed_lines_scanned = '\n'.join(tokens_by_newline)
            if 'TABLE OF CONTENTS' in followed_lines_scanned:
                valid_contract = True
        
        if not valid_contract:
            return

        # result = is_valid(found_keywords)
        filename = fn
        # if found_keywords:
            # print(filename)
        
        file_path = os.path.join('new_data', filename+'.txt')
        print(file_path)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                f.write(text)
            count += 1
        progress_writer.write(f"{filename},{url}\n")
    except Exception as e:
        print(e)
        print("Some problem occurred")


async def main():
    s = Session(connections=20)
    input_data = read_csv()
    # input_data = [("0000002135", "03/20/2006")]

    try:
        with alive_bar(len(input_data), title="Total Progress") as total_bar:
            for _cik, _date in input_data:
                try:
                    start_date, end_date = custom_date_generator(_date)
                    # Since, new sec-edge website doesn't support contracts past the year 2000,
                    # the ciks which have the year before 2000 are ignored as they are to be
                    # searched in the old directory of contracts.
                    if end_date.split('-')[0] in ('1999','1998','1997','1996'):
                        total_bar()
                        continue

                    extracted_urls = await make_search(s, _cik, start_date, end_date)
                    # or i.endswith('htm') and 'exv' not in i
                    extracted_urls = [(filename, url) for filename, url in extracted_urls if url.endswith('txt')]
                    text_date = date_to_text(_date)
                    # kp.add_keyword(text_date)
                    _urls_length = len(extracted_urls)
                    if not _urls_length:
                        print(extracted_urls)
                        continue
                    async with trio.open_nursery() as n:
                        for filename, url in extracted_urls:
                            print(filename, url)
                            n.start_soon(grabber, s, url, _cik, filename)
                    # kp.remove_keyword(_date)
                except Exception as e:
                    raise
                finally:
                    total_bar()
    except Exception as e:
        print(e)
    finally:
        progress_writer.close()
trio.run(main)
