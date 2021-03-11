import re
import os
from fuzzywuzzy import process
import json
from difflib import SequenceMatcher

with open('results.json', 'r') as f:
    data = json.load(f)


def fetch(_file,  stream):
    matched_lines = {}
    found_data = ""
    for files in data:
        if files.get(_file):
            found_data = files.get(_file)
    for query in found_data:
        if not query:
            continue
        if '.....' in query:
            query = query.split('.....')[0]
        seq = ((e, SequenceMatcher(None, query,
                                    e).get_matching_blocks()[0]) for e in stream)
        seq = [k for k, _ in sorted(
            seq, key=lambda e:e[-1].size, reverse=True)][:3]
        if seq:
            start = stream.index(seq[0])
            for index in range(start, start+10):
                try:
                    if not matched_lines.get(query):
                        matched_lines[query] = ""
                    matched_lines[query] += ('\n' + (' '.join(stream[index].split()))).strip()
                except Exception as e:
                    break
    return matched_lines