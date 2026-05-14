from pathlib import Path

from amazon_ads_app.parse_report import parse_report_payload


def test_parse_sample_json_file():
    p = Path(__file__).parent / "fixtures" / "sample_report.json"
    df = parse_report_payload(p.read_bytes())
    assert len(df) == 1
    assert df.loc[0, "campaign_name"] == "Test Campaign"
    assert df.loc[0, "spend"] == 12.34
    assert df.loc[0, "sales"] == 56.78
