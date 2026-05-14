"""Pivot long daily rows to wide columns (one column group per metric × day)."""

from __future__ import annotations

import pandas as pd

METRICS = ("spend", "sales", "roas", "acos")


def pivot_campaigns_wide(df: pd.DataFrame, dates: list[str], report_type: str = "spCampaigns") -> pd.DataFrame:
    """
    One row per grouping (campaign, adGroup, or targeting/ASIN).
    For each date, emit spend, sales, roas, acos columns.
    """
    # Identify grouping columns
    if report_type == "spProducts":
        # ASIN level only - remove campaign and ad group columns
        # Ensure 'range' and 'subcat' are at the front of meta_cols
        potential_meta = ["range", "subcat", "asin", "sku"]
    else:
        potential_meta = ["campaign_id", "campaign_name", "ad_group_id", "ad_group_name", "range", "subcat", "asin", "sku", "targeting", "targeting_type"]
    
    # If columns are missing but we are in spProducts, we expect they are coming from long_df
    meta_cols = [c for c in potential_meta if c in df.columns]
    
    if report_type == "spProducts":
        # Strictly by ASIN/SKU across the account as requested
        # Use a list of cols that exist in df
        group_by = [c for c in ["range", "subcat", "asin", "sku"] if c in df.columns]
        if not group_by: 
            # Extreme fallback if no asin columns found
            group_by = [c for c in df.columns if "_id" in c][:1] or [df.columns[0]]
    else:
        # We need a stable key for grouping. campaign_id is always present.
        group_by = ["campaign_id"]
        if "ad_group_id" in meta_cols:
            group_by.append("ad_group_id")
        if "asin" in meta_cols:
            group_by.append("asin")
        if "targeting" in meta_cols:
            group_by.append("targeting")

    if df.empty:
        cols = list(meta_cols)
        for d in dates:
            for m in METRICS:
                cols.append(f"{m}_{d}")
        return pd.DataFrame(columns=cols)

    work = df[df["date"].isin(dates)].copy()
    rows: list[dict[str, object]] = []
    
    for _, grp in work.groupby(group_by, sort=False):
        # Extract metadata from the first row of the group
        first = grp.iloc[0]
        row: dict[str, object] = {}
        for c in meta_cols:
            val = first[c]
            if "_id" in c and pd.notna(val):
                # Ensure IDs don't have decimals
                try:
                    row[c] = str(int(float(val)))
                except:
                    row[c] = str(val)
            else:
                row[c] = val
        
        by = grp.set_index("date")
        for d in dates:
            if d not in by.index:
                for m in METRICS:
                    row[f"{m}_{d}"] = float("nan")
                continue
            r = by.loc[d]
            if isinstance(r, pd.DataFrame):
                # This could happen if there are still duplicate dates after aggregation
                r = r.iloc[0]
            for m in METRICS:
                val = float(r[m]) if m in r and pd.notna(r[m]) else float("nan")
                if pd.isna(val):
                    row[f"{m}_{d}"] = float("nan")
                elif m in ("spend", "sales"):
                    row[f"{m}_{d}"] = int(round(val))
                elif m == "roas":
                    row[f"{m}_{d}"] = round(val, 2)
                elif m == "acos":
                    # Convert to percentage and round to 2 decimal points
                    row[f"{m}_{d}"] = round(val * 100, 2)
                else:
                    row[f"{m}_{d}"] = val
        rows.append(row)
        
    out = pd.DataFrame(rows)
    
    # Order: Metadata, then Date1 (Spend, Sales, ROI, ACoS), Date2...
    order = list(meta_cols) + [
        f"{m}_{d}" for d in dates for m in METRICS
    ]
    out = out.reindex(columns=order)
    
    # Sort by campaign_name if available, else by asin
    sort_cols = []
    if "campaign_name" in meta_cols:
        sort_cols.append("campaign_name")
        if "ad_group_name" in meta_cols:
            sort_cols.append("ad_group_name")
    elif "asin" in meta_cols:
        sort_cols.append("asin")
        if "sku" in meta_cols:
            sort_cols.append("sku")
    
    if sort_cols:
        return out.sort_values(sort_cols, kind="stable").reset_index(drop=True)
    return out.reset_index(drop=True)
