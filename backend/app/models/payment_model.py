import json
import logging
from typing import Dict, Any
from ..database import database

logger = logging.getLogger(__name__)


async def create(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create or update a payment record

    Args:
        data (Dict[str, Any]): Payment data dictionary

    Returns:
        Dict[str, Any]: Created/updated payment record

    Raises:
        ValueError: If required fields are missing or invalid
        Exception: If database operation fails
    """
    try:
        # Validate required fields
        required_fields = [
            "payment_id",
            "order_id",
            "order_status",
            "currency",
            "amount",
            "card_type",
            "masked_card",
            "sender_email",
            "data",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            if data[field] is None:
                raise ValueError(f"Field cannot be None: {field}")

        # Convert data to string if it's not already
        if isinstance(data["data"], (dict, list)):
            json_data = json.dumps(data["data"])
        else:
            json_data = str(data["data"])

        payment_id = data["payment_id"]
        order_id = data["order_id"]
        order_status = data["order_status"]
        currency = data["currency"]
        amount = data["amount"]
        card_type = data["card_type"]
        masked_card = data["masked_card"]
        sender_email = data["sender_email"]

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
        async with database.pool.acquire() as connection:
            payment = await connection.fetchrow(
                query,
                payment_id,
                order_id,
                order_status,
                currency,
                amount,
                card_type,
                masked_card,
                sender_email,
                json_data,
            )

        if not payment:
            raise Exception("Payment record was not created/updated")

        return dict(payment)

    except Exception as e:
        logger.error("Database error: %s", str(e))
        raise
