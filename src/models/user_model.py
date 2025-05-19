from typing import TypedDict
from datetime import datetime


class UserData(TypedDict):
    id: str
    first_name: str
    last_name: str
    username: str
    language_code: str
    is_bot: bool
    created_at: datetime
    last_active: datetime
    is_vip: bool
    vip_expires: datetime | None
