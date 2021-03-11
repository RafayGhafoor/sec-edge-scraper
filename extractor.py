import roman
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import csv
import matcher
import datefinder
import bs4
import re
import json
TOTAL = 0


class ParseAgreement:
    def __init__(self, content):
        self.content = content.split("\n")[:300]

    def get_section_number_roman(self, line):
        # line = 'ARTICLE V AFFIRMATIVE COVENANTS OF THE BORROWER..................................................................14'
        line = line.lower()
        if 'article' in line:
            line = line.replace('article', '')
        try:
            tokens = line.split()
            for line_tokens in tokens:
                try:
                    section_number = str(
                        roman.fromRoman(line_tokens.upper())) + '.'
                    return section_number
                except Exception as e:
                    continue
        except Exception as e:
            print(e)
            return -1
        return -1

    def get_section_number(self, line):
        section_number = re.findall('\d{1,2}\.?', line)
        roman_section_number = self.get_section_number_roman(line)
        if len(section_number) >= 2 and roman_section_number == -1:
            section_number = section_number[0]
        else:
            # Fallback method
            section_number = roman_section_number
        return section_number

    def get_covenant_categories(self, filename):
        headings_mapping = {}
        collected_data = {}

        for index, i in enumerate(self.content):
            if 'covenant' in i.lower() and sum(c.isdigit() for c in i):
                headings_mapping[i] = []

                section_number = float(
                    self.get_section_number(i))
                # print(section_number, i)
                for line in range(index+1, index + 100):
                    try:
                        # print("%r", self.content[line])
                        if not self.content[line].strip():
                            continue

                        section_number_now = float(self.get_section_number(
                            self.content[line]))
                        if section_number != -1 and section_number_now != -1:
                            # print(section_number_now, section_number, self.content[line])
                            if section_number_now > section_number:
                                break
                        # print(section_number, section_number_now,
                        #       self.content[line])
                        if section_number == section_number_now or 'section' in self.content[line].lower() and "article" not in self.content[line].lower():
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
                pass

            finally:
                found_values = []
                key = ' '.join(key.split())
                if key not in cache:
                    found_values.append(key)
                    print(key)
                cache.add(key)

                for i in v:
                    val = ' '.join(i.split())
                    if val not in cache:
                        found_values.append(val)
                        print(val)
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
        return ['','']

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
    json_data = []
    count = 1
    cwd_files = os.listdir('.')
    total_files = len(cwd_files)
    for num, _file in enumerate(cwd_files, 1):
        print(f"Processing {_file}: [{num}/{len(cwd_files)}]")
        if not _file.endswith('.txt'):
            continue
        # if not i.endswith('0001084408_09272001.txt'):
        #     continue

        cik, date = _file.replace('.txt', '').strip().split('_')
        cik = str(int(cik))
        month, date, year = date[0:2], date[2:4], date[4:]
        formatted_date = f"{month}/{date}/{year}"

        with open(_file, 'r') as f:
            try:
                # agreement_parser = ParseAgreement(f.read())
                # filename, values = agreement_parser.get_covenant_categories(
                #     i)
                # json_data.append({filename: values})
                cik, date = _file.replace('.txt', '').strip().split('_')
                month, date, year = [date[i:i+3]
                                     for i in range(0, len(date), 3)]
                formatted_date = f"{month}/{date}/{year}"
                string_stream = f.read()
                stream = string_stream.split('\n')
                fetched_data = matcher.fetch(_file, stream)
                agreement_phrase, info = get_agreement_info(stream)
                is_renegotiated = "1" if agreement_phrase else "0"
                if is_renegotiated:
                    agreement_phrase = ' '.join(agreement_phrase.split())
                else:
                    agreement_phrase = ""
                    info = ""
                if not fetched_data:
                    fetched_data = {"": ""}
                for covenant_name, lines in fetched_data.items():
                    csv_data = [str(count), cik, formatted_date, _file.replace(
                        '.txt', ''), is_renegotiated, agreement_phrase, info, covenant_name, lines]
                    with open("../desc.csv", 'a') as f:
                        writer = csv.writer(f)
                        writer.writerow(csv_data)
            except Exception as e:
                # raise
                continue
        count += 1

        # with open("../results.json", 'a') as z:
        #     json.dump(json_data, z)

        # print(i)
        # input()
    # print(TOTAL)

main()

# a = ParseAgreement("SECTION VI DEFAULT..........................................................................59")
# print(a.get_section_number(a.content[0]))
