import requests
from datetime import datetime, timedelta

from core.config import settings
from services.amazon_ads_service import AmazonAdsService


class ReportService(AmazonAdsService):

    def get_campaign_report(self, profile_id):

        endpoint = f"{self.BASE_URL}/reporting/reports"

        end_date = (
            datetime.utcnow() - timedelta(days=1)
        )
        start_date = end_date - timedelta(days=30)

        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Amazon-Advertising-API-ClientId": settings.AMAZON_CLIENT_ID,
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Content-Type": "application/vnd.createasyncreportrequest.v3+json",
            "Accept": "application/vnd.createasyncreportrequest.v3+json"
        }

        body = {
            "name": "Campaign Report",
            "startDate": start_date,
            "endDate": end_date,
            "configuration": {
                "adProduct": "SPONSORED_PRODUCTS",
                "groupBy": ["campaign"],
                "columns": [
                    "campaignId",
                    "campaignName",
                    "impressions",
                    "clicks",
                    "cost",
                    "purchases7d",
                    "sales7d"
                ],
                "reportTypeId": "spCampaigns",
                "timeUnit": "DAILY",
                "format": "GZIP_JSON"
            }
        }

        response = requests.post(
            endpoint,
            headers=headers,
            json=body,
            timeout=20
        )

        print("REPORT CREATE STATUS:")
        print(response.status_code)
        print(response.text)

        return response.json()

    def get_report_status(self, profile_id, report_id):

        endpoint = f"{self.BASE_URL}/reporting/reports/{report_id}"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Amazon-Advertising-API-ClientId": settings.AMAZON_CLIENT_ID,
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Accept": "application/vnd.createasyncreportrequest.v3+json"
        }

        response = requests.get(
            endpoint,
            headers=headers,
            timeout=20
        )

        print("REPORT STATUS CHECK:")
        print(response.status_code)
        print(response.text)

        return response.json()