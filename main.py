import os
import textwrap
from datetime import datetime, timezone
from typing import Dict, List

import requests
from openai import OpenAI

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
MAX_ARTICLES_PER_COUNTRY = int(os.getenv("MAX_ARTICLES_PER_COUNTRY", "8"))

COUNTRIES = {
    "kr": {"label": "한국", "lang": "ko"},
    "au": {"label": "호주", "lang": "en"},
    "us": {"label": "미국", "lang": "en"},
}

TOPIC_QUERIES = [
    'economy OR inflation OR central bank OR rates OR jobs OR election OR parliament OR policy OR trade',
    'market OR recession OR budget OR tax OR tariffs OR diplomacy OR regulation',
]


def require_env() -> None:
    missing = []
    for key, value in {
        "GNEWS_API_KEY": GNEWS_API_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }.items():
        if not value:
            missing.append(key)
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


def fetch_country_news(country_code: str, lang: str) -> List[Dict[str, str]]:
    articles: List[Dict[str, str]] = []
    seen_urls = set()

    for query in TOPIC_QUERIES:
        params = {
            "q": query,
            "country": country_code,
            "lang": lang,
            "max": MAX_ARTICLES_PER_COUNTRY,
            "apikey": GNEWS_API_KEY,
        }
        resp = requests.get("https://gnews.io/api/v4/search", params=params, timeout=30)
        resp.raise_for_status()
        payload = resp.json()

        for item in payload.get("articles", []):
            url = item.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            articles.append(
                {
                    "title": item.get("title", "").strip(),
                    "description": item.get("description", "").strip(),
                    "source": item.get("source", {}).get("name", "").strip(),
                    "publishedAt": item.get("publishedAt", "").strip(),
                    "url": url,
                }
            )
            if len(articles) >= MAX_ARTICLES_PER_COUNTRY:
                return articles
    return articles


def build_news_block(country_label: str, articles: List[Dict[str, str]]) -> str:
    if not articles:
        return f"[{country_label}] 관련 기사를 가져오지 못했습니다."

    lines = [f"[{country_label}]"]
    for idx, article in enumerate(articles, start=1):
        lines.append(
            textwrap.dedent(
                f"""
                {idx}. 제목: {article['title']}
                   요약: {article['description']}
                   매체: {article['source']}
                   발행: {article['publishedAt']}
                   링크: {article['url']}
                """
            ).strip()
        )
    return "\n".join(lines)


def generate_digest(all_news: Dict[str, List[Dict[str, str]]]) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    compiled_news = "\n\n".join(
        build_news_block(COUNTRIES[country]["label"], articles)
        for country, articles in all_news.items()
    )

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    prompt = f"""
너는 신중하고 균형 잡힌 뉴스 브리핑 에디터다.
아래 기사 목록만 바탕으로 한국어 뉴스 요약본을 만들어라.

중요 규칙:
- 없는 사실을 추가하지 말 것.
- 각 나라별로 경제/시사 핵심만 3개 이내로 압축할 것.
- 좌/우 의견은 '사실 판정'이 아니라, 같은 이슈를 두고 보통 진보 진영과 보수 진영이 각각 어떤 포인트를 강조할지 정리할 것.
- 과장, 선동, 확정적 표현을 피할 것.
- 맨 마지막에 '이 브리핑은 기사 목록 기반 요약이며, 좌/우 관점은 전형적 프레이밍 비교입니다.' 문장을 넣을 것.

원하는 출력 형식:
# 오늘의 경제·시사 브리핑 ({now_utc})

## 한눈에 보기
- 오늘 전체 흐름 4~6줄

## 한국
- 핵심 1
- 핵심 2
- 핵심 3
- 진보 성향에서 강조할 포인트:
- 보수 성향에서 강조할 포인트:

## 호주
(같은 형식)

## 미국
(같은 형식)

## 나라별 공통 흐름
- 세 나라를 함께 봤을 때 공통 이슈 3~5개

## 투자·생활 관점
- 환율/금리/물가/고용/주식시장 관점에서 실생활 영향 3~5개

기사 목록:
{compiled_news}
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
    )
    return response.output_text.strip()


def send_telegram_message(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()


def split_message(text: str, limit: int = 3500) -> List[str]:
    chunks = []
    current = []
    current_len = 0

    for line in text.splitlines(True):
        if current_len + len(line) > limit and current:
            chunks.append("".join(current))
            current = [line]
            current_len = len(line)
        else:
            current.append(line)
            current_len += len(line)

    if current:
        chunks.append("".join(current))
    return chunks


def main() -> None:
    require_env()

    all_news: Dict[str, List[Dict[str, str]]] = {}
    for country_code, meta in COUNTRIES.items():
        articles = fetch_country_news(country_code=country_code, lang=meta["lang"])
        all_news[country_code] = articles

    digest = generate_digest(all_news)
    for chunk in split_message(digest):
        send_telegram_message(chunk)


if __name__ == "__main__":
    main()
