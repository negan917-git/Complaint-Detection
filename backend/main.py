import os
import sys
import logging
if not __package__:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    __package__ = "backend"

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import engine, Base, get_db
from backend.models import Bot, Message, User
from backend.schemas import (
    MessageCreate, MessageOut, BotCreate, BotOut, BotConnectRequest,
    DashboardOut, AnalyzeRequest, AnalyzeResponse, AnalyticsOut,
    UserCreate, UserOut, LoginRequest, Token,
)
from backend.crud import (
    get_dashboard, get_messages, create_message,
    get_bots, create_bot, delete_bot, sync_bot_messages, get_analytics,
    connect_telegram_bot,
)
from backend.services.openai_service import analyze_message, test_openai_connection, HAS_OPENAI, OPENAI_API_KEY
from backend.services.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
import random
import re

Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(title="Complaint Detection")

log = logging.getLogger("opencode.api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    log.error("Unhandled exception: %s | %s", exc, type(exc).__name__, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Внутренняя ошибка сервера: {type(exc).__name__}"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@app.post("/api/auth/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if not data.email or not EMAIL_RE.match(data.email):
        raise HTTPException(status_code=400, detail="Некорректный формат email")
    if not data.password or len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Пароль должен быть минимум 6 символов")
    if not data.username or len(data.username.strip()) == 0:
        raise HTTPException(status_code=400, detail="Имя пользователя обязательно")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
    user = User(
        username=data.username.strip(),
        email=data.email.strip().lower(),
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    if not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Email и пароль обязательны")
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token)


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/api/dashboard", response_model=DashboardOut)
def api_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_dashboard(db, user_id=current_user.id)


@app.get("/api/messages", response_model=list[MessageOut])
def api_messages(
    q: str = Query(None),
    sentiment: str = Query(None),
    priority: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_messages(db, user_id=current_user.id, q=q, sentiment=sentiment, priority=priority)


@app.post("/api/messages", response_model=MessageOut)
def api_create_message(data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_message(db, data, user_id=current_user.id)


@app.get("/api/bots", response_model=list[BotOut])
def api_bots(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_bots(db, user_id=current_user.id)


@app.post("/api/bots", response_model=BotOut)
def api_create_bot(data: BotCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_bot(db, data, user_id=current_user.id)


@app.post("/api/bots/connect", response_model=BotOut)
def api_connect_bot(data: BotConnectRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        return connect_telegram_bot(db, data.token, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/bots/{bot_id}/sync")
def api_sync_bot(bot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = sync_bot_messages(db, bot_id, user_id=current_user.id)
    return {"messages_synced": len(messages), "messages": [MessageOut.model_validate(m).model_dump() for m in messages]}


@app.delete("/api/bots/{bot_id}")
def api_delete_bot(bot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not delete_bot(db, bot_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"ok": True}


@app.get("/api/analytics")
def api_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_analytics(db, user_id=current_user.id)


@app.post("/api/analyze", response_model=AnalyzeResponse)
def api_analyze(data: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    log = logging.getLogger("opencode.api")
    log.info("Анализ сообщения от user %d: %.80s | HAS_OPENAI=%s",
             current_user.id, data.text, HAS_OPENAI)
    try:
        result = analyze_message(data.text)
        log.info("Результат: sentiment=%s emotion=%s analyzer=%s",
                 result.get("sentiment"), result.get("emotion"), result.get("analyzer"))
        return result
    except Exception as e:
        log.error("Критическая ошибка анализа: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@app.get("/api/debug/openai")
def debug_openai():
    return test_openai_connection()


@app.delete("/api/messages/clear")
def api_clear_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Message).filter(Message.user_id == current_user.id).delete()
    db.query(Bot).filter(Bot.user_id == current_user.id).update({"messages_count": 0})
    db.commit()
    return {"ok": True}


@app.delete("/api/bots/clear")
def api_clear_bots(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Message).filter(Message.user_id == current_user.id).delete()
    db.query(Bot).filter(Bot.user_id == current_user.id).delete()
    db.commit()
    return {"ok": True}


@app.post("/api/seed")
def api_seed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid = current_user.id
    existing_bot = db.query(Bot).filter(Bot.user_id == uid).first()
    if not existing_bot:
        bot = Bot(user_id=uid, name="Complaint Detection", username="complaint_detection_bot", status="connected")
        db.add(bot)
        db.commit()
        db.refresh(bot)
    else:
        bot = existing_bot

    sample_messages = [
        ("Анна", "Ваш сервис работает ужасно, ничего не грузится!", "negative", "frustrated", True, "high", "technical"),
        ("Иван", "Спасибо за помощь, вы лучшие!", "positive", "happy", False, "low", "support"),
        ("Петр", "Когда будет обновление? Жду уже неделю.", "negative", "frustrated", False, "medium", "general"),
        ("Мария", "Не могу войти в аккаунт, пишет ошибку.", "negative", "frustrated", True, "high", "technical"),
        ("Ольга", "Отличный бот, всё нравится!", "positive", "happy", False, "low", "general"),
        ("Сергей", "Почему списали деньги дважды? Верните!", "negative", "angry", True, "high", "billing"),
        ("Елена", "Подскажите, как настроить уведомления?", "neutral", "neutral", False, "low", "service"),
        ("Дмитрий", "Всё супер, спасибо за работу!", "positive", "happy", False, "low", "general"),
        ("Алексей", "Приложение зависает при запуске.", "negative", "frustrated", True, "high", "technical"),
        ("Наталья", "Хочу оформить возврат товара.", "neutral", "neutral", True, "medium", "product"),
        ("Максим", "Новый дизайн просто ужасный!", "negative", "angry", True, "high", "general"),
        ("Татьяна", "Спасибо, разобрался. Всё работает.", "positive", "happy", False, "low", "support"),
        ("Владимир", "Не приходит код подтверждения на почту.", "negative", "frustrated", True, "high", "technical"),
        ("Юлия", "Где найти историю заказов?", "neutral", "confused", False, "low", "account"),
        ("Артем", "Вы лучший сервис поддержки!", "positive", "happy", False, "low", "support"),
        ("Ксения", "Игра не запускается после последнего обновления.", "negative", "frustrated", True, "high", "technical"),
        ("Роман", "Как сменить тарифный план?", "neutral", "neutral", False, "low", "billing"),
        ("Алина", "Бот не отвечает на команды.", "negative", "frustrated", True, "medium", "technical"),
        ("Виктор", "Очень доволен вашим сервисом!", "positive", "happy", False, "low", "general"),
        ("Евгения", "Сделайте тёмную тему, пожалуйста.", "neutral", "neutral", False, "low", "general"),
        ("Данил", "Какой-то непонятный баг, всё сломалось", "negative", "confused", True, "high", "technical"),
        ("Глеб", "Ахуенный сервис, красавчики!", "positive", "happy", False, "low", "general"),
        ("Гоша", "Всё пиздато, но можно лучше", "positive", "happy", False, "medium", "general"),
        ("Илья", "Где деньги, Лебовски?", "negative", "angry", True, "high", "billing"),
        ("Дима", "Почему бот тормозит?", "negative", "frustrated", False, "medium", "technical"),
        ("Даша", "Спасибо большое за консультацию!", "positive", "happy", False, "low", "support"),
        ("Катя", "Не могу открыть файл во вложении", "negative", "confused", True, "medium", "technical"),
        ("Лена", "Как привязать карту?", "neutral", "neutral", False, "low", "billing"),
        ("Павел", "Вы охуенно работаете, ребята!", "positive", "happy", False, "low", "general"),
        ("Света", "Уже третью неделю жду ответа", "negative", "frustrated", True, "high", "support"),
        ("Никита", "Идеально, спасибо!", "positive", "happy", False, "low", "general"),
        ("Алиса", "Дизайн стал хуже, верните как было", "negative", "angry", True, "high", "general"),
        ("Вера", "Не отправляется форма обратной связи", "negative", "frustrated", True, "high", "technical"),
        ("Костя", "Лучший бот из всех, что я видел", "positive", "happy", False, "low", "general"),
    ]

    count = 0
    for name, text, sentiment, emotion, complaint, priority, category in sample_messages:
        summary_map = {
            "negative": "Пользователь жалуется на проблему.",
            "positive": "Пользователь оставил положительный отзыв.",
            "neutral": "Пользователь задает вопрос.",
        }
        msg = Message(
            user_id=uid,
            name=name,
            username=bot.username,
            text=text,
            summary=summary_map.get(sentiment, ""),
            sentiment=sentiment,
            emotion=emotion,
            complaint=complaint,
            priority=priority,
            category=category,
        )
        db.add(msg)
        count += 1

    bot.messages_count = (
        db.query(func.count(Message.id)).filter(Message.user_id == uid, Message.username == bot.username).scalar()
    )
    db.commit()
    return {"seeded": count, "total_messages": bot.messages_count}


@app.get("/api/generate-demo")
def api_generate_demo(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    uid = current_user.id
    texts = [
        "Ваш сервис работает ужасно, ничего не грузится!",
        "Спасибо за помощь, вы лучшие!",
        "Когда будет обновление? Жду уже неделю.",
        "Не могу войти в аккаунт, пишет ошибку.",
        "Отличный бот, всё нравится!",
        "Почему списали деньги дважды? Верните!",
        "Подскажите, как настроить уведомления?",
        "Всё супер, спасибо за работу!",
        "Уже третью неделю жду ответа",
        "Идеально, всё работает отлично!",
    ]
    names = ["Анна", "Иван", "Петр", "Мария", "Ольга"]
    bot = db.query(Bot).filter(Bot.user_id == uid).first()
    if not bot:
        bot = Bot(user_id=uid, name="Complaint Detection", username="complaint_detection_bot", status="connected")
        db.add(bot)
        db.commit()
        db.refresh(bot)
    created = []
    for text in texts:
        result = analyze_message(text)
        msg = Message(
            user_id=uid,
            name=random.choice(names),
            username=bot.username,
            text=text,
            summary=result["summary"],
            sentiment=result["sentiment"],
            emotion=result["emotion"],
            priority=result["priority"],
            category=result["category"],
            complaint=result["complaint"],
        )
        db.add(msg)
        created.append(msg)
    bot.messages_count = (bot.messages_count or 0) + len(created)
    db.commit()
    return {"generated": len(created), "messages": [MessageOut.model_validate(m).model_dump() for m in created]}


api_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.isdir(api_dir):
    app.mount("/", StaticFiles(directory=api_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
