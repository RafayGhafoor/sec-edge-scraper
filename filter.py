import os
from flashtext import KeywordProcessor

os.chdir('old_data')

kp = KeywordProcessor()
keywords = ('table of contents', "credit agreement", "loan agreement", "credit facility", "loan and security agreement", "loan & security agreement", "revolving credit",
            "financing and security agreement", "financing & security agreement", "credit and guarantee agreement", "credit & guarantee agreement")

kp.add_keywords_from_list(list(keywords))
def is_valid(keywords):
    _keyword = 'table of contents'
    valid = _keyword in keywords
    return valid and keywords.index(_keyword) != 0


count = 0

for i in os.listdir('.'):
    should_delete = False
    with open(i, 'r') as f:

        lines = '\n'.join([i.lower() for i in f.readlines()[:50]])
        found_keywords = kp.extract_keywords(lines)
        result = is_valid(found_keywords)
        if not found_keywords:
            should_delete = True
    if should_delete:
        count+=1
        # os.remove(i)
        # os.remove(i)
print(count, len(list(os.listdir('.'))))