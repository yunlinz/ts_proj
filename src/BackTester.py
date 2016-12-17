from src.BackTestObjects import *

class BackTester(object):
    def __init__(self):
        self.portfolio = Portfolio()
        self.universe = Universe()
        self.start_date = None
        self.end_date = None

    def set_universe(self, current_spx=None, events=None):
        self.start_date, self.end_date = self.universe.initialize_from_files(current_spx=current_spx, events=events)


