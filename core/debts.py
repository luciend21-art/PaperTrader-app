import pandas as pd
import numpy as np

def simulate_debts(debts_df: pd.DataFrame,
                   monthly_cash_to_debt: pd.Series,
                   start_date,
                   method: str = "highest_apr") -> pd.DataFrame:
    """
    Multi-account snowball.
    debts_df: columns name, start_balance, apr, min_pct, promo_apr, promo_end
    monthly_cash_to_debt: index = month start, value = total $ available that month
    Returns wide df: [date, total_balance, <one col per account>]
    """
    # this is a stub; you’ll implement full logic here
    # but the interface is what the app will call

    # create one row per month in the series index
    dates = monthly_cash_to_debt.index.sort_values()
    accounts = debts_df["name"].tolist()
    balances = {name: debts_df.set_index("name").loc[name, "start_balance"] for name in accounts}

    rows = []
    for dt in dates:
        pool = monthly_cash_to_debt.loc[dt]
        # 1) interest & min payments
        # 2) apply extra to chosen accounts by 'method'
        # 3) update balances

        total_balance = sum(balances.values())
        row = {"date": dt, "total_balance": total_balance}
        for name in accounts:
            row[name] = balances[name]
        rows.append(row)

    return pd.DataFrame(rows)
