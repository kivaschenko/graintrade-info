from fastapi import BackgroundTasks
from app.domain.recipient import Recipient
from app.domain.services.item_service import ItemService
from app.infrastructure.persistence.item_repository import AbstractItemRepository
from app.services.notification_service import NotificationService
from app.domain.item import ItemInDB, ItemInResponse


class ItemApplicationService:
    def __init__(
        self,
        item_repository: AbstractItemRepository,
        item_service: ItemService = None,
        notification_service: NotificationService = None,
    ):
        self.item_service = item_service
        self.item_repository = item_repository
        self.notification_service = notification_service

    async def create_item(
        self,
        item: ItemInDB,
        username: str = None,
        recipient: Recipient = None,
        background_tasks: BackgroundTasks = None,
    ) -> ItemInResponse:
        if username is None:
            raise ValueError("Username is required")

        # Create item
        created_item = await self.item_repository.create(item, username)

        # Add some logic to the item service
        if self.item_service:
            self.item_service.bind_views_counter(created_item)
            # add more logic here

        # For example, check the list of subscribers of username and send notifications
        # Send notification if recipient(s) is provided
        if recipient and self.notification_service and background_tasks:
            background_tasks.add_task(
                self.notification_service.send_notification,
                recipient,
                f"Item {item.title} created",
            )
        return created_item
