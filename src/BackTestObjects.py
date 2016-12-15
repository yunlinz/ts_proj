import pandas as pd
import numpy as np


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
    def __init__(self, security, amount, date_entered, short_interest):
        self.security = security  # the security object
        self.amount = amount
        self.date_entered = date_entered
        self.short_interest = short_interest # annualized short interest

    def exit_position(self, date_exit):
        period_returns, bdays = self.security.get_return(self.date_entered, date_exit)
        return period_returns - 0.0015 - (self.short_interest ** (bdays / 252) if self.amount < 0 else 0)


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