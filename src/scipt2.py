import os

with open('../data/quotes-full.csv') as q:
    header = q.readline()
    cur_lines = 1
    cur_file = 0

    file = open('../data/quotes-full-{}.csv'.format(cur_file),'w')
    file.write(header)
    for line in q.readlines():
        file.write(line)
        cur_lines += 1
        if cur_lines >= 300000:
            cur_file += 1
            file.close()
            file = open('../data/quotes-full-{}.csv'.format(cur_file),'w')
            file.write(header)
            cur_lines = 1
    file.close()