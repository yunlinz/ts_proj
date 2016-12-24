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

# GICS sector codes are in 'gsector' file in the 
gics_map_code_to_header = {
    10 : 'energy',
    15 : 'materials',
    20 : 'industrial',
    25 : 'cons_discretionary',
    30 : 'cons_staple',
    35 : 'healthcare',
    40 : 'financials',
    45 : 'it',
    50 : 'telecom',
    55 : 'utilities',
    60 : 'real_estate'
}

gics_map_header_to_code = {v:k for k, v in gics_map_code_to_header.items()}

class Strategy(object):
    def __init__(self):
        self.trades = []
        self.dates = []
        self.returns = []
        self.figures = []
        self.serial = None
        self.frequency = WEEK
        self.text_data = {}

    def run_strategy(self):
        with BackTester() as bt:
            bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                            , events='../data/spx_events.csv', quotes='../data/'
                            , fundamentals='../data/fundamentals_quarterly.csv'
                            , signals_file='../data/sp500_sectors.csv')
            res = None
            orders = []
            while bt.cur_date < FIRST_DAY:
                res = bt.step_day()
            while bt.more_days():
                self.dates.append(bt.cur_date)
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
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].max()]['Price'].iloc[0]
                        pct_ret, _ = bt.exit_position(ticker, px_last)
                        self.returns[-1] += pct_ret * proportion
                    orders = self.calculate_positions(quotes, signals, bt)
                    for order in orders:
                        ticker, proportion = order
                        df_temp = quotes[quotes['Ticker'] == ticker]
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].max()]['Price'].iloc[0]
                        if proportion > 0:
                            bt.enter_position(ticker, px_last, 1)
                        else:
                            bt.enter_position(ticker, px_last, -1)
                    self.trades.append(orders)
        self.analyze_trades_and_returns()
        self.save_all_data()
        print('Strategy backtest done!')

    def calculate_positions(self, quote, signals, bt):
        raise NotImplementedError

    def analyze_trades_and_returns(self):
        raise NotImplementedError
        import pandas as pd
        import numpy as np
        from datetime import timedelta
        import matplotlib.pyplot as plt

        return_df = pd.DataFrame(data={
            'Date': self.dates,
            'Returns': self.returns
        })
        return_df['Date'] = return_df['Date'].apply(lambda x: x + timedelta(days=1))
        return_df['DlrGrowth'] = 1 + return_df['Returns']
        return_df.set_index('Date').sort_index()
        return_df['CumuGrowth'] = return_df['DlrGrowth'].cumprod()
        sp500 = pd.read_csv('../data/spx.csv', parse_dates=[0]).set_index('Date').sort_index()[['Close']]
        sp500['returns'] = sp500['Close'].apply(np.log).diff().apply(np.exp) - 1
        tbill = pd.read_csv('../data/tbill.csv', parse_dates=[0]).set_index('Date').sort_index()
        tbill['Weekly'] = tbill['Tbill'] * 7.0 / 365.25 # actual/actual method

        sp500 = sp500.join(tbill, how='inner', lsuffix='sp500', rsuffix='tbill')

        strat = return_df.join(sp500, how='inner', lsuffix='strat', rsuffix='')

        strat_annual_return = strat['CumuGrowth'].iloc[-1] ** (len(strat) * 7 / 365.25) - 1
        strat_annual_vol = strat['Returns'].std() * np.sqrt(365.25 / 7)
        strat_sharpe = (strat['Returns'] - strat['Weekly']).mean() * 365.25 / 7 / strat_annual_vol

        strat['CumuGrowthSP'] = strat['Close'] / strat['Close'].iloc[0]
        strat['SPWeekly'] = strat['Close'].apply(np.log).diff().apply(np.exp) - 1

        sp500_annual_return = strat['CumuGrowthSP'].iloc[-1] ** (len(strat) * 7 / 365.25) - 1
        sp500_annual_vol = strat['SPWeekly'].std() * np.sqrt(365.25 / 7)
        sp500_sharpe = (strat['SPWeekly'] - strat['Weekly']).mean() * 365.25 / 7 / strat_annual_vol

        self.text_data['Strategy Annualized Return'] = strat_annual_return
        self.text_data['Strategy Annualized Vol'] = strat_annual_vol
        self.text_data['Strategy Sharpe'] = strat_sharpe
        self.text_data['SP500 Annualized Return'] = sp500_annual_return
        self.text_data['SP500 Annualized Vol'] = sp500_annual_vol
        self.text_data['SP500 Sharpe'] = sp500_sharpe

        fig = plt.figure()
        plt.plot(strat.index, strat['CumuGrowth'], strat['CumuGrowthSP'])
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title('Growth of $1')
        plt.legend(['Strategy', 'S&P500'])
        self.figures.append(fig)


    def save_all_data(self):
        import os, random, string
        name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        self.serial = name
        os.mkdir('../data/{}'.format(name))
        print('Serial number for this run: {}'.format(name))
        for i, fig in enumerate(self.figures):
            fig.savefig('../data/{}/fig{}.png'.format(name, i))
        with open('../data/{}/return_series.csv'.format(name), 'w') as outstream:
            for d, r in zip(self.dates, self.returns):
                outstream.write('{},{}\n'.format(d.strftime('%Y-%m-%d'), r))
        with open('../data/{}/summary.txt'.format(name), 'w') as outstream:
            for k, v in self.text_data.items():
                outstream.write('{}:{}\n'.format(k, v))
