import urllib.request
import json

res = urllib.request.urlopen("http://localhost:8000/api/ledger/blocks")
data = json.loads(res.read().decode("utf-8"))
print("Stats response:", json.dumps(data.get("stats"), indent=2))
