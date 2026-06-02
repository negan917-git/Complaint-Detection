import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import Bot, Message
from backend.schemas import BotCreate, MessageCreate
from datetime import datetime, timedelta
import random
from backend.services.telegram_service import validate_bot_token, get_bot_updates
from backend.services.encryption import encrypt_token, decrypt_token
from backend.services.openai_service import analyze_message

logger = logging.getLogger("opencode.crud")


def get_dashboard(db: Session, user_id: int):
    base = db.query(Message).filter(Message.user_id == user_id)
    total = base.with_entities(func.count(Message.id)).scalar() or 0
    negative = base.filter(Message.sentiment == "negative").with_entities(func.count(Message.id)).scalar() or 0
    complaints = base.filter(Message.complaint == True).with_entities(func.count(Message.id)).scalar() or 0
    active_bots = (
        db.query(func.count(Bot.id))
        .filter(Bot.user_id == user_id, Bot.status == "connected")
        .scalar() or 0
    )
    negative_percent = round((negative / total * 100), 1) if total else 0
    return {
        "total_messages": total,
        "negative_percent": negative_percent,
        "complaints": complaints,
        "active_bots": active_bots,
    }


def connect_telegram_bot(db: Session, token: str, user_id: int):
    bot_data = validate_bot_token(token)
    telegram_id = bot_data["id"]
    existing = db.query(Bot).filter(Bot.telegram_bot_id == telegram_id).first()
    if existing:
        raise ValueError("Этот бот уже добавлен")
    encrypted = encrypt_token(token)
    bot = Bot(
        user_id=user_id,
        telegram_bot_id=telegram_id,
        name=bot_data["first_name"],
        username=bot_data["username"],
        token=encrypted,
        status="connected",
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


def get_messages(db: Session, user_id: int, q: str = None, sentiment: str = None, priority: str = None):
    query = db.query(Message).filter(Message.user_id == user_id)
    if q:
        query = query.filter(Message.text.ilike(f"%{q}%"))
    if sentiment and sentiment != "all":
        query = query.filter(Message.sentiment == sentiment)
    if priority and priority != "all":
        query = query.filter(Message.priority == priority)
    return query.order_by(Message.created_at.desc()).all()


def create_message(db: Session, data: MessageCreate, user_id: int):
    msg = Message(**data.model_dump(), user_id=user_id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_bots(db: Session, user_id: int):
    return db.query(Bot).filter(Bot.user_id == user_id).all()


def create_bot(db: Session, data: BotCreate, user_id: int):
    bot = Bot(name=data.name, username=data.username, status="connected", user_id=user_id)
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


def delete_bot(db: Session, bot_id: int, user_id: int):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == user_id).first()
    if bot:
        db.query(Message).filter(Message.username == bot.username, Message.user_id == user_id).delete()
        db.delete(bot)
        db.commit()
        return True
    return False


def sync_bot_messages(db: Session, bot_id: int, user_id: int):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == user_id).first()
    if not bot:
        return []
    if bot.token:
        raw_token = decrypt_token(bot.token)
        if not raw_token:
            logger.error("Не удалось расшифровать токен бота %d", bot.id)
            return []
        try:
            updates = get_bot_updates(raw_token)
        except Exception as e:
            logger.error("Ошибка получения обновлений для бота %d: %s", bot.id, e)
            updates = []
        new_messages = []
        for update in updates:
            msg_data = update.get("message", {})
            text = msg_data.get("text", "")
            if not text:
                continue
            from_user = msg_data.get("from", {})
            name = from_user.get("first_name", "User") or "User"
            username = from_user.get("username", "")
            logger.info("Анализ сообщения от @%s: %.80s", username, text)
            result = analyze_message(text)
            logger.debug("Результат анализа: %s", result)
            msg = Message(
                user_id=user_id,
                name=name,
                username=username,
                text=text,
                summary=result.get("summary", ""),
                sentiment=result.get("sentiment", "neutral"),
                emotion=result.get("emotion", "neutral"),
                priority=result.get("priority", "medium"),
                category=result.get("category", "general"),
                complaint=result.get("complaint", False),
            )
            db.add(msg)
            new_messages.append(msg)
        bot.messages_count = (bot.messages_count or 0) + len(new_messages)
        db.commit()
        for msg in new_messages:
            db.refresh(msg)
        return new_messages
    sample_texts = [
        "Ваш сервис работает ужасно, ничего не грузится!",
        "Спасибо за помощь, вы лучшие!",
        "Когда будет обновление? Жду уже неделю.",
        "Не могу войти в аккаунт, пишет ошибку.",
        "Отличный бот, всё нравится!",
    ]
    sentiments = ["positive", "negative", "neutral"]
    emotions = ["happy", "neutral", "confused", "frustrated", "angry"]
    categories = ["general", "support", "service", "technical", "billing", "product", "account"]
    priorities = ["low", "medium", "high"]
    new_messages = []
    count = random.randint(3, 5)
    for _ in range(count):
        text = random.choice(sample_texts)
        sentiment = random.choice(sentiments)
        emotion = random.choice(emotions)
        category = random.choice(categories)
        priority = random.choice(priorities)
        complaint = sentiment == "negative" and random.random() > 0.3
        summary = f"AI summary: {text[:50]}..."
        msg = Message(
            user_id=user_id,
            name=bot.name,
            username=bot.username,
            text=text,
            summary=summary,
            sentiment=sentiment,
            emotion=emotion,
            priority=priority,
            category=category,
            complaint=complaint,
        )
        db.add(msg)
        new_messages.append(msg)
    bot.messages_count = (bot.messages_count or 0) + count
    db.commit()
    for msg in new_messages:
        db.refresh(msg)
    return new_messages


def get_analytics(db: Session, user_id: int):
    base = db.query(Message).filter(Message.user_id == user_id)
    total = base.with_entities(func.count(Message.id)).scalar() or 0
    negative = base.filter(Message.sentiment == "negative").with_entities(func.count(Message.id)).scalar() or 0
    complaints = base.filter(Message.complaint == True).with_entities(func.count(Message.id)).scalar() or 0
    top_emotion_row = (
        base.with_entities(Message.emotion, func.count(Message.id).label("cnt"))
        .group_by(Message.emotion)
        .order_by(func.count(Message.id).desc())
        .first()
    )
    top_emotion = top_emotion_row[0] if top_emotion_row else "neutral"
    negative_share = round((negative / total * 100), 1) if total else 0
    complaint_share = round((complaints / total * 100), 1) if total else 0

    today = datetime.utcnow()
    daily_data = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        total_day = (
            base.with_entities(func.count(Message.id))
            .filter(Message.created_at >= day_start, Message.created_at < day_end)
            .scalar() or 0
        )
        neg_day = (
            base.with_entities(func.count(Message.id))
            .filter(
                Message.sentiment == "negative",
                Message.created_at >= day_start,
                Message.created_at < day_end,
            )
            .scalar() or 0
        )
        daily_data.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "total": total_day,
            "negative": neg_day,
        })

    top_complaints_rows = (
        base.with_entities(Message.text, func.count(Message.id).label("cnt"))
        .filter(Message.complaint == True)
        .group_by(Message.text)
        .order_by(func.count(Message.id).desc())
        .limit(5)
        .all()
    )
    top_complaints = [{"text": r[0][:60], "count": r[1]} for r in top_complaints_rows]

    categories_rows = (
        base.with_entities(Message.category, func.count(Message.id).label("cnt"))
        .group_by(Message.category)
        .order_by(func.count(Message.id).desc())
        .all()
    )
    total_cat = sum(r[1] for r in categories_rows) or 1
    categories = [
        {"name": r[0], "count": r[1], "percent": round((r[1] / total_cat * 100), 0)}
        for r in categories_rows
    ]

    return {
        "total_analyzed": total,
        "negative_share": negative_share,
        "complaint_share": complaint_share,
        "top_emotion": top_emotion,
        "daily_data": daily_data,
        "top_complaints": top_complaints,
        "categories": categories,
    }
