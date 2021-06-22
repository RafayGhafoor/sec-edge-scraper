import roman
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import csv
import matcher
import datefinder
import utils
import bs4
import re
import json
from flashtext import KeywordProcessor

TOTAL = 0

keywords = ("credit agreement", "loan agreement", "credit facility", "loan and security agreement", "loan & security agreement", "revolving credit",
            "financing and security agreement", "financing & security agreement", "credit and guarantee agreement", "credit & guarantee agreement")

kp = KeywordProcessor()
kp.add_keywords_from_list(list(keywords))

class ParseAgreement:
    def __init__(self, content):
        self.content = content.split("\n")
        self.number_of_lines = 1000
        self.table_of_content = [
            i for i in self.content if 'table of content' in i.lower()]
        if self.table_of_content:
            self.table_of_content_start_index = self.content.index(
                self.table_of_content[0])
            self.start_index = self.table_of_content_start_index
            self.content = self.content[self.start_index:
                                        self.start_index+self.number_of_lines]
            # print(self.content)
        else:
            self.content = self.content[:self.number_of_lines]

    def get_covenant_categories(self, filename):
        headings_mapping = {}
        collected_data = {}

        for index, i in enumerate(self.content):
            if 'covenant' in i.lower() and sum(c.isdigit() for c in i) and len([c for c in i if c.isdigit()]) <= 3 or 'Affirmative Covenants'.lower() in i.lower() or 'Negative Covenants'.lower() in i.lower():
                headings_mapping[i] = []
                section_number = float(
                    utils.get_section_number(i))
                for line in range(index+1, index + 100):
                    try:
                        if '----' in self.content[line]:
                            continue
                        # print("%r", self.content[line])
                        if not self.content[line].strip():
                            continue

                        section_number_now = float(utils.get_section_number(
                            self.content[line]))
                        if section_number != -1 and section_number_now != -1:
                            # print(section_number_now, section_number, self.content[line])
                            if section_number_now > section_number:
                                break
                        # print(section_number, section_number_now,
                        #       self.content[line])
                        if section_number == section_number_now or 'section' in self.content[line].lower() and "article" not in self.content[line].lower():
                            if not self.content[line][-1].isdigit() and self.content[line+1][-1].isdigit():
                                headings_mapping[i].append(
                                    self.content[line] + "\n" + self.content[line+1])
                            if self.content[line][-1].isdigit():
                                headings_mapping[i].append(self.content[line])
                        if "article" in self.content[line].lower():
                            break
                    except IndexError:
                        break

        if headings_mapping:
            print("Running on file: ", filename)

        cache = set()

        values_collection = []
        for k, v in headings_mapping.items():
            # if k.startswith(' '): continue
            key = ' '.join(k.strip().split()).strip()
            try:
                section_key = [i for i in key.split() if i[0].isdigit()
                               ][0].replace('.', '')
                if len(section_key) > 2:
                    continue
            except Exception as e:
                print(e)
            finally:
                found_values = []
                key = ' '.join(key.split()).strip()
                if key not in cache and '\n' not in key and len(key) > 8 and key[-1].isdigit():
                    found_values.append(key)
                cache.add(key)

                for i in v:
                    val = ' '.join(i.split())
                    if val not in cache and '\n' not in val and len(val) > 8 and val[-1].isdigit():
                        found_values.append(val)
                    cache.add(val)
                values_collection.extend(list(found_values))
        return filename, values_collection

        # print('-'*23+'\n\n')

        # print(filename)


def get_contract_date(content):
    pass


def is_renegotiated(content):
    pass


def get_agreement_info(data):
    global TOTAL
    result = ""
    contents = data[100:]  # skip first 100 lines
    header = ' '.join(data[:100]).lower()
    agreement_phrase = [line for line in data[:100]
                        if 'amended' in line.lower() or 'restated' in line.lower()]
    should_run = 'amended' in header or 'restated' in header
    if not agreement_phrase:
        return ['', '']

    data = []  # Line Number, data

    for line_no, content in enumerate(contents):
        if re.findall('.*dated as of.*', content):
            data.append((line_no, content))

    statement = ""

    try:
        line_no, content = data[1]

        threshold = 5

        # Add previous lines
        for i in range(line_no-threshold, line_no):
            statement += contents[i].strip()
            statement += '\n'

        for i in range(line_no, line_no+threshold):
            statement += contents[i].strip()
            statement += '\n'
            # if ';' in statement or '.' in statement:
            #     break

        if 'existing' in statement.lower():
            filtered_statement = statement[statement.lower().find(
                'whereas'):].strip()
            if not filtered_statement:
                result += statement + '\n'
            else:
                result += filtered_statement + '\n'
            TOTAL += 1
    except Exception as e:
        print(e)
        pass

    returned_elements = ['', result]
    if agreement_phrase:
        returned_elements[0] = ' '.join(agreement_phrase[:2])
    return tuple(returned_elements)


def parse_file(content):
    soup = bs4.BeautifulSoup(content, 'lxml')
    return soup


def main():
    # os.chdir('resources')
    os.chdir('data')
    # os.chdir('covenants')
    json_data = []
    count = 1
    cwd_files = os.listdir('.')
    total_files = len(cwd_files)
    for num, _file in enumerate(cwd_files, 1):
        print(f"Processing {_file}: [{num}/{len(cwd_files)}]")
        if not _file.endswith('.txt'):
            continue

        cik, date = _file.replace('.txt', '').strip().split('_')
        cik = str(int(cik))
        month, date, year = date[0:2], date[2:4], date[4:]
        formatted_date = f"{month}/{date}/{year}"

        # if _file != '0001163302_12152005.txt': continue
        with open(_file, 'r') as f:
            try:

                file_content = f.read()
                first_sixty = first_five = "\n".join(file_content.split('\n')[:60])
                first_five = "\n".join(file_content.split('\n')[:300])
                found_keywords = kp.extract_keywords(first_sixty.lower())
                if not found_keywords:
                    continue
                if 'covenant' not in first_five:
                    continue

                # agreement_parser = ParseAgreement(file_content)
                # filename, values = agreement_parser.get_covenant_categories(
                #     _file)
                # if values:
                #     json_data.append({filename: values})

                agreement_phrase = " "
                info = " "
                string_stream = file_content
                split_stream = string_stream.split('\n')
                stream = [' '.join(i.split()).strip()
                          for i in string_stream.upper().split('\n')]
                fetched_data = matcher.fetch(_file, stream, split_stream)
                agreement_phrase, info = get_agreement_info(split_stream)
                is_renegotiated = "1" if agreement_phrase else "0"
                if is_renegotiated:
                    agreement_phrase = ' '.join(agreement_phrase.split())
                if not fetched_data:
                    fetched_data = {"": ""}
                section_number = ""
                section_number_now = ""
                running_covenant = ""
                current_num = -1
                for covenant_name, lines in fetched_data.items():
                    section_number = float(
                        utils.get_section_number(covenant_name))
                    section_number_now = float(utils.get_section_number(
                        covenant_name))
                    if 'affirmative covenant' in covenant_name.lower() or 'negative covenant' in covenant_name.lower() and section_number_now == section_number_now:
                        running_covenant = covenant_name
                        current_num = section_number_now

                    if section_number_now != section_number and 'affirmative covenant' not in covenant_name.lower() and 'negative covenant' not in covenant_name.lower():
                        running_covenant = ""

                    filter_covenant_name = ' '.join(
                        covenant_name.replace("SECTION", '').strip().split()[1:])
                    csv_data = [str(count), cik, formatted_date, _file.replace(
                        '.txt', ''), is_renegotiated, agreement_phrase, info, running_covenant, covenant_name, filter_covenant_name, lines]
                    with open("../desc.csv", 'a') as f:
                        writer = csv.writer(f)
                        writer.writerow(csv_data)

            except Exception as e:
                print(e)
                continue
        count += 1

    if not os.path.exists("../new_results.json"):
        with open("../new_results.json", 'a') as z:
            json.dump(json_data, z)

        # print(i)
        # input()
    # print(TOTAL)


main()

# a = ParseAgreement("SECTION VI DEFAULT..........................................................................59")
# print(a.get_section_number(a.content[0]))
