from src.BackTester import *

if __name__ == '__main__':
    with BackTester() as bt:
        bt.set_universe(current_spx='../data/spx_constituents_20161216.csv'
                        , events='../data/spx_events.csv', quotes='../data/')
        print(bt.start_date)
        print(bt.end_date)

        assert (len(bt.step_day())==618)
        assert (len(bt.step_day())==618)
        assert (len(bt.step_day())==617)
        assert (len(bt.step_day())==617)
        assert (len(bt.step_day())==617)
        assert (len(bt.step_day())==616)