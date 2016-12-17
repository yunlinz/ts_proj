import pandas as pd
import numpy as np
from dateutil.parser import parse
import csv
import xlrd



class Security(object):
    def __init__(self):
        self.price_series = None  # Pandas data series of returns
        self.pe_ratio_series = None  # Pandas data series of P/E ratio
        self.mcap_series = None  # Pandas data series market cap
        self.sector = None  # string describing the sector
        self.ticker = None

    def get_return(self, enter_date, exit_date):
        price_series = self.price_series[enter_date:exit_date]
        return (price_series[-1] - price_series[0])/price_series[0], len(price_series)


class Position(object):
    def __init__(self, security, amount, date_entered, cost_to_borrow):
        self.security = security  # the security object
        self.amount = amount
        self.date_entered = date_entered
        self.cost_to_borrow = cost_to_borrow # annualized short interest

    def exit_position(self, date_exit):
        period_returns, bdays = self.security.get_return(self.date_entered, date_exit)
        return period_returns - 0.0015 - (self.cost_to_borrow ** (bdays / 252) if self.amount < 0 else 0)


class PositionCache(object):
    def __init__(self):
        self.position_dict = {}
        self.position_list = []

    def add_position(self, pos):
        self.position_list.append(pos)
        self.position_dict[pos.security.ticker] = self.position_list[-1]

    def close_position(self, security, date):
        pos = self.position_dict[security.ticker]
        period_returns = pos.exit_position(date)
        del self.position_dict[security.ticker]
        return period_returns

    def has_position(self, security):
        return security in self.position_dict


class Portfolio(object):
    def __init__(self):
        self.longs = PositionCache()
        self.shorts = PositionCache()

    def in_longs(self, security):
        return self.longs.has_position(security)

    def in_shorts(self, security):
        return self.shorts.has_position(security)


class Universe(object):
    def __init__(self):
        self.sec_dict = {}
        self.sec_list = []
        self.eligible_secs = set()
        self.events = {}
        self.last_sync_date = None

    def initialize_from_files(self, current_spx=None, events=None):
        self._initialize_events(events)
        self._create_initial_eligible_list(current_spx)
        self._rollback_events()
        raise NotImplementedError
        return 1,2

    def _initialize_events(self, file=None):
        if file is None:
            pass
        with open(file) as events: # assumes a 3 column csv with date,add,remove and date is in mm/dd/yyyy format
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


class Event(object):
    ADD = 0
    REMOVE = 1
    MERGER = 2
    def __init__(self, ticker, type):
        self.ticker = ticker
        self.type = type

