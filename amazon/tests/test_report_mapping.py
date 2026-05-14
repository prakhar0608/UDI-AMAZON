import pytest
from unittest.mock import MagicMock
from amazon_ads_app.reports_v3 import create_sp_daily_report
from amazon_ads_app.api_client import AdsApiClient

def test_create_sp_daily_report_maps_adgroups_to_campaigns():
    client = MagicMock(spec=AdsApiClient)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"reportId": "test-report-id"}
    client.request.return_value = mock_response
    
    report_id = create_sp_daily_report(
        client,
        name="test-report",
        start_date="2026-04-01",
        end_date="2026-04-07",
        report_type="spAdGroups"
    )
    
    assert report_id == "test-report-id"
    
    # Check that request was called with reportTypeId: "spCampaigns"
    # and correct groupBy/columns.
    _, kwargs = client.request.call_args
    body = kwargs["json"]
    assert body["configuration"]["reportTypeId"] == "spCampaigns"
    assert body["configuration"]["groupBy"] == ["campaign", "adGroup"]
    assert "roasClicks14d" in body["configuration"]["columns"]
    assert "acosClicks14d" in body["configuration"]["columns"]

def test_create_sp_daily_report_uses_sp_targeting_directly():
    client = MagicMock(spec=AdsApiClient)
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"reportId": "test-report-id"}
    client.request.return_value = mock_response
    
    report_id = create_sp_daily_report(
        client,
        name="test-report",
        start_date="2026-04-01",
        end_date="2026-04-07",
        report_type="spTargeting"
    )
    
    assert report_id == "test-report-id"
    
    # Check that request was called with reportTypeId: "spTargeting"
    _, kwargs = client.request.call_args
    body = kwargs["json"]
    assert body["configuration"]["reportTypeId"] == "spTargeting"
    assert body["configuration"]["groupBy"] == ["campaign", "adGroup", "targeting"]
    assert "roasClicks14d" in body["configuration"]["columns"]

def test_create_sp_daily_report_maps_products_to_advertised_product():
    client = MagicMock(spec=AdsApiClient)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"reportId": "test-report-id"}
    client.request.return_value = mock_response
    
    report_id = create_sp_daily_report(
        client,
        name="test-report",
        start_date="2026-04-01",
        end_date="2026-04-07",
        report_type="spProducts"
    )
    
    assert report_id == "test-report-id"
    
    _, kwargs = client.request.call_args
    body = kwargs["json"]
    assert body["configuration"]["reportTypeId"] == "spAdvertisedProduct"
    assert body["configuration"]["groupBy"] == ["advertiser"]
    assert "advertisedAsin" in body["configuration"]["columns"]

