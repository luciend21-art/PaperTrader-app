import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

def load_trades() -> pd.DataFrame:
    path = DATA_DIR / "trades.csv"
    if not path.exists():
        return pd.DataFrame(columns=["date","ticker","action","qty","price","fees",
                                     "asset_type","is_option","option_type","strike",
                                     "expiry","contracts"])
    df = pd.read_csv(path, parse_dates=["date"])
    return df

def load_cashflows() -> pd.DataFrame:
    path = DATA_DIR / "cashflows.csv"
    if not path.exists():
        return pd.DataFrame(columns=["date","type","ticker","amount","notes"])
    df = pd.read_csv(path, parse_dates=["date"])
    return df

def load_debts() -> pd.DataFrame:
    path = DATA_DIR / "debts.csv"
    if not path.exists():
        return pd.DataFrame(columns=["name","start_balance","apr","min_pct",
                                     "promo_apr","promo_end"])
    df = pd.read_csv(path, parse_dates=["promo_end"])
    return df

def load_tickers() -> pd.DataFrame:
    path = DATA_DIR / "tickers.csv"
    if not path.exists():
        return pd.DataFrame(columns=["ticker","expense_ratio","reinvest_dividends"])
    df = pd.read_csv(path)
    return df
