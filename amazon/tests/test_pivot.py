import pandas as pd

from amazon_ads_app.pivot_wide import pivot_campaigns_wide


def test_pivot_wide_two_campaigns():
    dates = ["2026-04-01", "2026-04-02"]
    df = pd.DataFrame(
        {
            "campaign_id": ["1", "1", "2"],
            "campaign_name": ["A", "A", "B"],
            "date": ["2026-04-01", "2026-04-02", "2026-04-01"],
            "spend": [1.0, 2.0, 3.0],
            "sales": [10.0, 20.0, 30.0],
            "roas": [10.0, 10.0, 10.0],
            "acos": [0.1, 0.1, 0.1],
        }
    )
    wide = pivot_campaigns_wide(df, dates)
    assert len(wide) == 2
    row_a = wide[wide["campaign_id"] == "1"].iloc[0]
    # spend and sales are now rounded to int
    assert row_a["spend_2026-04-01"] == 1
    assert row_a["spend_2026-04-02"] == 2
    # acos is now * 100
    assert row_a["acos_2026-04-01"] == 10.0
    row_b = wide[wide["campaign_id"] == "2"].iloc[0]
    assert pd.isna(row_b["spend_2026-04-02"])

    # Verify column order: spend_D1, sales_D1, roas_D1, acos_D1, spend_D2, sales_D2, roas_D2, acos_D2
    expected_cols = [
        "campaign_id", "campaign_name",
        "spend_2026-04-01", "sales_2026-04-01", "roas_2026-04-01", "acos_2026-04-01",
        "spend_2026-04-02", "sales_2026-04-02", "roas_2026-04-02", "acos_2026-04-02"
    ]
    assert list(wide.columns) == expected_cols
