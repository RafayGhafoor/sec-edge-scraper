import json
import shutil
import os
with open('new_results.json', 'r') as f:
    data = json.load(f)

os.chdir('test')
for fn in os.listdir('.'):

    with open(fn, 'r') as f:
        if 'covenant' in f.read().lower():
            shutil.move(fn, '../covenants/')