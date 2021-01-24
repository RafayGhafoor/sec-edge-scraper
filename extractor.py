from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
import datefinder
import bs4
import re

TOTAL = 0


class ParseAgreement:
    def __init__(self, content):
        self.content = content.split("\n")[:300]

    def get_covenant_categories(self, filename):
        headings_mapping = {}
        # if not filename.startswith('0000002969_09161999'):
        #     return
        for index, i in enumerate(self.content):
            if 'covenant' in i.lower() and sum(c.isdigit() for c in i):
                headings_mapping[i] = []
                section_number = re.findall('\d\.?\d', i)
                if len(section_number) == 2:
                    section_number = section_number[0]
                else:
                    section_number = -1
                for line in range(index+1, index + 100):
                    try:
                        section_number_now = re.findall(
                            '\d\.?\d', self.content[line])[0]

                        if section_number != -1:
                            if section_number_now > section_number:
                                break
                        if section_number == section_number_now or 'SECTION' in self.content[line]:
                            headings_mapping[i].append(self.content[line])
                        if "article" in self.content[line].lower():
                            break
                    except IndexError:
                        break
        for k, v in headings_mapping.items():
            print("KEY: ", k.strip())
            for i in v:
                print(i.strip())
                #     input()

        # print(filename)


def get_contract_date(content):
    pass


def is_renegotiated(content):
    pass


def get_existing_agreement_date(content):
    global TOTAL
    data = content.split('\n')
    contents = data[100:]
    header = ' '.join(data[:100]).lower()
    should_run = 'amended' in header or 'restated' in header
    if not should_run:
        return

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
            with open('data.txt', 'a') as f:
                filtered_statement = statement[statement.lower().find(
                    'whereas'):].strip()
                if not filtered_statement:
                    f.write(statement + '\n')
                else:
                    f.write(filtered_statement + '\n')
                f.write('-----------------------\n')
            TOTAL += 1
    except:
        pass


def parse_file(content):
    soup = bs4.BeautifulSoup(content, 'lxml')
    return soup


def main():
    os.chdir('resources')
    for i in os.listdir('.'):
        if not i.endswith('.txt'):
            continue
        with open(i, 'r') as f:
            try:
                agreement_parser = ParseAgreement(f.read())
                agreement_parser.get_covenant_categories(i)
                # get_existing_agreement_date(f.read())
            except Exception as e:
                print(e)
                # print(i)
                continue
        print(i)
        # input()
    # print(TOTAL)


main()
# os.chdir('data')
# for i in os.listdir('.'):
#     with open(i, 'r') as f:


#     for w in all_pages:
#         print(w)
