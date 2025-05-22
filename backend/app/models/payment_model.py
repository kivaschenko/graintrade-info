import json
from ..database import database


async def create(data: dict):
    # Ensure the data field is properly serialized to JSON
    if isinstance(data["data"], (dict, str)):
        json_data = json.dumps(data["data"])
    else:
        json_data = str(data["data"])

    query = """
    INSERT INTO payments (
        payment_id, order_id, order_status, currency,
        amount, card_type, masked_card, sender_email, data
    )
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    ON CONFLICT (payment_id) DO UPDATE
    SET order_id = EXCLUDED.order_id,
        order_status = EXCLUDED.order_status,
        currency = EXCLUDED.currency,
        amount = EXCLUDED.amount,
        card_type = EXCLUDED.card_type,
        masked_card = EXCLUDED.masked_card,
        sender_email = EXCLUDED.sender_email,
        data = EXCLUDED.data
    RETURNING id, payment_id, order_id, order_status, currency,
              amount, card_type, masked_card, sender_email, data
    """
    print("Data:", data)
    print("JSON Data:", json_data, type(json_data))

    async with database.pool.acquire() as connection:
        payment = await connection.fetchrow(
            query,
            data["payment_id"],
            str(data["order_id"]),
            data["order_status"],
            data["currency"],
            data["amount"],
            data["card_type"],
            data["masked_card"],
            data["sender_email"],
            json_data,
        )
    if payment:
        return payment
    else:
        raise Exception("Payment not created")
