import csv, sqlite3
from dateutil.parser import parse

# set up script. Run this once to create the database file for fast access
def create_quotes_table():
    db = sqlite3.connect('../data/quotes_db.db', detect_types=sqlite3.PARSE_DECLTYPES)
    c = db.cursor()
    c.execute('CREATE TABLE QUOTES (PERMNO INTEGER, Date DATETIME, Ticker TEXT, Name TEXT, SecStat TEXT, Low FLOAT, Hight FLOAT, Price FLOAT, Volume FLOAT, Bid FLOAT, Ask FLOAT, Shares FLOAT, Open FLOAT)')
    c.execute('CREATE INDEX date_index ON QUOTES (Date)')
    import os
    quote_dir = '../data/'
    quote_files = [file  for file in os.listdir(quote_dir) if 'quotes-' in file]
    quote_files.sort()
    for file in quote_files:
        with open(quote_dir + file) as fs:
            dr = csv.DictReader(fs)
            to_db = [(row['PERMNO'], parse(row['date']), row['TICKER']
                       , row['COMNAM'], row['SECSTAT'], row['BIDLO']
                       , row['ASKHI'], row['PRC'], row['VOL'], row['BID']
                       , row['ASK'], row['SHROUT'], row['OPENPRC']) for row in dr]
            c.executemany('INSERT INTO QUOTES VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', to_db)
            db.commit()
    db.close()

if __name__ == '__main__':
    create_quotes_table()