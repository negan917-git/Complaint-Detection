import requests


TELEGRAM_API = "https://api.telegram.org/bot"


def validate_bot_token(token: str) -> dict:
    response = requests.get(f"{TELEGRAM_API}{token}/getMe", timeout=10)
    data = response.json()
    if not data.get("ok"):
        raise ValueError("Неверный токен Telegram-бота")
    bot_info = data["result"]
    return {
        "id": bot_info["id"],
        "first_name": bot_info.get("first_name", "Unknown"),
        "username": bot_info.get("username", ""),
    }


def get_bot_updates(token: str) -> list:
    response = requests.get(
        f"{TELEGRAM_API}{token}/getUpdates",
        timeout=15,
        params={"timeout": 5, "allowed_updates": ["message"]},
    )
    data = response.json()
    if not data.get("ok"):
        return []
    return data.get("result", [])
