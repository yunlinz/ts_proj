from src.BackTestObjects import *
import copy
import pandas as pd
import datetime


class BackTester(object):
    def __init__(self):
        self.portfolio = Portfolio()
        self.universe = Universe()
        self.signal_set = None
        self.fundamentals = None
        self.cur_date = None
        self.start_date = None
        self.end_date = None

    def __enter__(self):
        return BackTester()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.universe.price_db is not None:
            self.universe.price_db.close()

    def set_universe(self, current_spx, events, quotes
                     , fundamentals=None, signals_file=None):
        print('Caching signals file')
        if signals_file is not None:
            self.signal_set = pd.read_csv(signals_file, parse_dates=[0])
        print('Caching fundamentals file')
        if fundamentals is not None:
            self.fundamentals = pd.read_csv(fundamentals, parse_dates=[1])
        print('Initialize SPX membership')
        self.start_date, self.end_date = \
            self.universe.initialize_from_files(current_spx=current_spx
                                                 , events=events
                                                 , quotes_dir=quotes)
        self.cur_date = copy.deepcopy(self.start_date)

    def _increment_date(self):
        self.cur_date += datetime.timedelta(days=1)
        if self.cur_date in self.universe.events:
            for event in self.universe.events[self.cur_date]:
                ticker, kind = event.ticker, event.type
                self.universe.update_eligibility(ticker, kind)
                print('Event {}:{} processed'.format(ticker, 'ADD' if kind == 0 else 'REMOVE'))

    def step_day(self):
        if self.cur_date > self.end_date:
            return None
        query = 'SELECT * FROM QUOTES WHERE DATE = DATETIME(\'{}\')'\
            .format(self.cur_date.strftime('%Y-%m-%d'))
        quote_df = pd.read_sql(query
                         , self.universe.price_db)
        self._increment_date()
        while len(quote_df) == 0:
            quote_df, signal_df = self.step_day()
        print(self.cur_date)
        quote_df['Eligible'] = quote_df['Ticker'].apply(lambda x: x in self.universe.eligible_secs)
        signal_df = self.signal_set[self.signal_set['Date'] == self.cur_date]
        return quote_df, signal_df

    def step_week(self):
        if self.cur_date > self.end_date:
            return None
        query = 'SELECT * FROM QUOTES WHERE DATE = DATETIME(\'{}\')' \
            .format(self.cur_date.strftime('%Y-%m-%d'))

        quote_res = None
        signal_res = None
        self._increment_date()
        while self.cur_date.isocalendar()[2] != 6:
            if quote_res is None:
                quote_res = pd.read_sql(query, self.universe.price_db)
                signal_res = self.signal_set[self.signal_set['Date'] == self.cur_date]
            else:
                quote_res = quote_res.append(pd.read_sql(query, self.universe.price_db), ignore_index=True)
                signal_res = signal_res.append(self.signal_set[self.signal_set['Date'] == self.cur_date]
                                               , ignore_index=True)
            query = 'SELECT * FROM QUOTES WHERE DATE = DATETIME(\'{}\')' \
                .format(self.cur_date.strftime('%Y-%m-%d'))
            self._increment_date()
        quote_res['Eligible'] = quote_res['Ticker'].apply(lambda x: x in self.universe.eligible_secs)
        return quote_res, signal_res

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

    def get_eligible_list(self):
        return self.universe.eligible_secs

    def get_current_fundamentals(self, ticker, delay=0):
        df = self.fundamentals[(self.fundamentals['tic'] == ticker)
                               & (self.fundamentals['datadate'] <= self.cur_date - datetime.timedelta(days=delay))]
        most_recent = df['datadate'].max()
        return(df[df['datadate'] == most_recent])

    def set_cur_date(self, date):
        self.cur_date = date

    def more_days(self):
        return self.cur_date <= self.end_date

    def get_final_price(self, ticker):
        query = 'SELECT Date, Price FROM QUOTES WHERE TICKER = \'{}\' ORDER BY Date DESC LIMIT 1'.format(ticker)
        df = pd.read_sql(self.universe.price_db, query, parse_dates=[0])
        date = df['Date'].iloc[0]
        px = df['Price'].iloc[0]
        return px