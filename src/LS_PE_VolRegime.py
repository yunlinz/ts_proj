"""
Test for Strategy Interface by implementing a strategy to only buy IBM
"""

from src.Strategy import Strategy
from src.BackTester import BackTester
from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.pyplot as plt
from hmmlearn.hmm import GaussianHMM


DAY = 0
WEEK = 1
FIRST_DAY = datetime(2001, 10, 9)
BURN_IN_PERIOD = 24**WEEK*120**DAY # 24 week or 120 days. make no investment in burn-in period

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


class LS_PE_VolRegime(Strategy):
    def __init__(self):
        super(LS_PE_VolRegime, self).__init__()
        # create these variables in addition to the standard ones that are created in the super class
        self.hist_quotes = None
        self.hist_signals = None
        self.fundamentals = None
        self.states = None

    def calculate_hist_data(self, quotes, signals):
        # persist the data frames
        if self.hist_quotes is None:
            self.hist_quotes = quotes
        else:
            self.hist_quotes = self.hist_quotes.append(quotes, ignore_index=True)
        if self.hist_signals is None:
            self.hist_signals = signals
        else:
            self.hist_signals = self.hist_signals.append(signals, ignore_index=True)
            #print self.hist_signals.count
        # don't do any actual processing and just return a single order in IBM
        # return [('IBM', 1)]

    def run_strategy(self):
        with BackTester() as bt:
            bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                            , events='../data/spx_events.csv', quotes='../data/'
                            , fundamentals='../data/fundamentals.csv'
                            , signals_file='../data/sp500_sectors.csv')
            self.fundamentals = bt.fundamentals
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
                    self.calculate_hist_data(quotes, signals)

                    if len(self.dates) < BURN_IN_PERIOD:
                        continue  # do nothing in burn-in days

                    for order in orders: # close out all open positions
                        print order
                        ticker, proportion = order
                        if ticker is 'DVN': # debugging
                            print 'DVN'
                        df_temp = quotes[quotes['Ticker'] == ticker]
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].max()]['Price'].iloc[0]
                        pct_ret, _ = bt.exit_position(ticker, px_last)
                        self.returns[-1] += pct_ret * proportion
                    orders = self.calculate_positions(self.hist_quotes, self.hist_signals, bt)
                    for order in orders:
                        ticker, proportion = order
                        if ticker is 'DVN': # debugging
                            print 'DVN'
                        df_temp = quotes[quotes['Ticker'] == ticker]
                        if df_temp.empty:
                            orders.remove(order) # if stock doesn't exist in quotes file, then remove from orders list
                            continue
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
        df_returns = self.calculate_returns(signals)
        #print signals.count
        #sns.heatmap(df_returns.corr(), annot=True)
        rolling_window = 12
        summary_df = self.hmm_df(df_returns.iloc[-rolling_window:, :])
        return self.generate_trades(summary_df)

    def generate_trades(self, df_hmm_decision):
        trades = []
        for industry_name in df_hmm_decision.index:
            pred_state = df_hmm_decision.loc[industry_name,'prediction'] ## states not uniform. why some states have neg mean???
            sort_col = 'sppe' # CRSP header for PE ratio
            df_stock_industry=self.grab_ticker_by_sector(industry_name,sort_col)
            # might wanna consider correlation when sorting as well
            if pred_state==0: #assuming 0 is high vol state
                pct_stocks_to_trade = 0.4 # trade 40% of sorted stocks, equally spreat between longs and shorts
                num_stock_select = (int) (len(df_stock_industry.index)*pct_stocks_to_trade)
                short_tickers = df_stock_industry['tic'].values[:num_stock_select]
                long_tickers = df_stock_industry['tic'].values[-num_stock_select:]

            portion = 1.0/(len(long_tickers)+len(short_tickers)) # can also try hedge ratio or mean-var (based on forecasted return and correlation to vol regime)

            for ticker in long_tickers:
                trades.append((ticker, portion))
            for ticker in short_tickers:
                trades.append((ticker,-portion))

        return trades

    #def port_optimizer(self, stocks, ): # returns weights

    def grab_ticker_by_sector(self,industry,sort_col):
        gics_code=gics_map_header_to_code[industry]
        df = self.get_fundamentals_by_gics(gics_code, sort_col)
        df.sort_values(by=sort_col, ascending=[1], inplace=True) # sort_criteria = PE
        return df

    def get_fundamentals_by_gics(self, gics_code, sort_col=None, delay=0):
        cur_date = self.dates[-1]
        if sort_col is not None:
            #remove NaNs in sort_col column
            fundamental_dropna = self.fundamentals[np.isfinite(self.fundamentals[sort_col])]
            df = fundamental_dropna[(fundamental_dropna['gsector'] == gics_code) & (fundamental_dropna['datadate'] <= cur_date - timedelta(days=delay))]
        else: df = self.fundamentals[(self.fundamentals['gsector'] == gics_code) & (self.fundamentals['datadate'] <= cur_date - timedelta(days=delay))]
        most_recent = df['datadate'].max()
        return(df[df['datadate'] == most_recent])


    def get_current_fundamentals(self, ticker, gics_code, delay=0):
        with BackTester() as bt:
            df = bt.fundamentals[(bt.fundamentals['tic'] == ticker) & bt.fundamentals['gics'] == gics_code
                               & (bt.fundamentals['datadate'] <= bt.cur_date - datetime.timedelta(days=delay))]
            most_recent = df['datadate'].max()
        return(df[df['datadate'] == most_recent])

    def calculate_returns(self, dataframe):
        return (dataframe.iloc[:,1:].apply(np.log).diff().apply(np.exp) - 1).ix[1:]

    def plot_returns(self, df_returns):
        for c in df_returns.columns:
            fig = plt.figure()
            df_returns[c].hist(bins=100)
            plt.title(c)
            df_returns.describe()

    def hmm_df(self, dataframe):
        summary_df = pd.DataFrame([], columns=['sector', 'state1', 'state2', 'prediction'])
        if self.states is None:
            self.states = pd.DataFrame([], columns=dataframe.columns)
        current_state = pd.DataFrame([], columns=dataframe.columns)
        for c in dataframe.columns:
            series = dataframe[c].values.reshape(-1,1)
            model = GaussianHMM(n_components=2)
            model.fit(series)
            states = model.predict(series)

            rolling_window=12 # 12 week rolling state median
            threshold=0.7 # percentage of state1 in window
            current_state.set_value(0,c,states[-1])
            predictor=self.state_predictor(states, threshold)
            #self.graph_hmm(series, states, c)

            state1_mean = model.means_[0][0]
            state2_mean = model.means_[1][0]

            # default state1 > state2, reverse if not the case
            if state1_mean<state2_mean:
                predictor = 1 - predictor
                current_state[c]=1-current_state[c] # swich names
                summary_df = summary_df.append(pd.DataFrame([[c,
                                                'N({:.2e},{:.2e})'.format(state2_mean, model.covars_[1][0][0]),
                                                'N({:.2e},{:.2e})'.format(state1_mean, model.covars_[0][0][0]),
                                                              predictor]]
                                               , columns=['sector', 'state1', 'state2', 'prediction']),
                                              ignore_index=True)

            else:
                summary_df = summary_df.append(pd.DataFrame([[c,
                                                'N({:.2e},{:.2e})'.format(state1_mean, model.covars_[0][0][0]),
                                                'N({:.2e},{:.2e})'.format(state2_mean, model.covars_[1][0][0]),
                                                              predictor]]
                                               , columns=['sector', 'state1', 'state2', 'prediction']),
                                              ignore_index=True)

        self.states=self.states.append(current_state, ignore_index=True)
        summary_df=summary_df.set_index('sector')
        return(summary_df)


    def state_predictor(self, states, threshold):
        state1_pct = np.sum(states)/len(states)
        if state1_pct>threshold: return 1 # state predictor for given sector
        if 1-state1_pct>threshold: return 0 # state predictor for given sector
        ## need to consider trend as well!!!

    def graph_hmm(self, time_series, pred_states, industry_name):
        fig, ax1 = plt.subplots()
        ax1.plot(time_series)
        ax2 = ax1.twinx()
        ax2.plot(pred_states, 'r--', linewidth=0.25)
        plt.title(industry_name.upper())
        plt.savefig(industry_name+'.png')

    def analyze_trades_and_returns(self):
        # the analysis just plots all the returns
        import matplotlib.pyplot as plt
        fig = plt.figure()
        fig.plot(self.returns)
        self.figures.append(fig)

if __name__ == '__main__':
    # instantiate BuyIbm class
    strat = LS_PE_VolRegime()
    # run the strategy
    strat.run_strategy()
