import requests
from core.config import settings


class AmazonAdsService:

    BASE_URL = "https://advertising-api.amazon.com"

    def __init__(self):
        self.access_token = self.get_access_token()

    def get_access_token(self):

        url = "https://api.amazon.com/auth/o2/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": settings.AMAZON_REFRESH_TOKEN,
            "client_id": settings.AMAZON_CLIENT_ID,
            "client_secret": settings.AMAZON_CLIENT_SECRET
        }

        response = requests.post(
            url,
            data=payload
        )

        data = response.json()

        if "access_token" not in data:
            raise Exception(
                f"Amazon Authentication Failed: {data}"
            )

        return data["access_token"]

    def get_campaigns(self, profile_id):

        endpoint = f"{self.BASE_URL}/sp/campaigns/list"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Amazon-Advertising-API-ClientId": settings.AMAZON_CLIENT_ID,
            "Amazon-Advertising-API-Scope": str(profile_id),
            "Content-Type": "application/vnd.spcampaign.v3+json",
            "Accept": "application/vnd.spcampaign.v3+json"
        }

        body = {}

        response = requests.post(
            endpoint,
            headers=headers,
            json=body,
            timeout=30
        )

        print("CAMPAIGN STATUS:")
        print(response.status_code)

        return response.json()