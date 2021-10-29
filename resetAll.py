import requests, json, stats

ids = [
        "706775474419793983",
        "691598868936130591",
        "681191191479320624",
        "572533314523627530"
    ]

last_monday = "2021/10/18"
last_first= "2021/10/01"

for timeframe in ["day", "month", "week", "all"]:

    url = f"https://helperdata.glitch.me/saveAb6hcxs/tracker/{timeframe}.json"

    data = stats.getDefaultData(ids)

    if timeframe == "week":
        data["lastReloaded"] = last_monday
    if timeframe == "month":
        data["lastReloaded"] = last_first

    requests.post(url, data = {"data":json.dumps(data)})