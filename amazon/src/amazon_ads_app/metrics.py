"""Derived metrics: RoAS and ACoS."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_roas_acos(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived metrics (roas, acos)."""
    out = df.copy()
    spend = out["spend"].astype(float)
    sales = out["sales"].astype(float)

    out["roas"] = np.where(spend > 0, sales / spend, np.nan)
    out["acos"] = np.where(sales > 0, spend / sales, np.nan)
    return out


def aggregate_campaign_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse duplicate daily rows by summing metrics, then recompute derived fields."""
    if df.empty:
        return df
    
    # Identify available grouping columns
    cols = ["campaign_id", "campaign_name", "ad_group_id", "ad_group_name", "range", "subcat", "asin", "sku", "targeting", "targeting_type", "date"]
    group_cols = [c for c in cols if c in df.columns]

    agg_map = {"spend": "sum", "sales": "sum"}

    g = (
        df.groupby(group_cols, as_index=False)
        .agg(agg_map)
    )
    return add_roas_acos(g)
