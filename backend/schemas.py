from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    text: str
    summary: Optional[str] = None
    sentiment: Optional[str] = "neutral"
    emotion: Optional[str] = "neutral"
    priority: Optional[str] = "medium"
    category: Optional[str] = "general"
    complaint: Optional[bool] = False


class MessageOut(BaseModel):
    id: int
    name: Optional[str]
    username: Optional[str]
    text: str
    summary: Optional[str]
    sentiment: str
    emotion: str
    priority: str
    category: str
    complaint: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BotConnectRequest(BaseModel):
    token: str


class BotCreate(BaseModel):
    name: str
    username: str


class BotOut(BaseModel):
    id: int
    telegram_bot_id: int | None = None
    name: str
    username: str
    status: str
    messages_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    total_messages: int
    negative_percent: float
    complaints: int
    active_bots: int


class AnalyzeRequest(BaseModel):
    text: str


class AnalyzeResponse(BaseModel):
    sentiment: str
    emotion: str
    complaint: bool
    priority: str
    category: str
    summary: str


class AnalyticsOut(BaseModel):
    total_analyzed: int
    negative_share: float
    complaint_share: float
    top_emotion: str
    daily_data: list
    top_complaints: list
    categories: list
