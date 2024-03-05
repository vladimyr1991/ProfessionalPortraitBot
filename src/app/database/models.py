from sqlalchemy import BigInteger, ForeignKey, Enum, DateTime, Column, Integer, Boolean, LargeBinary, String
from sqlalchemy.orm import Mapped, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import datetime as dt
from . import OrderStatus
import os

SQLALCHEMY_URL: str = os.getenv("SQLALCHEMY_URL")


engine = create_async_engine(SQLALCHEMY_URL, echo=True)

async_session = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    telegram_id: Mapped[int] = Column(Integer, primary_key=True, nullable=False, unique=True)
    email: Mapped[str] = Column(Integer, nullable=False)
    telegram_name: Mapped[str] = Column(String, nullable=False)
    is_admin: Mapped[bool] = Column(Boolean, default=False)
    registration_date: Mapped[dt.datetime] = Column(DateTime, nullable=False)
    order = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("user.telegram_id"))  # telegram_id atm
    status: Mapped[OrderStatus] = Column(Enum(OrderStatus), nullable=False)
    creation_date: Mapped[dt.datetime] = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="order")
    raw_image = relationship("RawImage", back_populates="order")
    processed_image = relationship("ProcessedImage", back_populates="order")


class RawImage(Base):
    __tablename__ = "raw_image"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey("order.id"))
    image: Mapped[bytes] = Column(LargeBinary, nullable=False)
    order = relationship("Order", back_populates="raw_image")


class ProcessedImage(Base):
    __tablename__ = "processed_image"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey("order.id"))
    image: Mapped[bytes] = Column(LargeBinary, nullable=False)
    order = relationship("Order", back_populates="processed_image")


async def async_main():
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)
