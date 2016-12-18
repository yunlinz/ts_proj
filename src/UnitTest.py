from src.BackTester import *

if __name__ == '__main__':
    bt = BackTester()
    bt.set_universe(current_spx='../data/spx_constituents_20161216.csv', events='../data/spx_events.csv')
    import pprint as pp
    pp.pprint(bt.universe.eligible_secs)