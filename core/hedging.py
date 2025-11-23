import pandas as pd

def apply_option_hedge(trades: pd.DataFrame,
                       prices: pd.DataFrame,
                       config: dict) -> pd.DataFrame:
    """
    Level 1: track actual hedge P&L from user-entered option trades.
    - Filter trades where is_option == True
    - Combine with closing prices the user records when closing
    - Return a time-series of hedge P&L / cashflows that can be merged into the ledger.
    """
    # stub: implement as you start entering option trades
    return pd.DataFrame()
