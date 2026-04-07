"""Pydantic models for the OpenEnv Email Triage environment."""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    SPAM = "spam"
    IMPORTANT = "important"
    NEWSLETTER = "newsletter"
    PERSONAL = "personal"
    URGENT = "urgent"


class Department(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    ENGINEERING = "engineering"
    HR = "hr"
    MANAGEMENT = "management"
    GENERAL = "general"


class ActionType(str, Enum):
    CLASSIFY = "classify"
    PRIORITIZE = "prioritize"
    ROUTE = "route"
    RESPOND = "respond"
    FLAG = "flag"
    SKIP = "skip"
    DONE = "done"


class EmailMessage(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    timestamp: str
    attachments: list[str] = Field(default_factory=list)
    ground_truth_category: Optional[EmailCategory] = None
    ground_truth_priority: Optional[int] = None
    ground_truth_department: Optional[Department] = None
    requires_response: bool = False
    key_points: list[str] = Field(default_factory=list)


class Observation(BaseModel):
    inbox: list[EmailMessage]
    current_email_index: int = 0
    processed: list[str] = Field(default_factory=list)
    time_remaining: float = 100.0
    task_id: str = ""
    task_description: str = ""


class Action(BaseModel):
    action_type: ActionType
    email_id: str = ""
    category: Optional[EmailCategory] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    department: Optional[Department] = None
    response_text: Optional[str] = None
    flag_reason: Optional[str] = None


class Reward(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    breakdown: dict[str, Any] = Field(default_factory=dict)
    message: str = ""
