from enum import Enum


class OrderStatus(Enum):
    PENDING = "IN_QUEUE"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"