from src.BackTester import *
import datetime

if __name__ == '__main__':
    with BackTester() as bt:
        bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                        , events='../data/spx_events.csv', quotes='../data/'
                        , fundamentals='../data/fundamentals.csv'
                        , signals_file='../data/sp500_sectors.csv')

        print(bt.universe.eligible_secs)
        exit()

        print(bt.start_date)
        print(bt.end_date)

        print(bt.step_day())

        bt.set_cur_date(datetime.datetime(2015,12,30))
        print(bt.step_day())

        bt.reset_portfolio()

        bt.step_day()
        bt.enter_position('AAPL', 100, 1000000)
        bt.step_day()
        print(bt.exit_position('AAPL', 101))
        print(bt.exit_position('A', 11))

        for _ in range(1000):
            bt._increment_date()
        print(bt.cur_date)
        print(bt.get_current_fundamentals('AAPL'))
        print(bt.get_current_fundamentals('AAPL', 365))

        print(bt.step_week())