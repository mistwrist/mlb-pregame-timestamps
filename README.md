# mlb-pregame-timestamps

MLB 경기 **전(前)** 정보가 *언제* 공개됐는지를 기록하는 수집기.

내용이 아니라 **시각**이다. "오늘 선발이 누구냐"가 아니라 "그 정보가 몇 시 몇 분에 공개됐느냐".
이 데이터는 **소급 취득이 불가능하다** — 지나가면 영원히 알 수 없어서 전향으로만 쌓인다.

## 기록하는 것

| 이벤트 | 뜻 |
|---|---|
| `probable_change` | 예고 선발이 바뀐 시각 (= 선발 스크래치) |
| `lineup_posted` | 라인업이 처음 올라온 시각 |
| `lineup_change` | 올라온 라인업이 수정된 시각 |
| `officials_posted` | 심판진이 공개된 시각 |
| `weather_update` | 지붕 개폐·날씨 정보가 갱신된 시각 |

출력: `data/lineup_timestamps/events_<날짜>.jsonl` · `data/pregame_conditions/events_<날짜>.jsonl`
(직전 스냅샷과 diff 해서 **변한 것만** append)

## 어떻게 도는가

- **소스**: [MLB StatsAPI](https://statsapi.mlb.com) — 구단 공식·공개·API 키 불필요
- **주기**: 15분 (GitHub Actions cron, ET 10:00~23:59 창)
- **시크릿**: 없음. 이 저장소는 어떤 토큰·키·비밀번호도 쓰지 않는다

## 왜 저장소가 따로인가

GitHub Actions는 **public 저장소에서 무제한 무료**다.
15분 간격 수집기는 월 ~1,700분을 쓰는데, private 저장소의 무료 한도(월 2,000분)로는 감당이 안 된다.

이 수집기는 공개 API만 쓰고 전략·모델 코드가 전혀 없어서 공개해도 잃을 게 없다.

## 수동 실행

```bash
pip install requests
python collect_lineup_timestamps.py            # 1회
python collect_lineup_timestamps.py --loop 15  # 15분 간격 상주
python collect_pregame_conditions.py
```

설치·설정은 `SETUP.md`.
