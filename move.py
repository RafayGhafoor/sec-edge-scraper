import shutil
import os

ciks_list = []
with open('ciks_list.txt', 'r') as f:
    for i in f:
        ciks_list.append(i.strip())


for i in os.listdir('old_data/'):
    if i.split('_')[0] in ciks_list:
        shutil.copy(f"data/{i}", "small_data/")


