import requests
import gzip
import json

from services.daily_metrics_service import DailyMetricsService

profile_id = "3388765377025893"

report_url = "https://offline-report-storage-us-east-1-prod.s3.amazonaws.com/7f69c82b-cddb-4a98-be27-a793bf098a55-1779777591377/report-7f69c82b-cddb-4a98-be27-a793bf098a55-1779777591377.json.gz?X-Amz-Security-Token=IQoJb3JpZ2luX2VjEK%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJHMEUCIGxujUcF787YbqB6aL5V1Ae94zY0y4keA3pJGcDZsck9AiEAmfq4giS09XeKfcvWUdE4jtFyOd8OUa49fP2PQ0ttvUIq4QUIeBADGgw4NDE2NDU1NDMwNzQiDPeiPxxM363A0NO1tSq%2BBRGKcS8FVRy3Dh191uD0S4YqCSJkuXFJTpBBLNnRp%2BvMKW7zEhsk1MEuIs1eXYxSSPGru5QHLwnK9DrDAkEAcr98fkUXdaMCRTFZez2ibjRCmHI%2B%2BfHenjzqDOsKazEGi2Lu00b%2FeAL2ASnbu%2BaUsJzjYAcZVwTOHoC0Jb5MsIB9AGneS7CSmtOtzxDRc6BSbtu5iYAEi17p81BMZnge2GPcP%2BuwO84IoGWZM8XomBLRUvAekFdYYQLZiNJbIP2fnvjkedjMV3897Db1xvwbhSIUIynEikHdOmWQThn%2FzNFx3GMasa4jrJIEFc2WMoUpTYpqPr7py77kw1283krsistiqfQR9zIQUzbMjhqLFSyOBOgH7W8oxEMWPVRWHE0YVHSbL5S24UDdfZanA78lrbND6bu2b%2BVkfeIndn0oywiJoDOBgi9hiaiEqxyRRzni3TrBDQf2ba7vPoEI7QRry9atTX0h2IFCziz5YI2l4kc1E72OvNHoSXPGY16UA9L%2FSJHKF9T2BSiwi3RqQoQPTGwU2uCZleG10Ojqd%2BPqp4OR40VOrDsBAuC2hfO5N%2F61tmKKEk7WMioH5pwrBpA8gItAjCiAyPHKJGDO%2Bcdb6hABQAvdAwPZUSNqZACfVjTMp5sixdBXYBtxSL9ige1mXdxWCf%2BkgupT5wu2uUm2u7Q7aprjDOEqpkNfYXvV4mIWa4d2uWZUSUvgt4%2F216n8ANrDndptX4ZPCZnvXpMAHkHfkxKnxfelBiw2ltHbz5%2Bs8bLhzEikPRDyR%2B1twT9P0YiAeuGgz5sf4mCB5XtLW%2Bj%2FpRtPSeLyJcObURokroT0yUyx%2FsgIjpMGCoShgVacRdUJImO4fuAahqaTJtJB8%2FXsg%2F1XZge6P5qw81lKwtczcm%2BGLi7%2FcHMfxEWZRr%2FvM%2BcUfcx0mvmMUUbN0xc62TCF%2BNTQBjqpAXRwW1KBTNhBhZCrxDR1hSg5QMVOWJmr%2B2cgZvpaxj3bU%2FXB4Bp4srDErveLH5ZFIRmtOIpkL868jhSmCvTcTb6c8NTXKBq%2Bzk6zArcs%2Byxo1TitxL%2FtqeZRptx810PkyfX%2FPszX9oHCXpw92dxj8b6jbDhtx0o2k5Bl%2FuVAH6LclgsJ%2Fkwaok9uRitCKx8VWm8sCQ%2Fl%2BOKc9dskXsSsRIOhO3AR%2FsdlRNc%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260526T064655Z&X-Amz-SignedHeaders=host&X-Amz-Expires=3600&X-Amz-Credential=ASIA4H5P3Z2RJK63WFE4%2F20260526%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=7431296d0fc6c3af9cea240d0ead7cc406353cdffecb334427e7a701356beb09"

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