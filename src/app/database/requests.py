from .models import engine
from .models import User
import datetime as dt


async def insert_user(telegram_id: int, email: str):
    async with engine.begin() as session:
        user = User(
            telegram_id=telegram_id,
            email=email,
            is_admin=False,
            registration_date=dt.datetime.now(dt.timezone.utc)
            )
        await session.add(user)
        await session.commit()
