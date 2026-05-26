import time

from services.report_service import ReportService

service = ReportService()

profile_id = "3388765377025893"

report_id = "7f69c82b-cddb-4a98-be27-a793bf098a55"

while True:

    status = service.get_report_status(
        profile_id,
        report_id
    )

    report_status = status.get("status")

    print("\nCURRENT STATUS:")
    print(report_status)

    if report_status == "COMPLETED":

        print("\nREPORT READY")
        print(status.get("url"))

        break

    elif report_status == "FAILED":

        print("\nREPORT FAILED")
        print(status)

        break

    time.sleep(20)