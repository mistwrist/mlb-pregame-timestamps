# 설정 — 한 번만 확인하면 된다

저장소는 이미 만들어져 있고 코드도 올라가 있다. **남은 건 아래 1번 하나뿐이다.**

## 1. ⚠️ 봇이 커밋할 수 있게 권한 열기 (필수)

```
Settings → Actions → General → 맨 아래 Workflow permissions
  → "Read and write permissions" 선택 → Save
```

새 저장소는 기본이 **읽기 전용**이라, 이걸 안 바꾸면 수집기가 데이터를 못 올리고
`push 실패` 에러로 끝난다. (에러가 뜨도록 일부러 만들어 뒀다 — 조용히 실패하지 않는다.)

## 2. 동작 확인

```
Actions 탭 → mlb-collectors → Run workflow (수동 1회)
```

초록 체크가 뜨고 `data/` 폴더에 JSONL이 생기면 끝. 이후 **15분 간격 자동**.

## 3. 데이터 쓰는 법

```bash
git clone https://github.com/mistwrist/mlb-pregame-timestamps.git
# data/lineup_timestamps/events_<날짜>.jsonl
# data/pregame_conditions/events_<날짜>.jsonl
```

각 줄이 이벤트 하나이고 UTC 타임스탬프가 붙어 있다.

## 참고

- **PC가 꺼져 있어도 24시간 수집된다.** 이게 이 저장소를 만든 이유다
- public 저장소라 Actions 분 소모가 **무제한 무료** — 다른 저장소 할당량에 영향 0
- 로컬에서 `--loop`로 병행 실행해도 무해하다(이벤트는 타임스탬프로 중복 제거 가능)
- 수집이 멈추면 `data/`의 최신 날짜가 밀린다. 그것만 보면 바로 안다
