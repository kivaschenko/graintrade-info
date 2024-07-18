from .unit_of_works import AbstractUnitOfWork
from .repositories import *  # noqa


def create_new_item_and_bind_user(
    uow: AbstractUnitOfWork,
    item_repo: AbstractItemRepository,
    item_user_repo: AbstractItemUserRepository,
    item: dict,
    user_id: int,
):
    with uow:
        item_repo.create(item)
        item_user_repo.bind_item(user_id, item.id)