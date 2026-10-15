
Atualizar · PY
import os, json, time, datetime as dt, requests
KEY = os.environ["ODDSPAPI_KEY"]
B = "https://api.oddspapi.io/v4"
 
def get(path, **p):
    p["apiKey"] = KEY
    for i in range(3):
        r = requests.get(f"{B}/{path}", params=p, timeout=180)
        if r.status_code == 429:
            time.sleep(5 * (i + 1)); continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("limite de consultas em " + path)
 
MAP = {}
for l in open("campeonatos.txt", encoding="utf-8"):
    if "=" in l and not l.startswith("#"):
        a, b = l.split("=", 1)
        MAP[a.strip()] = b.strip()
 
if not os.path.exists("torneios.txt"):
    t = get("tournaments", sportId=10)
    open("torneios.txt", "w", encoding="utf-8").write("\n".join(
        f'{x["tournamentId"]} | {x["categoryName"]} | {x["tournamentName"]}'
        for x in t if x.get("futureFixtures", 0) > 0))
 
hoje = dt.date.today()
fx = get("fixtures", sportId=10, **{"from": str(hoje), "to": str(hoje + dt.timedelta(days=8))}) or []
nm = {f["fixtureId"]: f for f in fx}
agora = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
ids, out = list(MAP), []
for i in range(0, len(ids), 10):
    od = get("odds-by-tournaments", bookmaker="pinnacle", tournamentIds=",".join(ids[i:i + 10])) or []
    for f in od:
        if f["startTime"] <= agora or f["fixtureId"] not in nm:
            continue
        m = f.get("bookmakerOdds", {}).get("pinnacle", {}).get("markets", {}).get("101")
        if not m:
            continue
        try:
            pr = [m["outcomes"][k]["players"]["0"] for k in ("101", "102", "103")]
        except KeyError:
            continue
        if not all(p["active"] and p["price"] > 1 for p in pr):
            continue
        n = nm[f["fixtureId"]]
        out.append({"lg": MAP[str(f["tournamentId"])], "h": n["participant1Name"],
                    "a": n["participant2Name"], "t": f["startTime"], "o": [p["price"] for p in pr]})
    time.sleep(1)
json.dump({"atualizado": agora, "jogos": out}, open("jogos.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out), "jogos")

