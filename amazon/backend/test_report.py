from services.report_service import ReportService
from core.supabase_client import supabase

service = ReportService()

profiles = supabase.table("profiles").select("*").execute()

for profile in profiles.data:

    try:

        profile_id = profile["profile_id"]
        account_name = profile["account_name"]

        print("\n====================")
        print("ACCOUNT:", account_name)
        print("PROFILE:", profile_id)

        report = service.get_campaign_report(profile_id)

        print(report)

    except Exception as e:

        print("ERROR:")
        print(e)