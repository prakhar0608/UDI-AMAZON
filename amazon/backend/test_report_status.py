from services.report_service import ReportService

service = ReportService()

profile_id = "1635579834460007"

report_id = "7f69c82b-cddb-4a98-be27-a793bf098a55"

status = service.get_report_status(
    profile_id,
    report_id
)

print(status)