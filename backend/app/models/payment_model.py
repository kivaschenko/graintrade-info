from ..database import database
from ..schemas import PaymentInDB, PaymentInResponse


async def create(payment: PaymentInDB) -> PaymentInResponse:
    query = """
    INSERT INTO payments (user_id, tarif_id, subscription_id, amount, currency, payment_id, signature)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING id, user_id, tarif_id, subscription_id, amount, currency, payment_id, signature
    """
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            query,
            payment.user_id,
            payment.tarif_id,
            payment.subscription_id,
            payment.amount,
            payment.currency,
            payment.payment_id,
            payment.signature,
        )
        new_payment = PaymentInResponse(**row)
        return new_payment
