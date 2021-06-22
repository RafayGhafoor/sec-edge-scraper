with open('ciks_list.txt', 'r') as f:
    for i in f:
        i = i.strip()
        cik, date = i.split(',') 
        day, month, year = date.split('/')
        print(f"{cik}_{year}{month.zfill(2)}{day}.txt")