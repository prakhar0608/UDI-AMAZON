import pandas as pd

from amazon_ads_app.metrics import add_roas_acos, aggregate_campaign_daily


def test_add_roas_acos_basic():
    df = pd.DataFrame(
        {
            "campaign_id": ["1"],
            "campaign_name": ["A"],
            "date": ["2026-04-01"],
            "spend": [10.0],
            "sales": [50.0],
        }
    )
    out = add_roas_acos(df)
    assert abs(out.loc[0, "roas"] - 5.0) < 1e-9
    assert abs(out.loc[0, "acos"] - 0.2) < 1e-9


def test_aggregate_campaign_daily_sums():
    df = pd.DataFrame(
        {
            "campaign_id": ["1", "1"],
            "campaign_name": ["A", "A"],
            "date": ["2026-04-01", "2026-04-01"],
            "spend": [3.0, 7.0],
            "sales": [10.0, 15.0],
        }
    )
    out = aggregate_campaign_daily(df)
    assert len(out) == 1
    assert out.loc[0, "spend"] == 10.0
    assert out.loc[0, "sales"] == 25.0
