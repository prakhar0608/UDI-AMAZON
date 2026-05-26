from services.amazon_ads_service import AmazonAdsService
from core.supabase_client import supabase

service = AmazonAdsService()

profiles = supabase.table("profiles").select("*").execute()

first_profile = profiles.data[0]

profile_id = first_profile["profile_id"]

print("USING PROFILE:")
print(profile_id)

campaigns = service.get_campaigns(profile_id)

print(campaigns)