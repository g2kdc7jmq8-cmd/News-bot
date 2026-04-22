# Daily global news digest bot

이 프로젝트는 매일 아침 텔레그램으로 아래 형식의 브리핑을 보내도록 만든 Python 스크립트입니다.

- 한국 / 호주 / 미국 3개국 뉴스
- 경제 + 시사 중심
- 나라별 핵심 요약
- 진보 성향에서 보통 강조하는 포인트
- 보수 성향에서 보통 강조하는 포인트
- 공통 흐름 + 실생활 영향 정리

## 1) 준비물

- GitHub 계정
- GNews API 키
- OpenAI API 키
- Telegram Bot Token
- Telegram Chat ID

## 2) 텔레그램 설정

1. Telegram에서 `@BotFather` 검색
2. `/newbot` 입력
3. 봇 토큰 복사
4. 만든 봇에게 아무 메시지나 하나 보내기
5. 아래 주소를 브라우저에 넣어 Chat ID 확인

```text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

응답 JSON 안의 `chat.id` 값을 저장하면 됩니다.

## 3) GitHub 업로드

이 폴더 전체를 새 GitHub 저장소에 올립니다.

## 4) GitHub Secrets 추가

Repository → Settings → Secrets and variables → Actions → New repository secret

아래 5개를 추가하세요.

- `OPENAI_API_KEY`
- `OPENAI_MODEL` → 보통 `gpt-5`
- `GNEWS_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## 5) 실행 시간

`.github/workflows/daily_news.yml` 안에서 기본값은 브리즈번 시간 오전 7시입니다.

```yaml
cron: "0 7 * * *"
timezone: "Australia/Brisbane"
```

시간을 바꾸고 싶으면 숫자만 바꾸면 됩니다.
예: 오후 8시는 `0 20 * * *`

## 6) 커스터마이즈

`main.py`에서 수정 가능:

- 나라 추가/삭제
- 기사 수 변경
- 프롬프트 문구 변경
- 경제 비중 더 높이기
- 좌/우 비교 문체 더 짧게 만들기

## 7) 주의

- 이 코드는 기사 원문 전체를 읽는 게 아니라 기사 목록 기반 브리핑입니다.
- 좌/우 비교는 사실 판정이 아니라 프레이밍 차이 요약입니다.
- 정치 성향 분류는 언제나 완벽하지 않으니 참고용으로 보세요.
