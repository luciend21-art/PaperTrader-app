import pandas as pd
import numpy as np

def compute_positions(trades: pd.DataFrame,
                      prices: pd.DataFrame,
                      tickers_meta: pd.DataFrame) -> pd.DataFrame:
    """
    Returns per-ticker positions with:
    ticker, net_shares, avg_cost, latest_price, mv, fwd_yield, net_fwd_yield, ...
    """
    if trades.empty:
        return pd.DataFrame(columns=[
            "ticker","net_shares","avg_cost","latest_price","mv",
            "fwd_yield","net_fwd_yield"
        ])

    # equity-only for now
    eq_trades = trades[trades["asset_type"]=="equity"].copy()
    grp = eq_trades.groupby("ticker")

    net_shares = grp["qty"].sum()
    buy_mask = eq_trades["action"].str.upper() == "BUY"
    buys = eq_trades[buy_mask]
    avg_cost = (buys["qty"] * buys["price"]).groupby(buys["ticker"]).sum() / \
               buys["qty"].groupby(buys["ticker"]).sum()

    latest_price = prices.sort_values("date").groupby("ticker")["close"].last()

    pos = pd.DataFrame({
        "ticker": net_shares.index,
        "net_shares": net_shares.values,
    }).merge(
        avg_cost.rename("avg_cost"), on="ticker", how="left"
    ).merge(
        latest_price.rename("latest_price"), on="ticker", how="left"
    )

    pos["mv"] = pos["net_shares"] * pos["latest_price"]

    # forward yield from historical dividends (you can refine)
    # here: assume we have ttm_div_per_share in tickers_meta
    pos = pos.merge(
        tickers_meta[["ticker","expense_ratio","ttm_div_per_share"]],
        on="ticker", how="left"
    )
    pos["fwd_yield"] = pos["ttm_div_per_share"] / pos["latest_price"]
    pos["net_fwd_yield"] = pos["fwd_yield"] - (pos["expense_ratio"] / 100.0)

    return pos

def compute_equity_curve(positions_ts: pd.DataFrame,
                         cash_ts: pd.Series,
                         margin_ts: pd.Series) -> pd.DataFrame:
    """
    positions_ts: indexed by date, with column 'portfolio_mv'
    cash_ts: Series indexed by date
    margin_ts: Series indexed by date (negative = borrowing)
    """
    df = pd.DataFrame(index=positions_ts.index)
    df["portfolio_mv"] = positions_ts["portfolio_mv"]
    df["cash"] = cash_ts.reindex(df.index).fillna(method="ffill").fillna(0)
    df["margin"] = margin_ts.reindex(df.index).fillna(method="ffill").fillna(0)
    df["equity"] = df["portfolio_mv"] + df["cash"] - df["margin"]
    df["running_max"] = df["equity"].cummax()
    df["drawdown"] = df["equity"] / df["running_max"] - 1
    return df.reset_index().rename(columns={"index":"date"})
