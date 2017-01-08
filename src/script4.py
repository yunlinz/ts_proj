import csv, sqlite3
from dateutil.parser import parse

# set up script. Run this once to create the database file for fast access
def create_quotes_table():
    db = sqlite3.connect('../data/quotes_db_full.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
    c = db.cursor()
    c.execute('CREATE TABLE QUOTES (PERMNO INTEGER, Date DATETIME, TICKER TEXT, Name TEXT, CUSIP TEXT, Low FLOAT, '
              'High FLOAT, Price FLOAT, Return FLOAT, Bid FLOAT, Ask FLOAT, Shares FLOAT, PriceFactor FLOAT, '
              'ShareFactor FLOAT, Open FLOAT, Return2 FLOAT )')
    c.execute('CREATE INDEX date_index ON QUOTES (Date)')
    c.execute('CREATE INDEX ticker_index ON QUOTES (TICKER)')
    import os
    quote_dir = '../data/'
    quote_files = [file  for file in os.listdir(quote_dir) if 'quotes-full-' in file]
    quote_files.sort()
    for file in quote_files:
        with open(quote_dir + file) as fs:
            dr = csv.DictReader(fs)
            to_db = [(row['PERMNO'], parse(row['date']), row['TICKER'], row['COMNAM'], row['CUSIP'], row['BIDLO'],
                      row['ASKHI'], row['PRC'], row['RET'], row['BID'], row['ASK'], row['SHROUT'], row['CFACPR'],
                      row['CFACSHR'], row['OPENPRC'], row['RETX']) for row in dr]
            c.executemany('INSERT INTO QUOTES VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', to_db)
            db.commit()
    db.close()

if __name__ == '__main__':
    create_quotes_table()