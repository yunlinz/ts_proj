"""
Strategy class is the entry point into this program. You have to implemented a method that returns a list of tuples
that returns the weight of each position and the list of ticker positions to enter into
"""

from src.BackTester import BackTester
from datetime import datetime
import random
import matplotlib.pyplot as plt

DAY = 0
WEEK = 1
FIRST_DAY = datetime(2001, 10, 9)

class Strategy(object):
    def __init__(self):
        self.trades = []
        self.returns = []
        self.figures = []
        self.frequency = WEEK

    def run_strategy(self):
        with BackTester() as bt:
            bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                            , events='../data/spx_events.csv', quotes='../data/'
                            , fundamentals='../data/fundamentals.csv'
                            , signals_file='../data/sp500_sectors.csv')
            res = None
            orders = []
            while bt.cur_date < FIRST_DAY:
                res = bt.step_day()
            while bt.more_days():
                if self.frequency == WEEK:
                    res = bt.step_week()
                else:
                    res = bt.step_day()
                if res is None:
                    print('No more results!')
                    break
                else:
                    quotes, signals = res
                    self.returns.append(0.0)
                    for order in orders: # close out all open positions
                        ticker, proportion = order
                        df_temp = quotes[quotes['Ticker'] == ticker]
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].min()]['Price'].iloc[0]
                        pct_ret, _ = bt.exit_position(ticker, px_last)
                        self.returns[-1] += pct_ret * proportion
                    orders = self.calculate_positions(quotes, signals)
                    for order in orders:
                        ticker, proportion = order
                        df_temp = quotes[quotes['Ticker'] == ticker]
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].max()]['Price'].iloc[0]
                        if proportion > 0:
                            bt.enter_position(ticker, px_last, 1)
                        else:
                            bt.enter_position(ticker, px_last, -1)
            self.returns.append(0)
            for order in orders:  #get the final returns
                ticker, proportion = order
                px_last = bt.get_final_price(ticker)
                pct_ret, _ = bt.exit_position(ticker, px_last)
                self.returns[-1] += proportion * pct_ret

        self.analyze_trades_and_returns()
        self.save_all_figs()
        print('Strategy backtest done!')

    def calculate_positions(self, quote, signals):
        raise NotImplementedError

    def analyze_trades_and_returns(self):
        raise NotImplementedError

    def save_all_figs(self):
        import os, random, string
        name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        os.mkdir('../data/{}'.format(name))
        print('Serial number for this run: {}'.format(name))
        for i, fig in enumerate(self.figures):
            fig.savefig('../data/{}/fig{}.png'.format(name, i))
