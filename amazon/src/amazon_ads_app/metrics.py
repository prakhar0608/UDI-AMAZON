"""Derived metrics: RoAS and ACoS."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived metrics (roas, acos, ctr, cpc, cvr)."""
    if df.empty: return df
    out = df.copy()
    spend = out["spend"].astype(float)
    sales = out["sales"].astype(float)
    clicks = out["clicks"].astype(float) if "clicks" in out.columns else pd.Series(0, index=out.index)
    impressions = out["impressions"].astype(float) if "impressions" in out.columns else pd.Series(0, index=out.index)
    orders = out["orders"].astype(float) if "orders" in out.columns else pd.Series(0, index=out.index)

    out["roas"] = np.where(spend > 0, sales / spend, 0.0)
    out["acos"] = np.where(sales > 0, spend / sales, 0.0)
    out["ctr"] = np.where(impressions > 0, clicks / impressions, 0.0)
    out["cpc"] = np.where(clicks > 0, spend / clicks, 0.0)
    out["cvr"] = np.where(clicks > 0, orders / clicks, 0.0)
    return out


def aggregate_campaign_daily(df: pd.DataFrame, report_type: str = "spCampaigns") -> pd.DataFrame:
    """Collapse duplicate daily rows by summing metrics, then recompute derived fields."""
    if df.empty:
        return df
    
    # Identify available grouping columns
    cols = ["campaign_id", "campaign_name", "ad_group_id", "ad_group_name", "range", "subcat", "asin", "sku", "targeting", "targeting_type", "date"]
    
    if report_type == "spProducts":
        # For product-wise, we want to sum metrics per ASIN per Day across all campaigns.
        # We must EXCLUDE campaign/adgroup columns from the group_by to aggregate correctly.
        group_cols = [c for c in ["range", "subcat", "asin", "sku", "date"] if c in df.columns]
    else:
        group_cols = [c for c in cols if c in df.columns]

    agg_map = {"spend": "sum", "sales": "sum", "impressions": "sum", "clicks": "sum", "orders": "sum"}
    # Filter agg_map to only include columns present in df
    agg_map = {k: v for k, v in agg_map.items() if k in df.columns}

    g = (
        df.groupby(group_cols, as_index=False)
        .agg(agg_map)
    )
    return add_derived_metrics(g)
