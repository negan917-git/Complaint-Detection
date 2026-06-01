import os
import json
import re
import logging
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger("opencode.openai_service")

HAS_OPENAI = False

_dotenv_path = find_dotenv(usecwd=True)
if _dotenv_path:
    load_dotenv(_dotenv_path)
else:
    load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    HAS_OPENAI = True

if not HAS_OPENAI:
    logger.warning("OPENAI_API_KEY не задан — используется локальный анализатор")


def analyze_message(text: str) -> dict:
    if HAS_OPENAI:
        try:
            return _openai_analyze(text)
        except Exception as e:
            logger.error("OpenAI анализ упал: %s", e, exc_info=True)
    return _local_analyzer(text)


def _openai_analyze(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("Текст сообщения пустой")

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    logger.info("Отправка запроса в OpenAI (gpt-4o-mini), длина текста: %d символов", len(text))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a message analyzer. Analyze the user's message and return a JSON object. "
                    "The JSON must have EXACTLY these fields (no extra fields, no markdown):\n"
                    '  "sentiment": "positive" | "negative" | "neutral",\n'
                    '  "emotion": "joy" | "anger" | "sadness" | "fear" | "neutral",\n'
                    '  "complaint": true | false,\n'
                    '  "priority": "high" | "medium" | "low",\n'
                    '  "category": "general" | "technical" | "complaint" | "support" | "other",\n'
                    '  "summary": "1-2 short sentences describing the message essence in Russian"\n'
                    "The analysis must depend on the actual message content. "
                    "Do NOT return default/hardcoded values. Return ONLY the JSON object."
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0.3,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    logger.info("Ответ OpenAI (raw): %s", raw)

    raw = re.sub(r"(?is)^.*?```(?:json)?\s*", "", raw)
    raw = re.sub(r"(?is)\s*```.*$", "", raw)
    raw = raw.strip()

    if not raw:
        raise ValueError("OpenAI вернул пустой ответ")

    result = json.loads(raw)

    if "is_complaint" in result and "complaint" not in result:
        result["complaint"] = result.pop("is_complaint")

    logger.info("Анализ завершён: sentiment=%s, emotion=%s, complaint=%s",
                result.get("sentiment"), result.get("emotion"), result.get("complaint"))
    return result


def _local_analyzer(text: str) -> dict:
    text_lower = text.lower()

    negative_words = [
        "ужасн", "плох", "не работ", "ошибк", "зависа", "проблем", "сломал",
        "не могу", "почему", "вернит", "жалоб", "грузит", "гавно", "ужас",
        "фу", "отвратит", "не нравит", "разочар",
    ]
    positive_words = [
        "спасиб", "отличн", "супер", "лучш", "класс", "хорош", "нравит",
        "прекрасн", "круто", "молодц", "довол", "благодар",
    ]
    complaint_words = ["вернит", "возврат", "жалоб", "ошибк", "не работ", "проблем", "деньги"]

    negative_score = sum(1 for w in negative_words if w in text_lower)
    positive_score = sum(1 for w in positive_words if w in text_lower)

    if negative_score > positive_score:
        sentiment = "negative"
    elif positive_score > negative_score:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    if sentiment == "negative":
        if any(w in text_lower for w in ["ужасн", "фу", "отвратит"]):
            emotion = "angry"
        elif any(w in text_lower for w in ["зависа", "ошибк", "не работ", "проблем"]):
            emotion = "frustrated"
        elif any(w in text_lower for w in ["почему", "не могу"]):
            emotion = "confused"
        else:
            emotion = "frustrated"
    elif sentiment == "positive":
        if any(w in text_lower for w in ["спасиб", "благодар"]):
            emotion = "happy"
        else:
            emotion = "happy"
    else:
        emotion = "neutral"

    is_complaint = any(w in text_lower for w in complaint_words) and sentiment == "negative"

    if "деньг" in text_lower or "цен" in text_lower or "стоим" in text_lower:
        category = "billing"
    elif "установ" in text_lower or "настрой" in text_lower:
        category = "service"
    elif "сайт" in text_lower or "приложен" in text_lower or "зависа" in text_lower:
        category = "technical"
    elif "возврат" in text_lower or "заказ" in text_lower:
        category = "product"
    elif "аккаунт" in text_lower or "вход" in text_lower:
        category = "account"
    elif "помог" in text_lower or "подскаж" in text_lower:
        category = "support"
    else:
        category = "general"

    if is_complaint:
        priority = "high"
    elif sentiment == "negative":
        priority = "medium"
    else:
        priority = "low"

    summary = f"Пользователь {'жалуется на' if is_complaint else 'пишет о'} проблеме." if sentiment == "negative" else "Пользователь оставил положительный отзыв."
    if sentiment == "neutral":
        summary = "Пользователь задает вопрос."

    return {
        "sentiment": sentiment,
        "emotion": emotion,
        "complaint": is_complaint,
        "priority": priority,
        "category": category,
        "summary": summary,
    }
