import re
import logging
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError as ReqConnectionError

logger = logging.getLogger("opencode.telegram")

TELEGRAM_API = "https://api.telegram.org/bot"

TOKEN_RE = re.compile(r"^\d+:[a-zA-Z0-9_-]+$")


def validate_bot_token(token: str) -> dict:
    if not TOKEN_RE.match(token):
        raise ValueError(
            "Некорректный формат токена. Токен должен выглядеть как 123456789:ABCdef..."
        )
    try:
        response = requests.get(f"{TELEGRAM_API}{token}/getMe", timeout=15)
        data = response.json()
    except Timeout:
        logger.error("Timeout при проверке токена")
        raise ValueError(
            "Таймаут при проверке токена. Сервер Telegram не ответил за 15 секунд."
        )
    except ReqConnectionError:
        logger.error("Ошибка подключения к Telegram API")
        raise ValueError(
            "Не удалось подключиться к Telegram API. Проверьте интернет-соединение сервера."
        )
    except RequestException as e:
        logger.error("Ошибка запроса к Telegram API: %s", e)
        raise ValueError(f"Ошибка при проверке токена: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error("Неизвестная ошибка при проверке токена: %s", e)
        raise ValueError(f"Неизвестная ошибка при проверке токена: {e}")

    if not data.get("ok"):
        error_desc = data.get("description", "Неверный токен Telegram-бота")
        raise ValueError(error_desc)

    bot_info = data["result"]
    return {
        "id": bot_info["id"],
        "first_name": bot_info.get("first_name", "Unknown"),
        "username": bot_info.get("username", ""),
    }


def get_bot_updates(token: str) -> list:
    try:
        response = requests.get(
            f"{TELEGRAM_API}{token}/getUpdates",
            timeout=15,
            params={"timeout": 5, "allowed_updates": ["message"]},
        )
        data = response.json()
        if not data.get("ok"):
            return []
        return data.get("result", [])
    except Exception as e:
        logger.error("Ошибка получения обновлений для бота: %s", e)
        return []
