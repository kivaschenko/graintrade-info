import json
from datetime import datetime
from typing import Dict, Any
from ..database import database
from ..logger import logger


async def create(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create or update a payment record

    Args:
        data (Dict[str, Any]): Payment data dictionary from payment provider response

    Returns:
        Dict[str, Any]: Created/updated payment record

    Raises:
        ValueError: If required fields are missing or invalid
        Exception: If database operation fails
    """
    try:
        # Essential fields that must be present for persistence.
        essential_fields = [
            "payment_id",
            "order_id",
            "order_status",
            "currency",
            "amount",
            "response_status",
            "tran_type",
            "order_time",
            "additional_info",
            "provider",
        ]

        # Optional provider-specific fields that may be absent in live callbacks.
        optional_fields_with_defaults = {
            "card_type": "unknown",
            "masked_card": "",
            "payment_system": "unknown",
        }

        for field, default_value in optional_fields_with_defaults.items():
            if field not in data or data[field] is None:
                data[field] = default_value

        # Validate required fields and data types
        for field in essential_fields:
            if field not in data:
                logger.error(f"Missing required field in payment data: {field}. Available fields: {list(data.keys())}")
                raise ValueError(f"Missing required field: {field}")
            if data[field] is None:
                logger.error(f"Field '{field}' is None in payment data. All data: {data}")
                raise ValueError(f"Field cannot be None: {field}")

        # Ensure numeric fields are properly typed
        try:
            data["amount"] = int(data["amount"])
            data["payment_id"] = int(data["payment_id"])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid numeric value: {str(e)}")

        # Convert additional_info to JSONB
        additional_info = {
            k: v for k, v in data.items() if k not in essential_fields and k != "id"
        }

        insert_query = """
        INSERT INTO payments (
            payment_id,
            order_id,
            order_status,
            currency,
            amount,
            card_type,
            masked_card,
            payment_system,
            response_status,
            tran_type,
            order_time,
            additional_info,
            provider
        )
        VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
        )
        RETURNING *;
        """

        update_by_order_query = """
        UPDATE payments
        SET
            payment_id = $2,
            order_status = $3,
            currency = $4,
            amount = $5,
            card_type = $6,
            masked_card = $7,
            payment_system = $8,
            response_status = $9,
            tran_type = $10,
            order_time = $11,
            additional_info = COALESCE(payments.additional_info, '{}'::jsonb) || $12::jsonb,
            provider = $13
        WHERE order_id = $1
        RETURNING *;
        """

        try:
            order_time = datetime.strptime(data["order_time"], "%d.%m.%Y %H:%M:%S")
        except ValueError:
            raise ValueError("Invalid order_time format. Expected DD.MM.YYYY HH:MM:SS")

        async with database.pool.acquire() as connection:
            async with connection.transaction():
                payment = await connection.fetchrow(
                    update_by_order_query,
                    data["order_id"],
                    data["payment_id"],
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
                if payment is None:
                    payment = await connection.fetchrow(
                        insert_query,
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
