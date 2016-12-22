"""
Test for Strategy Interface by implementing a strategy to only buy IBM
"""

from src.Strategy import Strategy

class BuyIbm(Strategy):
    def calculate_positions(self, quote, signals):
        return [('IBM', 1)]

    def analyze_trades_and_returns(self):
        import matplotlib.pyplot as plt
        fig = plt.figure()
        fig.plot(self.returns)
        self.figures.append(fig)

if __name__ == '__main__':
    strat = BuyIbm()
    strat.run_strategy()
