Operations guide:

To initialize the database object run script.py: this creates quotes_db.db in data director for fast access and later use

To use the BackTester objects use the following syntax:

with BackTester() as bt:
    bt.set_universe(...)

BackTester object contains the list of securities in the portfolio, the universe and current date

Methods:
1. bt.set_universe(current_spx, spx_events, quote_db): this will read the list of companies currently in the SPX, and backtrack to the beginning of 2001
2. bt.step_day(): returns a Pandas dataframe with the next business day's data, and will automatically process any new events
3. bt.enter_position(ticker, price, amount): enter in a position on the current date--will return True if position is entered into correctly
4. bt.exit_position(ticker, price): exits the position and returns (percent return, dollar return)
