"""
Test for Strategy Interface by implementing a strategy to only buy IBM
"""

from src.Strategy import Strategy

class BuyIbm(Strategy):
    def __init__(self):
        super().__init__()
        # create these variables in addition to the standard ones that are created in the super class
        self.hist_quotes = None
        self.hist_signals = None

    def calculate_positions(self, quote, signals, bt):
        # persist the data frames
        if self.hist_quotes is None:
            self.hist_quotes = quote
        else:
            self.hist_quotes = self.hist_quotes.append(quote, ignore_index=True)
        if self.hist_signals is None:
            self.hist_signals = signals
        else:
            self.hist_signals.append(signals, ignore_index=True)

        # don't do any actual processing and just return a single order in IBM
        return [('IBM', 1)]



if __name__ == '__main__':
    # instantiate BuyIbm class
    strat = BuyIbm()
    # run the strategy
    strat.run_strategy()
