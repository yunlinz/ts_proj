from src.BackTester import *

if __name__ == '__main__':
    with BackTester() as bt:
        bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                        , events='../data/spx_events.csv', quotes='../data/'
                        , fundamentals='../data/fundamentals.csv')
        print(bt.start_date)
        print(bt.end_date)

        assert (len(bt.step_day()) == 618)
        assert (len(bt.step_day()) == 618)
        assert (len(bt.step_day()) == 617)
        assert (len(bt.step_day()) == 617)
        assert (len(bt.step_day()) == 617)
        assert (len(bt.step_day()) == 616)

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