from typing import List, Optional

from fastapi import BackgroundTasks

from app.domain.item import ItemInDB, ItemInResponse
from app.domain.recipient import Recipient
from app.infrastructure.persistence.item_repository import AbstractItemRepository
from app.services.notification_service import NotificationService


class ItemApplicationService:
    """The service layer is responsible for the application's business logic.
    """
    def __init__(
        self,
        item_repository: AbstractItemRepository,
        notification_services: Optional[List[NotificationService]] = None,
    ):
        self.item_repository = item_repository
        self.notification_services = notification_services

    async def create_item(
        self,
        item: ItemInDB,
        username: str = None,
        recipient: Recipient = None,
        background_tasks: BackgroundTasks = None,
    ) -> ItemInResponse:
        """Create an item and send notifications to the recipient(s) if provided."""
        if username is None:
            raise ValueError("Username is required")

        # Create item
        created_item = await self.item_repository.create(item, username)

        # Add some logic to the item service
        # add more logic here

        # For example, check the list of subscribers of username and send notifications
        # Send notification if recipient(s) is provided
        if recipient and self.notification_services and background_tasks:
            for notification_service in self.notification_services:
                background_tasks.add_task(
                notification_service.send_notification,
                recipient,
                f"Item {item.title} created",
            )
        return created_item
