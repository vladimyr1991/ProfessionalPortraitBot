from . import User, Order, async_session, OrderStatus, RawImage, ImageType, ProcessedImage
import datetime as dt
import logging
import sqlalchemy as sa

__all__ = [
    "create_user",
    "user_registered",
    "create_order",
    "save_image",
    "get_order_by_telegram_id",
    "get_list_of_admin_users",
    "get_list_of_orders_for_admin",
    "update_order_status",
    "get_amount_of_pictures_in_order"
    ]


async def create_user(telegram_id: int, telegram_name: str, email: str = '', is_admin=False) -> User:
    async with async_session() as session:
        if telegram_id == 431200271:
            is_admin = True

        new_user = User(
            telegram_id=telegram_id,
            telegram_name=telegram_name,
            email=email,
            is_admin=is_admin,
            registration_date=dt.datetime.now(dt.timezone.utc)
            )
        session.add(new_user)
        await session.commit()
    logging.info(f"Inserted user {new_user}")
    return new_user


async def user_registered(user_id: int) -> bool:
    async with async_session() as session:
        query = sa.future.select(User).where(User.telegram_id == user_id)
        result = await session.execute(query)
        user = result.scalars().one_or_none()
        if not user:
            return False
        return True


async def get_order_by_telegram_id(telegram_id: int) -> Order | None:
    async with async_session() as session:
        query = sa.future.select(Order).where(Order.user_id == telegram_id, Order.status == OrderStatus.PREPARATION)
        result = await session.execute(query)
        user = result.scalars().one_or_none()
        return user


async def create_order(telegram_id: int, order_status: OrderStatus) -> Order:
    async with async_session() as session:
        new_order = Order(
            user_id=telegram_id,
            status=order_status,
            creation_date=dt.datetime.now(dt.timezone.utc)
            )
        session.add(new_order)
        logging.info(f"Inserted user {new_order}")
        await session.commit()
    logging.info("Order created")
    return new_order


async def update_order_status(order_id: int, order_status: OrderStatus) -> Order | None:
    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order:
            order.status = order_status
            logging.info(f"Order {order_id} updated with status {order_status.name}")
            await session.commit()
            logging.info("Order status updated")
            return order
        else:
            logging.error(f"Order {order_id} not found")
            return None


async def save_image(order_id: str, image_binary: bytes, image_type: ImageType) -> RawImage | ProcessedImage:
    try:
        async with async_session() as session:
            if image_type == ImageType.RAW:
                image = RawImage(
                    order_id=order_id,
                    image=image_binary
                    )
            elif image_type == ImageType.PROCESSED:
                image = ProcessedImage(
                    order_id=order_id,
                    image=image_binary
                    )
            session.add(image)
            await session.commit()
            logging.info(f"Inserted {image_type}  image {image}")
        return image
    except Exception as e:
        logging.error(f"Failed to insert raw image: {e}")
        raise


async def get_list_of_admin_users() -> list[str]:
    async with async_session() as session:
        query = sa.future.select(User).where(User.is_admin == True)
        result = await session.execute(query)
        users = result.scalars().all()
        return [user.telegram_id for user in users]


async def get_list_of_orders_for_admin(operation_type: str) -> set[str]:
    async with async_session() as session:
        if operation_type == "change_status":
            query = sa.future.select(Order).where(Order.status == OrderStatus.PAYMENT_APPROVAL_REQUIRED)
        elif operation_type == "upload_photo":
            query = sa.future.select(Order).where(Order.status == OrderStatus.AWAITING_RESULTS_FROM_AI)
        result = await session.execute(query)
        orders = result.scalars().all()
        return {order.id for order in orders}


async def get_amount_of_pictures_in_order(order_id: str):
    async with async_session() as session:
        query = sa.future.select(RawImage).where(RawImage.order_id == order_id)
        result = await session.execute(query)
        images = result.scalars().all()
        return len(images)