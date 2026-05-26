from services.amazon_ads_service import AmazonAdsService
from core.supabase_client import supabase

service = AmazonAdsService()

profiles = supabase.table("profiles").select("*").execute()

for profile in profiles.data:

    try:

        profile_id = profile["profile_id"]
        account_name = profile["account_name"]

        print("\n====================")
        print("ACCOUNT:", account_name)
        print("PROFILE:", profile_id)

        campaigns = service.get_campaigns(profile_id)

        print(campaigns)

    except Exception as e:

        print("ERROR:")
        print(e)