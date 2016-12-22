"""
Test for Strategy Interface by implementing a strategy to only buy IBM
"""

from src.Strategy import Strategy

class BuyIbm(Strategy):
    def __init__(self):
        super().__init__()
        self.hist_quotes = None
        self.hist_signals = None

    def calculate_positions(self, quote, signals):
        if self.hist_quotes is None:
            self.hist_quotes = quote
        else:
            self.hist_quotes = self.hist_quotes.append(quote, ignore_index=True)
        if self.hist_signals is None:
            self.hist_signals = signals
        else:
            self.hist_signals.append(signals, ignore_index=True)
        return [('IBM', 1)]

    def analyze_trades_and_returns(self):
        import matplotlib.pyplot as plt
        fig = plt.figure()
        fig.plot(self.returns)
        self.figures.append(fig)

if __name__ == '__main__':
    strat = BuyIbm()
    strat.run_strategy()
