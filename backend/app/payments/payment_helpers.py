from datetime import date, timedelta
import logging
import redis
from ..database import redis_db

ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"


logging.basicConfig(level=logging.INFO)


# ---------------------------
# Helpers for Payment Service


def make_start_end_dates_for_monthly_case() -> tuple[date, date]:
    start_date = date.today()
    end_date = start_date + timedelta(days=30)
    return start_date, end_date


def save_signature_to_cache(order_id: str, signature: str):
    r = redis.Redis().from_pool(redis_db.pool)
    res = r.set(name=order_id, value=signature, ex=600)
    if not res:
        logging.error(f"Failed to save signature for order_id {order_id} in cache")
    else:
        logging.info(f"Signature saved for order_id {order_id} in cache")
    r.close()


def get_signature_from_cache(order_id: str):
    r = redis.Redis().from_pool(redis_db.pool)
    signature = r.get(name=order_id)
    r.close()
    return signature
