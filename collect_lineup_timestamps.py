# collect_lineup_timestamps.py — ★전향 수집기: 라인업 게시/프로버블 변경 '시각' 아카이빙 (2026-07-02 신설)
# 지금부터 안 쌓으면 영원히 살 수 없는 데이터(발표 타임스탬프). 소급 불가.
# 한 번 실행 = 현재 스냅샷과 직전 상태를 diff → 이벤트를 JSONL append (probable_change / lineup_posted / lineup_change)
# 배치: 로컬 작업스케줄러(10~15분 간격) 또는 GitHub Actions(드래프트 yml 동봉 — 배치는 사용자 결정)
# 사용: python collect_lineup_timestamps.py            (1회)
#       python collect_lineup_timestamps.py --loop 10  (10분 간격 상주)
import sys, os, time, json, argparse
from datetime import datetime, timezone, timedelta
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lineup_timestamps")
os.makedirs(BASE, exist_ok=True)

def et_today():
    # ET = UTC-4(서머타임 기준, 시즌 중 충분) — 정밀 tz 라이브러리 없이 보수적 처리
    return (datetime.now(timezone.utc) - timedelta(hours=4)).date().isoformat()

def snapshot(date_str):
    games = {}
    url = (f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}"
           "&hydrate=probablePitcher&fields=dates,games,gamePk,gameDate,officialDate,status,detailedState,"
           "teams,home,away,team,id,name,probablePitcher,fullName")
    r = requests.get(url, timeout=60); r.raise_for_status()
    for day in r.json().get("dates", []):
        for g in day.get("games", []):
            pk = g["gamePk"]
            h = g.get("teams", {}).get("home", {}); a = g.get("teams", {}).get("away", {})
            entry = {
                "status": (g.get("status") or {}).get("detailedState"),
                "home_probable": ((h.get("probablePitcher") or {}).get("id")),
                "away_probable": ((a.get("probablePitcher") or {}).get("id")),
                "home_lineup": [], "away_lineup": [],
            }
            try:
                b = requests.get(f"https://statsapi.mlb.com/api/v1/game/{pk}/boxscore"
                                 "?fields=teams,home,away,battingOrder", timeout=30).json()
                entry["home_lineup"] = (b.get("teams", {}).get("home", {}) or {}).get("battingOrder", []) or []
                entry["away_lineup"] = (b.get("teams", {}).get("away", {}) or {}).get("battingOrder", []) or []
            except Exception:
                pass
            games[str(pk)] = entry
            time.sleep(0.2)
    return games

def diff_and_log(date_str):
    state_path = os.path.join(BASE, f"state_{date_str}.json")
    events_path = os.path.join(BASE, f"events_{date_str}.jsonl")
    prev = {}
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            prev = json.load(f)
    cur = snapshot(date_str)
    ts = datetime.now(timezone.utc).isoformat()
    events = []
    for pk, c in cur.items():
        p = prev.get(pk)
        if p is None:
            if c["home_probable"] or c["away_probable"]:
                events.append({"ts_utc": ts, "gamePk": pk, "type": "first_seen", "payload": c})
            continue
        for side in ("home", "away"):
            if c[f"{side}_probable"] != p.get(f"{side}_probable"):
                events.append({"ts_utc": ts, "gamePk": pk, "type": "probable_change", "side": side,
                               "from": p.get(f"{side}_probable"), "to": c[f"{side}_probable"]})
            was, now = p.get(f"{side}_lineup") or [], c[f"{side}_lineup"] or []
            if not was and now:
                events.append({"ts_utc": ts, "gamePk": pk, "type": "lineup_posted", "side": side, "lineup": now})
            elif was and now and was != now:
                events.append({"ts_utc": ts, "gamePk": pk, "type": "lineup_change", "side": side,
                               "from": was, "to": now})
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False)
    if events:
        with open(events_path, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"[{ts}] games={len(cur)} events={len(events)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=int, default=0, help="N분 간격 상주 (0=1회)")
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
