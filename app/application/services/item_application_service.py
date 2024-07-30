from fastapi import BackgroundTasks
from app.domain.entities.item import Item
from app.domain.value_objects.recipient import Recipient
from app.domain.services.item_service import ItemService
from app.infrastructure.persistence.item_repository import AbstractItemRepository
from app.application.services.notification_service import NotificationService
from app.schemas.schemas import ItemInDB, ItemInResponse


class ItemApplicationService:
    def __init__(
        self,
        item_service: ItemService,
        item_repository: AbstractItemRepository,
        notification_service: NotificationService,
    ):
        self.item_service = item_service
        self.item_repository = item_repository
        self.notification_service = notification_service

    async def create_item(
        self,
        item: ItemInDB,
        recipient: Recipient = None,
        background_tasks: BackgroundTasks = None,
    ) -> ItemInResponse:
        result = await self.item_repository.create(item)
        if recipient:
            background_tasks.add_task(
                self.notification_service.send_notification,
                recipient,
                f"Item {item.title} created",
            )
        return result
