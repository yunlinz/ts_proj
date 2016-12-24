import pandas as pd
import numpy as np
from dateutil.parser import parse
import csv
import xlrd
import sqlite3

TRANSACTION_COST = 0.0005


class Position(object):
    def __init__(self, security, amount, date_entered, enter_price, cost_to_borrow=0):
        self.security = security  # the security ticker
        self.amount = amount
        self.enter_price = enter_price
        self.date_entered = date_entered
        self.cost_to_borrow = cost_to_borrow  # annualized borrowing cost

    def exit_position(self, date_exit, exit_price):
        bdays = 5.0 / 7.0 * (date_exit - self.date_entered).days
        pct_return = (exit_price - self.enter_price) / self.enter_price - \
                     TRANSACTION_COST - (self.cost_to_borrow ** (bdays / 252)
                                         if self.amount < 0 else 0)
        return pct_return, self.amount * self.enter_price * pct_return


class PositionCache(object):
    def __init__(self):
        self.position_dict = {}
        self.position_list = []

    def add_position(self, pos):
        self.position_list.append(pos)
        self.position_dict[pos.security.ticker] = self.position_list[-1]

    def enter_position(self, security, amount, date, price, cost_to_borrow=0):
        pos = Position(security, amount, date, price, cost_to_borrow)
        self.position_list.append(pos)
        self.position_dict[security] = self.position_list[-1]

    def close_position(self, security, date, price):
        pos = self.position_dict[security]
        pct_ret, amt_ret = pos.exit_position(date, price)
        # del self.position_dict[security]
        return pct_ret, amt_ret

    def has_position(self, ticker):
        return ticker in self.position_dict


class Portfolio(object):
    def __init__(self):
        self.longs = PositionCache()
        self.shorts = PositionCache()

    def in_longs(self, ticker):
        return self.longs.has_position(ticker)

    def in_shorts(self, ticker):
        return self.shorts.has_position(ticker)


class Universe(object):
    def __init__(self):
        self.sec_dict = {}
        self.sec_list = []
        self.eligible_secs = set()
        self.events = {}
        self.price_db = None
        self.last_sync_date = None

    def __enter__(self):
        return Universe.__init__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.price_db is not None:
            self.price_db.close()

    def initialize_from_files(self, current_spx=None, events=None, quotes_dir='../data/'):
        print('Reading files')
        self._initialize_events(events)
        self._create_initial_eligible_list(current_spx)
        self._rollback_events()

        print('Opening DB connection')
        db = sqlite3.connect(quotes_dir + 'quotes_db.db'
                             , detect_types=sqlite3.PARSE_DECLTYPES)
        c = db.cursor()
        print('Querying DB')
        c.execute('SELECT MIN(Date), MAX(Date) FROM QUOTES')
        print('Done')
        first, last = c.fetchone()
        self.price_db = db

        return parse(first), parse(last)

    def _initialize_events(self, file=None):
        if file is None:
            pass
        with open(file) as events:  # assumes a 3 column csv with date,add,remove and date is in mm/dd/yyyy format
            csvreader = csv.reader(events)
            for line in csvreader:
                date, add, remove = line
                date = parse(date)
                if date not in self.events:
                    self.events[date] = []
                if add != '':
                    self.events[date].append(Event(add, Event.ADD))
                if remove != '':
                    self.events[date].append(Event(remove, Event.REMOVE))

    def _create_initial_eligible_list(self, current_spx=None):
        if current_spx is None:
            pass
        with open(current_spx) as eligibles:
            csvreader = csv.reader(eligibles)
            for line in csvreader:
                ticker, name, industry, subindustry = line
                self.eligible_secs.add(ticker)

    def _rollback_events(self):
        if len(self.eligible_secs) == 0:
            raise BrokenPipeError("No current eligible securities!")
        if len(self.events) == 0:
            pass
        dates = list(self.events.keys())
        dates.sort()
        for d in reversed(dates):
            for event in self.events[d]:
                if event.type == Event.ADD:
                    self.eligible_secs.remove(event.ticker)
                elif event.type == Event.REMOVE:
                    self.eligible_secs.add(event.ticker)
                else:
                    raise BrokenPipeError('Malformed event for {}'.format(event.ticker))

    def is_eligible(self, ticker):
        return ticker in self.eligible_secs

    def update_eligibility(self, ticker, type):
        if type == Event.ADD:
            self.eligible_secs.add(ticker)
        elif type == Event.REMOVE:
            self.eligible_secs.remove(ticker)

class Event(object):
    ADD = 0
    REMOVE = 1

    def __init__(self, ticker, type):
        self.ticker = ticker
        self.type = type
