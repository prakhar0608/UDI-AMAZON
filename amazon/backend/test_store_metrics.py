import requests
import gzip
import json

from services.daily_metrics_service import DailyMetricsService

profile_id = "3388765377025893"

report_url = "very long amazon url..."

response = requests.get(report_url)

with open("report.gz", "wb") as f:
    f.write(response.content)

with gzip.open(
    "report.gz",
    "rt",
    encoding="utf-8"
) as f:

    data = json.load(f)

print("TOTAL ROWS:")
print(len(data))

DailyMetricsService.store_metrics(
    profile_id,
    data
)

print("METRICS STORED")