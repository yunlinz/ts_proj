import csv, sqlite3
from dateutil.parser import parse

# set up script. Run this once to create the database file for fast access
def create_quotes_table():
    db = sqlite3.connect('../data/quotes_db_new.sqlite', detect_types=sqlite3.PARSE_DECLTYPES)
    c = db.cursor()
    c.execute('CREATE TABLE QUOTES (gvkey INTEGER, iid INTEGER, Date DATETIME, Ticker TEXT, Cusip TEXT, Name TEXT, '
              'Shares FLOAT, EPS  FLOAT, Close  FLOAT, High  FLOAT, Low  FLOAT, Open  FLOAT, Status INTEGER,'
              'trfd FLOAT, cik INTEGER , ggroup  INTEGER, gind INTEGER, gsector INTEGER, gsubind INTEGER, spcindcd INTEGER, spcseccd INTEGER)')
    c.execute('CREATE INDEX date_index ON QUOTES (Date)')
    c.execute('CREATE INDEX ticker_index ON QUOTES (Ticker)')
    import os
    quote_dir = '../data/'
    quote_files = [file  for file in os.listdir(quote_dir) if 'quotes-new-' in file]
    quote_files.sort()
    for file in quote_files:
        with open(quote_dir + file) as fs:
            dr = csv.DictReader(fs)
            to_db = [(row['gvkey'], row['iid'], parse(row['datadate']), row['tic'], row['cusip'], row['conm'],
                      row['cshoc'], row['eps'], row['prccd'], row['prchd'], row['prcld'], row['prcod'], row['prcstd'],
                      row['trfd'], row['cik'], row['ggroup'], row['gind'], row['gsector'], row['gsubind'],
                      row['spcindcd'], row['spcseccd']) for row in dr]
            c.executemany('INSERT INTO QUOTES VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', to_db)
            db.commit()
    db.close()

if __name__ == '__main__':
    create_quotes_table()