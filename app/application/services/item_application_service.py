from fastapi import BackgroundTasks
from app.domain.items.item import Item
from app.domain.services.item_service import ItemService
from app.infrastructure.persistence.item_repository import ItemRepository
from app.application.services.notification_service import NotificationService


class ItemApplicationService:
    def __init__(
        self,
        item_service: ItemService,
        item_repository: ItemRepository,
        notification_service: NotificationService,
    ):
        self.item_service = item_service
        self.item_repository = item_repository
        self.notification_service = notification_service

    def create_item(self, item: Item, background_tasks: BackgroundTasks) -> None:
        self.item_service.create_item(item)
        self.item_repository.save(item)
        self.notification_service.send_notification(
            item.owner, f"Item {item.name} created"
        )
