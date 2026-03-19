import logging
from database import get_db_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def check_subscriptions():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT update_expired_subscriptions()")
            conn.commit()
            logging.info("Successfully checked and updated subscriptions")
    except Exception as e:
        logging.error(f"Error checking subscriptions: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    check_subscriptions()
