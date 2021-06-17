import re
import roman


def get_section_number_roman(line):
    # line = 'ARTICLE V AFFIRMATIVE COVENANTS OF THE BORROWER..................................................................14'
    line = line.lower()
    if 'article' in line:
        line = line.replace('article', '')
    try:
        tokens = line.split()[:10]
        for line_tokens in tokens:
            try:
                line_tokens = line_tokens.replace('.', '')
                section_number = str(
                    roman.fromRoman(line_tokens.upper())) + '.'
                return section_number
            except Exception as e:
                continue
    except Exception as e:
        return -1
    return -1


def get_section_number(line):
    if not line:
        return -1
    section_number = re.findall('\d{1,2}\.?', line)
    roman_section_number = get_section_number_roman(line)
    if roman_section_number == -1:
        try:
            section_number = section_number[0].replace('.', '')
        except IndexError:
            return -1

    else:
        section_number = roman_section_number
    # if len(section_number) >= 2 and roman_section_number == -1:
    #     section_number = section_number[0]
    # else:
    #     # Fallback method
    #     section_number = roman_section_number
    if not section_number:
        return -1
    return section_number
