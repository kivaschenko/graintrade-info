from typing import List
from datetime import date, timedelta, timezone
from app.database import database
from app.schemas import UserInDB, UserInResponse


async def create(user: UserInDB, tarif_name: str = "Basic") -> UserInResponse:
    start_date = date.today()
    end_date = start_date + timedelta(days=31)
    scope = tarif_name.lower()
    print(f"start date: {start_date}, end date: {end_date}, scope={scope}")
    query = """
        INSERT INTO users (username, email, full_name, phone, hashed_password)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, username, email, full_name, phone, hashed_password, disabled
    """
    subscr_query = """
        INSERT INTO subscriptions (user_id, tarif_id, start_date, end_date, status)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
    """
    tarif_query = """
        SELECT id, name, description, price, currency, scope, terms, created_at
        FROM tarifs
        WHERE scope = $1
    """

    async with database.pool.acquire() as connection:
        # Open a transaction to create default subscription
        async with connection.transaction():
            row = await connection.fetchrow(
                query,
                user.username,
                user.email,
                user.full_name,
                user.phone,
                user.hashed_password,
            )
            user = UserInResponse(**row)
            tarif_id = await connection.fetchval(tarif_query, scope)
            subscr_id = await connection.fetchval(
                subscr_query, user.id, tarif_id, start_date, end_date, "active"
            )
            assert subscr_id > 0
    return user
