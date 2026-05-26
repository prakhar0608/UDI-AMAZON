from services.amazon_ads_service import AmazonAdsService
from services.campaign_storage_service import CampaignStorageService
from core.supabase_client import supabase

service = AmazonAdsService()

profiles = supabase.table("profiles").select("*").execute()

for profile in profiles.data:

    profile_id = profile["profile_id"]

    campaigns = service.get_campaigns(profile_id)

    if campaigns.get("campaigns"):

        CampaignStorageService.store_campaigns(
            profile_id,
            campaigns
        )

        print("CAMPAIGNS STORED")  