from src.BackTestObjects import *
import copy
import pandas as pd
import datetime

class BackTester(object):
    def __init__(self):
        self.portfolio = Portfolio()
        self.universe = Universe()
        self.cur_date = None
        self.start_date = None
        self.end_date = None

    def __enter__(self):
        return BackTester()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.universe.price_db is not None:
            self.universe.price_db.close()

    def set_universe(self, current_spx=None, events=None, quotes=None):
        self.start_date, self.end_date = \
            self.universe.initialize_from_files(current_spx=current_spx
                                                 , events=events
                                                 , quotes_dir=quotes)
        self.cur_date = copy.deepcopy(self.start_date)

    def _increment_date(self):
        self.cur_date += datetime.timedelta(days=1)
        if self.cur_date in self.universe.events:
            for event in self.universe.events[self.cur_date]:
                ticker, type = event.ticker, event.type
                self.universe.update_eligibility(ticker, type)
                print('Event {}:{} processed'.format(ticker, 'ADD' if type == 0 else 'REMOVE'))

    def step_day(self):
        if self.cur_date > self.end_date:
            return None
        query = 'SELECT * FROM QUOTES WHERE DATE = DATETIME(\'{}\')'\
            .format(self.cur_date.strftime('%Y-%m-%d'))
        df = pd.read_sql(query
                         , self.universe.price_db)
        self._increment_date()
        while len(df) == 0:
            df = self.step_day()
        return df

    def reset_portfolio(self):
        self.portfolio = Portfolio()
        self.cur_date = copy.deepcopy(self.start_date)

    def enter_position(self, ticker, price, amount):
        if not self.universe.is_eligible(ticker):
            print('Security {} is not eligible to right now!'.format(ticker))
            return False
        if amount < 0:
            self.portfolio.shorts.enter_position(ticker, amount, self.cur_date, price)
        else:
            self.portfolio.longs.enter_position(ticker, amount, self.cur_date, price)
        print('Security {} added successfully!'.format(ticker))
        return True


    def exit_position(self, ticker, price):
        pct_ret, amt_ret = None, None
        if self.portfolio.in_longs(ticker):
            pct_ret, amt_ret = \
                self.portfolio.longs.close_position(ticker, self.cur_date, price)
        if self.portfolio.in_shorts(ticker):
            pct_ret, amt_ret = \
                self.portfolio.shorts.close_position(ticker, self.cur_date, price)
        return pct_ret, amt_ret