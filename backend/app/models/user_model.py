from datetime import date, timedelta, datetime, timezone

from ..database import database
from ..schemas import UserInDB, UserInResponse, PreferencesUpdateSchema

ORDER_ID = "registration-{}"


async def create(user, scope: str = "free") -> UserInResponse:
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    order_id = ORDER_ID.format(user.username)
    query = """
        INSERT INTO users (username, email, full_name, phone, hashed_password)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, username, email, full_name, phone, hashed_password, disabled
    """
    subscr_query = """
        INSERT INTO subscriptions (user_id, tarif_id, start_date, end_date, order_id, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """
    tarif_query = """
        SELECT id, name, description, price, currency, scope, terms, created_at
        FROM tarifs
        WHERE scope = $1
    """

    async with database.pool.acquire() as conn:
        # Open a transaction to create default subscription
        async with conn.transaction():
            row = await conn.fetchrow(
                query,
                user.username,
                user.email,
                user.full_name,
                user.phone,
                user.hashed_password,
            )
            user = UserInResponse(**row)
            tarif_id = await conn.fetchval(tarif_query, scope)
            subscr_id = await conn.fetchval(
                subscr_query,
                user.id,
                tarif_id,
                start_date,
                end_date,
                order_id,
                "active",
            )
            assert subscr_id > 0
    return user


async def get_by_username(username: str) -> UserInResponse:
    query = """
        SELECT id, username, email, full_name, phone, hashed_password, disabled
        FROM users
        WHERE username = $1
    """
    async with database.pool.acquire() as conn:
        try:
            row = await conn.fetchrow(query, username)
            return UserInResponse(**row)
        except Exception as e:
            print(f"Error fetching user by username: {e}")
            raise ValueError(f"User with username {username} not found.")


async def get_by_id(user_id: int) -> UserInResponse:
    query = """
        SELECT id, username, email, full_name, phone, disabled, hashed_password
        FROM users
        WHERE id = $1 AND disabled = 'false'
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(query, user_id)
    return UserInResponse(**row)


async def update(user_id: int, user: UserInDB) -> UserInResponse:
    query = """
        UPDATE users
        SET username = $1, email = $2, full_name = $3, hashed_password = $4, phone = $5
        WHERE id = $6
        RETURNING id, username, email, full_name, phone, disabled, hashed_password
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            query,
            user.username,
            user.email,
            user.full_name,
            user.hashed_password,
            user.phone,
            user_id,
        )
    return UserInResponse(**row)


async def delete(user_id: int) -> None:
    query = "UPDATE users SET disabled = 'true' WHERE id = $1"
    async with database.pool.acquire() as conn:
        await conn.execute(query, user_id)


async def get_by_email(email: str) -> UserInResponse:
    query = """
        SELECT id, username, email, full_name, phone, disabled, hashed_password
        FROM users
        WHERE email = $1
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, email)
    return UserInResponse(**row)


async def get_by_username_and_email(username: str, email: str) -> UserInResponse:
    query = """
        SELECT id, username, email, full_name, phone, disabled, hashed_password
        FROM users
        WHERE username = $1 AND email = $2
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, username, email)
    return UserInResponse(**row)


async def update_password(user_id: int, hashed_password: str) -> UserInResponse | None:
    query = """
        UPDATE users
        SET hashed_password = $1
        WHERE id = $2
        RETURNING id, username, email, full_name, phone, disabled, hashed_password
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, hashed_password, user_id)
    return UserInResponse(**row) if row else None


# ----------
# Prefernces


async def update_user_preferences(user_id: int, prefs_data: PreferencesUpdateSchema):
    query = """
        UPDATE user_notification_preferences
        SET notify_new_messages = $1,
            notify_new_items = $2,
            interested_categories = $3,
            updated_at = $4
        WHERE user_id = $5
        RETURNING user_id, notify_new_messages, notify_new_items, interested_categories
    """
    timestamp = datetime.now()
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(
            query,
            prefs_data.notify_new_messages,
            prefs_data.notify_new_items,
            prefs_data.interested_categories,
            timestamp,
            user_id,
        )
        if row is None:
            raise ValueError("User prefernces not found for the given user_id.")
        return PreferencesUpdateSchema(
            notify_new_messages=row["notify_new_messages"],
            notify_new_items=row["notify_new_items"],
            interested_categories=row["interested_categories"],
        )


async def get_user_preferences(user_id: int) -> PreferencesUpdateSchema:
    query = """
        SELECT user_id, notify_new_messages, notify_new_items, interested_categories
        FROM user_notification_preferences
        WHERE user_id = $1
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(query, user_id)
        if row is None:
            raise ValueError("User preferences not found for the given user_id.")
        return PreferencesUpdateSchema(
            notify_new_messages=row["notify_new_messages"],
            notify_new_items=row["notify_new_items"],
            interested_categories=row["interested_categories"],
        )


async def create_user_preferences(user_id: int, prefs_data: PreferencesUpdateSchema):
    query = """
        INSERT INTO user_notification_preferences (user_id, notify_new_messages, notify_new_items, interested_categories)
        VALUES ($1, $2, $3, $4)
        RETURNING user_id, notify_new_messages, notify_new_items, interested_categories
    """
    async with database.pool.acquire() as connection:
        row = await connection.fetchrow(
            query,
            user_id,
            prefs_data.notify_new_messages,
            prefs_data.notify_new_items,
            prefs_data.interested_categories,
        )
        return PreferencesUpdateSchema(
            notify_new_messages=row["notify_new_messages"],
            notify_new_items=row["notify_new_items"],
            interested_categories=row["interested_categories"],
        )


async def get_or_create_user_preferences(user_id: int) -> PreferencesUpdateSchema:
    try:
        return await get_user_preferences(user_id)
    except ValueError:
        # If preferences do not exist, create them with default values
        default_prefs = PreferencesUpdateSchema(
            notify_new_messages=False, notify_new_items=False, interested_categories=[]
        )
        return await create_user_preferences(user_id, default_prefs)
