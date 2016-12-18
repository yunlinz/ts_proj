from src.BackTestObjects import *
import copy
import pandas as pd
import datetime

class BackTester(object):
    def __init__(self):
        self.portfolio = Portfolio()
        self.universe = Universe()
        self.cur_date = None
        self.start_date = None
        self.end_date = None

    def __enter__(self):
        return BackTester()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.universe.price_db is not None:
            self.universe.price_db.close()

    def set_universe(self, current_spx=None, events=None, quotes=None):
        self.start_date, self.end_date = \
            self.universe.initialize_from_files(current_spx=current_spx
                                                 , events=events
                                                 , quotes_dir=quotes)
        self.cur_date = copy.deepcopy(self.start_date)

    def step_day(self):
        if self.cur_date > self.end_date:
            return None
        query = 'SELECT * FROM QUOTES WHERE DATE = DATETIME(\'{}\')'\
            .format(self.cur_date.strftime('%Y-%m-%d'))
        df = pd.read_sql(query
                         , self.universe.price_db)
        self.cur_date += datetime.timedelta(days=1)
        while len(df) == 0:
            df = self.step_day()
        return df

