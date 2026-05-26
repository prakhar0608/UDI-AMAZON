from core.supabase_client import supabase


class CampaignStorageService:

    @staticmethod
    def store_campaigns(profile_id, campaigns):

        for campaign in campaigns.get("campaigns", []):

            data = {
                "profile_id": str(profile_id),
                "campaign_id": str(campaign.get("campaignId")),
                "campaign_name": campaign.get("name"),
                "state": campaign.get("state"),
                "budget": campaign.get("budget", {}).get("budget"),
                "start_date": campaign.get("startDate")
            }

            response = supabase.table("campaigns").insert(data).execute()

            print(response)