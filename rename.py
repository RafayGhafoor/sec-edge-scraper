import os

os.chdir('old_data')
for i in os.listdir('.'):
    a, b = i.split('_')
    b = b.replace('-', '')
    res = a + "_" + b
    os.rename(i, res)