#!/usr/bin/env python3
"""Fetch official ECB daily reference rates and update site JSON."""
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET

URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "ecb-rates.json"
req = urllib.request.Request(URL, headers={"User-Agent": "JiYiBi-ECB-Rates/1.0"})
with urllib.request.urlopen(req, timeout=25) as res:
    xml = res.read()
root = ET.fromstring(xml)
# Namespace-independent parsing: the ECB document contains a Cube time="YYYY-MM-DD".
day_nodes = [e for e in root.iter() if e.tag.split("}")[-1] == "Cube" and "time" in e.attrib]
if not day_nodes:
    raise ValueError("ECB response missing date")
day = day_nodes[0]
date = day.attrib["time"]
rates = {e.attrib["currency"]: float(e.attrib["rate"]) for e in day if "currency" in e.attrib and "rate" in e.attrib}
if "CNY" not in rates or not (0 < rates["CNY"] < 30):
    raise ValueError("ECB response missing valid CNY rate")
new = {"source": "ECB", "date": date, "base": "EUR", "rates": rates, "source_url": URL}
if OUT.exists():
    try:
        old = json.loads(OUT.read_text(encoding="utf-8"))
        if old.get("source") == "ECB" and old.get("date") and old["date"] > date:
            raise ValueError("ECB returned an older date: refusing downgrade")
    except json.JSONDecodeError:
        pass
OUT.write_text(json.dumps(new, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"ECB {date}: 1 EUR = {rates['CNY']} CNY")
