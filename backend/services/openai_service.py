import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def analyze_message(text: str) -> dict:
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a message analyzer. Analyze the following message and return a JSON object "
                            "with these fields: sentiment (positive/negative/neutral), "
                            "emotion (happy/neutral/confused/frustrated/angry), "
                            "complaint (true/false), priority (low/medium/high), "
                            "category (general/support/service/technical/billing/product/account), "
                            "summary (short summary in Russian). "
                            "Return ONLY valid JSON."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception:
            pass
    return _local_analyzer(text)


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
