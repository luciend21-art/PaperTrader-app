import streamlit as st
import pandas as pd
from datetime import date

from core.data_io import load_trades, load_cashflows, load_debts, load_tickers
from core.market_data import fetch_price_history, fetch_dividends
from core.portfolio import compute_positions, compute_equity_curve
from core.debts import simulate_debts
from core.hedging import apply_option_hedge

st.set_page_config(page_title="Dividend + Debt PaperTrader", layout="wide")

# ---------- Sidebar: Config ----------
st.sidebar.title("Controls")

trades = load_trades()
cashflows = load_cashflows()
debts_df = load_debts()
tickers_meta = load_tickers()

all_tickers = sorted(trades["ticker"].unique()) if not trades.empty else []

st.sidebar.markdown("### Backtest Dates")

if not trades.empty:
    min_date = trades["date"].min().date()
    max_date = trades["date"].max().date()
else:
    min_date = date(2024,1,1)
    max_date = date.today()

test_start = st.sidebar.date_input(
    "Test Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

as_of = st.sidebar.slider(
    "As-of Date",
    min_value=test_start,
    max_value=max_date,
    value=max_date
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Dividend Reinvestment")

global_reinvest = st.sidebar.checkbox("Reinvest dividends by default", value=True)

reinvest_multiselect = st.sidebar.multiselect(
    "Tickers to reinvest (overrides default)",
    options=all_tickers,
    default=all_tickers if global_reinvest else []
)

# Build reinvest config dict
reinvest_config = {t: (t in reinvest_multiselect) for t in all_tickers}

st.sidebar.markdown("---")
st.sidebar.markdown("### Debt Snowball")

extra_debt_payment = st.sidebar.number_input(
    "Extra $/month to apply to debts",
    min_value=0.0, step=100.0, value=0.0
)

snowball_method = st.sidebar.selectbox(
    "Snowball method",
    ["highest_apr","smallest_balance","custom_promo_aware"]
)

# ---------- Data + Simulation ----------
st.title("Dividend + Margin + Debt Payoff Simulator")

if trades.empty:
    st.info("Upload or populate trades.csv in /data to begin.")
    st.stop()

# 1) price & dividend history
start_str = str(test_start)
end_str = str(as_of)
prices = fetch_price_history(all_tickers, start_str, end_str)
divs = fetch_dividends(all_tickers, start_str, end_str)

# TODO: use divs to compute ttm_div_per_share for each ticker and merge into tickers_meta

positions = compute_positions(trades, prices, tickers_meta)

# 2) build daily portfolio MV, cash, margin from trades + cashflows
# For now we'll stub: you will implement a full ledger later.
# Example simple equity curve using MV only:
if positions.empty or prices.empty:
    st.warning("No positions or prices in selected window.")
else:
    # aggregate portfolio MV by date
    mv_by_date = prices.merge(
        positions[["ticker","net_shares"]],
        on="ticker", how="left"
    )
    mv_by_date["position_mv"] = mv_by_date["close"] * mv_by_date["net_shares"].fillna(0)
    daily_mv = mv_by_date.groupby("date")["position_mv"].sum().to_frame("portfolio_mv")

    # placeholder cash & margin series for now
    cash_ts = pd.Series(0.0, index=daily_mv.index)
    margin_ts = pd.Series(0.0, index=daily_mv.index)

    equity_df = compute_equity_curve(daily_mv, cash_ts, margin_ts)

    # Filter by test_start/as_of
    mask = (equity_df["date"] >= pd.to_datetime(test_start)) & \
           (equity_df["date"] <= pd.to_datetime(as_of))
    equity_view = equity_df.loc[mask].copy()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Equity Curve")
        st.line_chart(equity_view.set_index("date")["equity"])
    with col2:
        st.subheader("Drawdown")
        st.line_chart(equity_view.set_index("date")["drawdown"])

# 3) Debts simulation: map cashflows → monthly_cash_to_debt (stub simple for now)
if not debts_df.empty:
    # Example: treat any cashflow type == "withdraw_to_debt" as debt-payment pool
    cf = cashflows.copy()
    if not cf.empty:
        cf["month"] = cf["date"].dt.to_period("M").dt.to_timestamp()
        monthly_pool = cf[cf["type"]=="withdraw_to_debt"].groupby("month")["amount"].sum()
    else:
        monthly_pool = pd.Series([], dtype=float)

    # add extra_debt_payment each month in range
    if not monthly_pool.empty:
        idx = monthly_pool.index
        monthly_pool = monthly_pool.reindex(idx, fill_value=0.0) + extra_debt_payment
    else:
        # create a monthly index between test_start and as_of
        idx = pd.date_range(start=test_start, end=as_of, freq="MS")
        monthly_pool = pd.Series(extra_debt_payment, index=idx)

    debt_ts = simulate_debts(debts_df, monthly_pool, start_date=monthly_pool.index[0],
                             method=snowball_method)

    st.subheader("Total Debt Balance Over Time")
    if not debt_ts.empty:
        st.line_chart(debt_ts.set_index("date")["total_balance"])

        # Optional: stacked per-account chart
        acct_cols = [c for c in debt_ts.columns if c not in ["date","total_balance"]]
        if acct_cols:
            st.area_chart(debt_ts.set_index("date")[acct_cols])
    else:
        st.write("No simulated debt data yet.")
else:
    st.info("No debts defined in debts.csv yet.")

# 4) Table of positions + net yields
st.markdown("### Current Positions Snapshot")
if not positions.empty:
    show_cols = ["ticker","net_shares","avg_cost","latest_price","mv","fwd_yield","net_fwd_yield"]
    st.dataframe(positions[show_cols])
else:
    st.write("No open positions.")

# 5) Options hedge hook (to be expanded)
st.markdown("### Options Hedge P&L (stub)")
hedge_ts = apply_option_hedge(trades, prices, config={})
if not hedge_ts.empty:
    st.line_chart(hedge_ts.set_index("date")["hedge_pnl"])
else:
    st.write("No option hedge simulation yet. This will populate once hedge logic is implemented.")
