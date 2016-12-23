from src.Strategy import Strategy

class VolRegimeStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.hist_quotes = []
        self.hist_signals = []
        self.dtw_matrix = []