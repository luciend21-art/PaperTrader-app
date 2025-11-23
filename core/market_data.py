import pandas as pd
import yfinance as yf
from pathlib import Path

CACHE = Path("data") / "prices_cache.parquet"

def fetch_price_history(tickers, start, end) -> pd.DataFrame:
    """
    Returns: df with columns [date, ticker, close]
    """
    frames = []
    for t in tickers:
        hist = yf.Ticker(t).history(start=start, end=end)
        if hist.empty:
            continue
        tmp = hist.reset_index()[["Date","Close"]]
        tmp["ticker"] = t
        tmp.rename(columns={"Date":"date","Close":"close"}, inplace=True)
        frames.append(tmp)
    if not frames:
        return pd.DataFrame(columns=["date","ticker","close"])
    return pd.concat(frames, ignore_index=True)

def fetch_dividends(tickers, start, end) -> pd.DataFrame:
    """
    Returns: df with columns [pay_date, ticker, div_per_share]
    """
    rows = []
    for t in tickers:
        tk = yf.Ticker(t)
        divs = tk.dividends
        if divs is None or divs.empty:
            continue
        divs = divs[(divs.index >= start) & (divs.index <= end)]
        for dt, amt in divs.items():
            rows.append({"pay_date": dt, "ticker": t, "div_per_share": amt})
    return pd.DataFrame(rows)
