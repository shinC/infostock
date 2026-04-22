import urllib.request
import json

futures_data = json.loads(urllib.request.urlopen("https://finviz.com/api/futures_all.ashx?timeframe=NO", timeout=5).read().decode())
cl_data = futures_data.get("CL")
print(cl_data)
if cl_data and "last" in cl_data and "prevClose" in cl_data and cl_data["prevClose"] != 0:
    change = ((cl_data["last"] - cl_data["prevClose"]) / cl_data["prevClose"]) * 100
    print("Calculated:", round(change, 2))
