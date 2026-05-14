"""Parse downloaded report bytes into a normalized DataFrame."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd

from amazon_ads_app.reports_v3 import decompress_if_gzip

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParseReportResult:
    dataframe: pd.DataFrame
    has_row_date: bool


def _records_from_payload(payload: bytes) -> list[dict[str, Any]]:
    raw = decompress_if_gzip(payload)
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return []
    if text[0] == "[":
        data = json.loads(text)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            # Some responses wrap rows
            for key in ("records", "data", "rows"):
                if key in data and isinstance(data[key], list):
                    return [x for x in data[key] if isinstance(x, dict)]
        return []
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except json.JSONDecodeError:
            logger.debug("skip_line_parse", extra={"line": line[:200]})
    return rows


def _first(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return None


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Map API-specific keys to canonical columns."""
    if not records:
        return pd.DataFrame()

    def _val(row, keys):
        v = _first(row, keys)
        if v is None: return ""
        s = str(v).strip()
        return s

    # Pre-scan records to see which columns we actually have WITH data
    has_agid = any(_val(r, ("adGroupId", "ad_group_id")) != "" for r in records)
    has_agname = any(_val(r, ("adGroupName", "ad_group_name")) != "" for r in records)
    has_targeting = any(_val(r, ("targeting", "targeting_expression", "targetingExpression")) != "" for r in records)
    has_targeting_type = any(_val(r, ("targetingType", "targeting_type")) != "" for r in records)
    has_asin = any(_val(r, ("asin", "advertisedAsin")) != "" for r in records)
    has_sku = any(_val(r, ("sku", "advertisedSku")) != "" for r in records)

    out_rows: list[dict[str, Any]] = []
    for row in records:
        cid = _first(row, ("campaignId", "campaign_id", "id"))
        cname = _first(row, ("campaignName", "campaign_name", "name"))
        
        day = _first(row, ("date", "startDate", "day"))
        if "costMicros" in row and row.get("costMicros") is not None:
            cost = float(row["costMicros"]) / 1_000_000.0
        else:
            cost = _first(row, ("cost", "spend"))
        
        # Primary for sales is sales14d in V3 to match Amazon Console standard attribution,
        # fallback to sales7d or sales1d if needed.
        sales = _first(row, ("sales14d", "sales7d", "sales1d", "sales_14d", "sales_7d", "sales_1d"))

        item: dict[str, Any] = {
            "campaign_id": str(cid) if cid is not None else "",
            "campaign_name": str(cname or ""),
            "date": str(day)[:10] if day is not None else "",
            "impressions": int(_first(row, ("impressions",)) or 0),
            "clicks": int(_first(row, ("clicks",)) or 0),
            "spend": float(cost) if cost is not None else 0.0,
            "sales": float(sales) if sales is not None else 0.0,
        }

        if has_agid:
            item["ad_group_id"] = _val(row, ("adGroupId", "ad_group_id"))
        if has_agname:
            item["ad_group_name"] = _val(row, ("adGroupName", "ad_group_name"))
        if has_targeting:
            item["targeting"] = _val(row, ("targeting", "targeting_expression", "targetingExpression"))
        if has_targeting_type:
            item["targeting_type"] = _val(row, ("targetingType", "targeting_type"))
        if has_asin:
            item["asin"] = _val(row, ("asin", "advertisedAsin"))
        if has_sku:
            item["sku"] = _val(row, ("sku", "advertisedSku"))

        out_rows.append(item)
    df = pd.DataFrame(out_rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.date.astype(str)
    return df


def parse_report_payload(payload: bytes) -> pd.DataFrame:
    recs = _records_from_payload(payload)
    return records_to_dataframe(recs)


def parse_report_payload_with_meta(payload: bytes) -> ParseReportResult:
    recs = _records_from_payload(payload)
    has_row_date = any(
        ("date" in r and r.get("date") is not None)
        or ("startDate" in r and r.get("startDate") is not None)
        or ("day" in r and r.get("day") is not None)
        for r in recs
    )
    return ParseReportResult(dataframe=records_to_dataframe(recs), has_row_date=has_row_date)
