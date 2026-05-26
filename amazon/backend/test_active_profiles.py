from services.amazon_ads_service import AmazonAdsService
from core.supabase_client import supabase

service = AmazonAdsService()

profiles = supabase.table("profiles").select("*").execute()

for profile in profiles.data:

    try:

        profile_id = profile["profile_id"]
        account_name = profile["account_name"]

        campaigns = service.get_campaigns(profile_id)

        total = campaigns.get("totalResults", 0)

        if total > 0:

            print("\n====================")
            print("ACTIVE ACCOUNT FOUND")
            print("ACCOUNT:", account_name)
            print("PROFILE:", profile_id)
            print("TOTAL CAMPAIGNS:", total)

    except Exception as e:

        pass