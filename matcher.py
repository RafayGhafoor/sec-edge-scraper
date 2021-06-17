import json

with open('new_results.json', 'r') as f:
    data = json.load(f)


def fetch(_file, stream, original_stream):
    matched_lines = {}
    found_data = ""
    for files in data:
        if files.get(_file):
            found_data = files.get(_file)
    for data_index, query in enumerate(found_data):
        if not query:
            continue
        if '.....' in query:
            query = query.split('.....')[0]
        query = query.upper()[:45].strip()
        try:
            result = [line for line in stream if line.startswith(query)][1]
        except IndexError:
            continue

        start = stream.index(result)
        for index in range(start, start+30):
            try:
                if not matched_lines.get(query):
                    matched_lines[query] = ""

                # if data_index + 1 < len(found_data):
                #     if found_data[index+1].lower()[:45] in original_stream[index].lower():
                #         print("BREAKS")
                #         matched_lines[query] += "\n" + \
                #             matched_lines[query].strip()
                #         break
                matched_lines[query] += '\n' + original_stream[index]

            except Exception as e:
                print(e)
                # print("Breaking")
                break
        matched_lines[query] = " ".join(matched_lines[query][:80].split())
    return matched_lines


def test():

    _file = '0000909281_05162005.txt'
    with open('data/' + _file, 'r') as f:
        string_stream = f.read()
        split_stream = string_stream.split('\n')
        stream = [' '.join(i.split()).strip()
                  for i in string_stream.upper().split('\n')]
        fetched_data = fetch(_file, stream, split_stream)
        print(fetched_data["SECTION 5.6. BOOKS AND RECORDS"])


if "__main__" == __name__:
    new_data = []
    for i in data:
        _len = len(list(i.values())[0])
        if _len < 7 and [j for j in list(i.values())[0] if 'affirmative' in j.lower()]:
            new_data.append(i)
    with open('work.json', 'w') as f:
        json.dump(new_data, f)
    # test()
