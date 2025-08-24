import json
import logging
from datetime import datetime
from typing import Dict, Any
from ..database import database

logger = logging.getLogger(__name__)


async def create(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create or update a payment record

    Args:
        data (Dict[str, Any]): Payment data dictionary from Fondy response

    Returns:
        Dict[str, Any]: Created/updated payment record

    Raises:
        ValueError: If required fields are missing or invalid
        Exception: If database operation fails
    """
    try:
        # Required fields according to PaymentInDB schema
        required_fields = [
            "payment_id",
            "order_id",
            "order_status",
            "currency",
            "amount",
            "card_type",
            "masked_card",
            "payment_system",
            "response_status",
            "tran_type",
            "order_time",
            "additional_info",
            "provider",
        ]

        # Validate required fields and data types
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
            if data[field] is None:
                raise ValueError(f"Field cannot be None: {field}")

        # Ensure numeric fields are properly typed
        try:
            data["amount"] = int(data["amount"])
            data["payment_id"] = int(data["payment_id"])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid numeric value: {str(e)}")

        # Convert additional_info to JSONB
        additional_info = {
            k: v for k, v in data.items() if k not in required_fields and k != "id"
        }

        query = """
        INSERT INTO payments (payment_id, order_id, order_status, currency, amount, card_type, masked_card, payment_system, response_status, tran_type, order_time, additional_info, provider
        )
        VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
        )
        ON CONFLICT (payment_id) DO UPDATE
        SET 
            order_status = EXCLUDED.order_status,
            response_status = EXCLUDED.response_status,
            additional_info = payments.additional_info || EXCLUDED.additional_info
        RETURNING *;
        """

        try:
            order_time = datetime.strptime(data["order_time"], "%d.%m.%Y %H:%M:%S")
        except ValueError:
            raise ValueError("Invalid order_time format. Expected DD.MM.YYYY HH:MM:SS")

        async with database.pool.acquire() as connection:
            async with connection.transaction():
                payment = await connection.fetchrow(
                    query,
                    data["payment_id"],
                    data["order_id"],
                    data["order_status"],
                    data["currency"],
                    data["amount"],
                    data["card_type"],
                    data["masked_card"],
                    data["payment_system"],
                    data["response_status"],
                    data["tran_type"],
                    order_time,
                    json.dumps(additional_info),
                    data["provider"],
                )

        if not payment:
            raise Exception("Payment record was not created/updated")

        return dict(payment)

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise
    except Exception as e:
        logger.error("Database error: %s", str(e))
        raise
