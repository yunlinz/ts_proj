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


'''Changes (12/25)
1. now trade 2 highest PE stocks and 2 lowest PE stocks in each industry (we could trade 1 long 1 short in each sector, but I thought that trade is too concentraded given not all trades get closed out in our code)
2. hmm state based on daily volatility calculated on a rolling 12-day (2-week) window. Note this is unnormalized daily returns
3. now using quarterly fundamental csho(q)*px_last*ni(q) as PE ratio (more datapoints than sppe from annual files)
4. hmm and volaitlity forecast window changed to be consistent with volatility window.
5. refined state predictor: see comments in state_predictor method, now based on both absolute probabilities, as well as trend (full range probability vs recent half period probability)
'''

DAY = 0
WEEK = 1
FIRST_DAY = datetime(2001, 10, 9)
BURN_IN_PERIOD = 52**WEEK*260**DAY # 52 week or 260 days. make no investment in burn-in period

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
    '''
    def run_strategy(self):
        with BackTester() as bt:
            bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                            , events='../data/spx_events.csv', quotes='../data/'
                            , fundamentals='../data/fundamentals_quarterly.csv'
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
                        #print(order)
                        ticker, proportion = order
                        df_temp = quotes[quotes['Ticker'] == ticker]
                        if df_temp.empty:
                            continue
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].max()]['Price'].iloc[0]
                        try:
                            pct_ret, _ = bt.exit_position(ticker, px_last)
                        except:
                            pct_ret=0.0
                        if np.isnan(pct_ret): pct_ret=0.0
                        self.returns[-1] += pct_ret * proportion

                    orders = self.calculate_positions(self.hist_quotes, self.hist_signals, bt)
                    #orders = self.validate_order_list(orders, quotes) # if tickers are not avail. in quotes, then drop order
                    for order in list(orders):
                        ticker, proportion = order
                        df_temp = quotes[quotes['TICKER'] == ticker]
                        if df_temp.empty:
                            orders.remove(order) # if stock doesn't exist in quotes file, then remove from orders list
                            continue
                        px_last = df_temp[df_temp['Date'] == df_temp['Date'].max()]['Adj_Price'].iloc[0]
                        if proportion > 0:
                            bt.enter_position(ticker, px_last, 1)
                        else:
                            bt.enter_position(ticker, px_last, -1)
                    self.trades.append(orders)
        self.analyze_trades_and_returns()
        self.save_all_data()
        print('Strategy backtest done!')
    '''
    def validate_order_list(self, orders, quotes):
        #check if quotes file contains all order tickers, if not, remove from order list
        return [order for order in orders if order[0] in quotes['TICKER']]

    def calculate_positions(self, quote, signals, bt):
        df_returns = self.calculate_returns(signals)
        #print signals.count
        #sns.heatmap(df_returns.corr(), annot=True)
        rolling_window = 252
        df_std=pd.rolling_std(df_returns, window=20) # montly rolling volatility
        df_std=df_std.dropna()
        #summary_df = self.hmm_df(df_std.iloc[-rolling_window:, :]) #most recent year data for vol regime estimates
        summary_df = self.hmm_df(df_std) # use cumulative data for hmmm estimates
        return self.generate_trades(summary_df)

    def generate_trades(self, df_hmm_decision):
        trades = []
        for industry_name in df_hmm_decision.index:
            pred_state = df_hmm_decision.loc[industry_name,'prediction'] ## states not uniform. why some states have neg mean???
            #sort_col = 'sppe' # CRSP header for PE ratio
            sort_col = self.calc_PE()# add PE column to self.fundamentals and return column name

            df_stock_industry=self.grab_ticker_by_sector(industry_name,sort_col)
            df_stock_industry=df_stock_industry[np.isfinite(df_stock_industry[sort_col])]
            # might wanna consider correlation when sorting as well

            #pct_stocks_to_trade = 0.4 # trade 40% of sorted stocks, equally spreat between longs and shorts
            #num_stock_select = (int) (len(df_stock_industry.index)*pct_stocks_to_trade)
            num_stock_select=2 # select two stocks for each direction (L/S) in each sector

            if pred_state==0: #assuming 0 is high vol state
                long_tickers = df_stock_industry['tic'].values[-num_stock_select:]
                short_tickers = df_stock_industry['tic'].values[:num_stock_select]
            else:
                long_tickers = df_stock_industry['tic'].values[:num_stock_select]
                short_tickers = df_stock_industry['tic'].values[-num_stock_select:]

            port_daily_trading_limit = 0.3 # max percentage can trade per day
            portion = 1.0/(len(long_tickers))*port_daily_trading_limit # can also try hedge ratio or mean-var (based on forecasted return and correlation to vol regime)

            for ticker in long_tickers:
                trades.append((ticker, portion))
            for ticker in short_tickers:
                trades.append((ticker,-portion))

        return trades

    #def port_optimizer(self, stocks, ): # returns weights

    def calc_PE(self):
        num_shrs = self.fundamentals['cshoq']
        qe_prices = self.fundamentals['prccq']
        net_income_q = self.fundamentals['niq']
        net_income_annual = net_income_q*4
        pe = num_shrs * qe_prices / net_income_annual
        new_col_name = 'PE_q'
        self.fundamentals[new_col_name]=pe
        return new_col_name # returns column name in self.fundamentals

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

            rolling_window=10 # 12 week rolling state median

            threshold=0.95 # probability of significance: either state1 or state2 has to pass the threshold in order to be considered a predicted state
            current_state.set_value(0,c,states[-1])
            prediction_window = 20 # 1 month state estimates for prediction
            predictor=self.state_predictor(states, threshold, prediction_window)
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


    def state_predictor(self, states, threshold=0.95, prediction_window=20):

        states=states[-min(prediction_window,len(states)):] # select last month state estimates for prediction
        # full-period probability
        p1_full = np.sum(states)/len(states)*1.0
        p0_full = 1 - p1_full
        p1_recent = np.sum(states[-len(states)/2:])/(len(states)/2.0) # p1 calculated on most recent half of states vector
        p0_recent = 1 - p1_recent
        cur_state = states[-1]

        # if probability for state1 or state2 are very high (higher than threshold), conclude with high probability state
        if p1_full>threshold: return 1 # state predictor for given sector
        if p0_full>threshold: return 0 # state predictor for given sector

        # if two states have similar probabilities, then consider trend
        if p1_recent>p1_full: return 1
        elif p1_recent<p1_full:  return 0
        else: return cur_state # if state1 and 2 have same probability, use current state as predictor


    def graph_hmm(self, time_series, pred_states, industry_name):
        fig, ax1 = plt.subplots()
        ax1.plot(time_series)
        ax2 = ax1.twinx()
        ax2.plot(pred_states, 'r--', linewidth=0.25)
        plt.title(industry_name.upper())
        plt.savefig(industry_name+'.png'(fig))

if __name__ == '__main__':
    # instantiate BuyIbm class
    strat = LS_PE_VolRegime()
    # run the strategy
    strat.run_strategy()
