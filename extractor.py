import roman
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

    def get_section_number_roman(self, line):
        # line = 'ARTICLE V AFFIRMATIVE COVENANTS OF THE BORROWER..................................................................14'
        line = line.lower()
        if 'article' in line:
            line = line.replace('article', '')
        try:
            tokens = line.split()
            for line_tokens in tokens:
                try:
                    section_number = str(roman.fromRoman(line_tokens.upper())) + '.'
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
                key = ' '.join(key.split())
                if key not in cache:
                    print(key)
                cache.add(key)
                
                for i in v:
                    val = ' '.join(i.split())
                    if val not in cache:
                        print(val)
                    cache.add(val)
                
                # print('-'*23+'\n\n')

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
    # os.chdir('resources')
    os.chdir('data')

    for i in os.listdir('.'):
        if not i.endswith('.txt'):
            continue
        # if not i.endswith('0000813856_07022002.txt'):
        #     continue
        # if not i.endswith('0001084408_09272001.txt'):
        #     continue
        with open(i, 'r') as f:
            try:
                agreement_parser = ParseAgreement(f.read())
                agreement_parser.get_covenant_categories(i)
                # get_existing_agreement_date(f.read())
            except Exception as e:
                # print(i)
                continue
        # print(i)
        # input()
    # print(TOTAL)


main()

# a = ParseAgreement("SECTION VI DEFAULT..........................................................................59")
# print(a.get_section_number(a.content[0]))