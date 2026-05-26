from services.report_service import ReportService

service = ReportService()

profile_id = "3388765377025893"

report_id = "edf2c133-17b2-4372-b2e9-361d2c3a8d49"

status = service.get_report_status(
    profile_id,
    report_id
)

print(status)