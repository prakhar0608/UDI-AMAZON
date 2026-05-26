from core.supabase_client import supabase


class DailyMetricsService:

    @staticmethod
    def store_metrics(profile_id, metrics_data):

        for row in metrics_data:

            impressions = int(row.get("impressions", 0))
            clicks = int(row.get("clicks", 0))

            spend = float(row.get("cost", 0))
            sales = float(row.get("sales7d", 0))

            orders = int(row.get("purchases7d", 0))

            ctr = (
                (clicks / impressions) * 100
                if impressions > 0 else 0
            )

            cpc = (
                spend / clicks
                if clicks > 0 else 0
            )

            roas = (
                sales / spend
                if spend > 0 else 0
            )

            acos = (
                (spend / sales) * 100
                if sales > 0 else 0
            )

            data = {

                "profile_id": str(profile_id),

                "campaign_id": str(
                    row.get("campaignId")
                ),

                "date": row.get("date"),

                "impressions": impressions,
                "clicks": clicks,

                "spend": spend,
                "sales": sales,

                "orders": orders,

                "ctr": ctr,
                "cpc": cpc,
                "roas": roas,
                "acos": acos
            }

            response = supabase.table(
                "daily_metrics"
            ).insert(data).execute()

            print(response)