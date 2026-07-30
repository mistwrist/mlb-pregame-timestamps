# collect_pregame_conditions.py — ★전향 수집기 2호: 지붕/날씨·심판 배정의 '공개 시각' (2026-07-02 신설, §7-E)
# 오늘 경기들의 feed/live를 폴링해 gameData.weather(지붕 개폐 포함)와 심판진(officials) '첫 등장/변경' 시각을 JSONL로.
# game_conditions(사후 확정값)와 달리 이건 경기 前 타임라인 — 소급 불가 데이터.
# 사용: python collect_pregame_conditions.py            (1회)
#       python collect_pregame_conditions.py --loop 20  (20분 간격 상주)
import sys, os, time, json, argparse
from datetime import datetime, timezone, timedelta
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pregame_conditions")
os.makedirs(BASE, exist_ok=True)

def et_today():
    return (datetime.now(timezone.utc) - timedelta(hours=4)).date().isoformat()

FIELDS = ("gamePk,gameData,weather,condition,temp,wind,datetime,officialDate,status,detailedState,"
          "liveData,boxscore,officials,official,fullName,officialType")

def snapshot(date_str):
    r = requests.get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
                     "&fields=dates,games,gamePk,status,detailedState", timeout=60)
    pks = [g["gamePk"] for d in r.json().get("dates", []) for g in d.get("games", [])
           if (g.get("status") or {}).get("detailedState") not in ("Final", "Game Over")]
    out = {}
    for pk in pks:
        try:
            j = requests.get(f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live?fields={FIELDS}",
                             timeout=30).json()
            gd = j.get("gameData") or {}
            w = gd.get("weather") or {}
            offs = ((j.get("liveData") or {}).get("boxscore") or {}).get("officials") or []
            out[str(pk)] = {
                "weather": {"condition": w.get("condition"), "temp": w.get("temp"), "wind": w.get("wind")},
                "officials": [{"name": (o.get("official") or {}).get("fullName"),
                               "type": o.get("officialType")} for o in offs],
            }
        except Exception:
            pass
        time.sleep(0.2)
    return out

def diff_and_log(date_str):
    state_p = os.path.join(BASE, f"state_{date_str}.json")
    events_p = os.path.join(BASE, f"events_{date_str}.jsonl")
    prev = {}
    if os.path.exists(state_p):
        with open(state_p, encoding="utf-8") as f:
            prev = json.load(f)
    cur = snapshot(date_str)
    ts = datetime.now(timezone.utc).isoformat()
    events = []
    for pk, c in cur.items():
        p = prev.get(pk, {})
        if c["weather"] != p.get("weather") and any(c["weather"].values()):
            events.append({"ts_utc": ts, "gamePk": pk, "type": "weather_update",
                           "from": p.get("weather"), "to": c["weather"]})
        if c["officials"] and c["officials"] != p.get("officials"):
            events.append({"ts_utc": ts, "gamePk": pk, "type": "officials_posted" if not p.get("officials") else "officials_change",
                           "officials": c["officials"]})
    with open(state_p, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False)
    if events:
        with open(events_p, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"[{ts}] games={len(cur)} events={len(events)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=0)
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    while True:
        try:
            diff_and_log(a.date or et_today())
        except Exception as e:
            print(f"[ERR] {e}")
        if not a.loop:
            break
        time.sleep(a.loop * 60)
