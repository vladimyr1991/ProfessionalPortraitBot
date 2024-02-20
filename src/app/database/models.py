from sqlalchemy import BigInteger, ForeignKey, Enum, LargeBinary, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine
import datetime as dt
from . import OrderStatus


import src.config as config

engine = create_async_engine(config.SQLALCHEMY_URL, echo=True)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    registration_date: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, telegram_id={self.telegram_id}, is_admin={self.is_admin}), registration_date={self.registration_date}"


class RawPhotos(Base):
    __tablename__ = "raw_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('orders.id'), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)  # Storing binary data
    creation_date: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    # Relationship to link back to the Orders table
    order: Mapped['Orders'] = relationship("Orders", back_populates="raw_photos")


class ProcessedPhotos(Base):
    __tablename__ = "processed_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('orders.id'), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)  # Storing binary data
    creation_date: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)

    # Relationship to link back to the Orders table
    order: Mapped['Orders'] = relationship("Orders", back_populates="processed_photos")


class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    creation_date: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    users = relationship("Orders", back_populates="users")
    # Relationships to link to the photo tables
    raw_photos: Mapped[list['RawPhotos']] = relationship("RawPhotos", back_populates="order", cascade="all, delete-orphan")
    processed_photos: Mapped[list['ProcessedPhotos']] = relationship("ProcessedPhotos", back_populates="order", cascade="all, delete-orphan")


async def async_main():
    async with engine.begin() as session:
        await session.run_sync(Base.metadata.create_all)
