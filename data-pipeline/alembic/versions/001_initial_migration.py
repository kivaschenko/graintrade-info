"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-12-25 14:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    return inspect(bind).has_table(table_name)


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    existing = inspect(bind).get_indexes(table_name)
    return any(idx.get("name") == index_name for idx in existing)


def upgrade() -> None:
    # Create data_sources table
    if not _has_table("data_sources"):
        op.create_table(
            "data_sources",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("source_type", sa.String(length=50), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("url", sa.String(length=500), nullable=True),
            sa.Column("file_path", sa.String(length=500), nullable=True),
            sa.Column("api_endpoint", sa.String(length=500), nullable=True),
            sa.Column("credentials_required", sa.Boolean(), nullable=True),
            sa.Column("config", postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column("update_frequency", sa.String(length=50), nullable=True),
            sa.Column("last_ingestion", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_scheduled_ingestion", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("is_validated", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.String(length=100), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
    if _has_table("data_sources") and not _has_index("data_sources", op.f("ix_data_sources_id")):
        op.create_index(op.f("ix_data_sources_id"), "data_sources", ["id"], unique=False)

    # Create commodities table
    if not _has_table("commodities"):
        op.create_table(
            "commodities",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("variety", sa.String(length=100), nullable=True),
            sa.Column("region", sa.String(length=100), nullable=True),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=True),
            sa.Column("unit", sa.String(length=20), nullable=True),
            sa.Column("quality_grade", sa.String(length=50), nullable=True),
            sa.Column("protein_content", sa.Float(), nullable=True),
            sa.Column("moisture_content", sa.Float(), nullable=True),
            sa.Column("date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("source_type", sa.String(length=50), nullable=True),
            sa.Column("source_name", sa.String(length=200), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_validated", sa.Boolean(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if _has_table("commodities") and not _has_index("commodities", op.f("ix_commodities_date")):
        op.create_index(op.f("ix_commodities_date"), "commodities", ["date"], unique=False)
    if _has_table("commodities") and not _has_index("commodities", op.f("ix_commodities_id")):
        op.create_index(op.f("ix_commodities_id"), "commodities", ["id"], unique=False)
    if _has_table("commodities") and not _has_index("commodities", op.f("ix_commodities_name")):
        op.create_index(op.f("ix_commodities_name"), "commodities", ["name"], unique=False)
    if _has_table("commodities") and not _has_index("commodities", op.f("ix_commodities_region")):
        op.create_index(op.f("ix_commodities_region"), "commodities", ["region"], unique=False)

    # Create ingestion_logs table
    if not _has_table("ingestion_logs"):
        op.create_table(
            "ingestion_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("data_source_id", sa.Integer(), nullable=False),
            sa.Column("job_id", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("layer", sa.String(length=20), nullable=True),
            sa.Column("records_read", sa.Integer(), nullable=True),
            sa.Column("records_written", sa.Integer(), nullable=True),
            sa.Column("records_failed", sa.Integer(), nullable=True),
            sa.Column("execution_time_seconds", sa.Float(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("error_details", sa.Text(), nullable=True),
            sa.Column("input_path", sa.String(length=500), nullable=True),
            sa.Column("output_path", sa.String(length=500), nullable=True),
            sa.ForeignKeyConstraint(["data_source_id"], ["data_sources.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    if _has_table("ingestion_logs") and not _has_index("ingestion_logs", op.f("ix_ingestion_logs_id")):
        op.create_index(op.f("ix_ingestion_logs_id"), "ingestion_logs", ["id"], unique=False)
    if _has_table("ingestion_logs") and not _has_index("ingestion_logs", op.f("ix_ingestion_logs_job_id")):
        op.create_index(op.f("ix_ingestion_logs_job_id"), "ingestion_logs", ["job_id"], unique=True)

    # Create predictions table
    if not _has_table("predictions"):
        op.create_table(
            "predictions",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("commodity_name", sa.String(length=100), nullable=False),
            sa.Column("region", sa.String(length=100), nullable=True),
            sa.Column("predicted_price", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=True),
            sa.Column("prediction_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("prediction_horizon_days", sa.Integer(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("lower_bound", sa.Float(), nullable=True),
            sa.Column("upper_bound", sa.Float(), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("model_version", sa.String(length=50), nullable=True),
            sa.Column("features_used", postgresql.JSON(astext_type=sa.Text()), nullable=True),
            sa.Column("actual_price", sa.Float(), nullable=True),
            sa.Column("prediction_error", sa.Float(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
            sa.Column("is_validated", sa.Boolean(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
    if _has_table("predictions") and not _has_index("predictions", op.f("ix_predictions_commodity_name")):
        op.create_index(op.f("ix_predictions_commodity_name"), "predictions", ["commodity_name"], unique=False)
    if _has_table("predictions") and not _has_index("predictions", op.f("ix_predictions_id")):
        op.create_index(op.f("ix_predictions_id"), "predictions", ["id"], unique=False)
    if _has_table("predictions") and not _has_index("predictions", op.f("ix_predictions_prediction_date")):
        op.create_index(op.f("ix_predictions_prediction_date"), "predictions", ["prediction_date"], unique=False)
    if _has_table("predictions") and not _has_index("predictions", op.f("ix_predictions_region")):
        op.create_index(op.f("ix_predictions_region"), "predictions", ["region"], unique=False)


def downgrade() -> None:
    if _has_table("predictions"):
        if _has_index("predictions", op.f("ix_predictions_region")):
            op.drop_index(op.f("ix_predictions_region"), table_name="predictions")
        if _has_index("predictions", op.f("ix_predictions_prediction_date")):
            op.drop_index(op.f("ix_predictions_prediction_date"), table_name="predictions")
        if _has_index("predictions", op.f("ix_predictions_id")):
            op.drop_index(op.f("ix_predictions_id"), table_name="predictions")
        if _has_index("predictions", op.f("ix_predictions_commodity_name")):
            op.drop_index(op.f("ix_predictions_commodity_name"), table_name="predictions")
        op.drop_table("predictions")

    if _has_table("ingestion_logs"):
        if _has_index("ingestion_logs", op.f("ix_ingestion_logs_job_id")):
            op.drop_index(op.f("ix_ingestion_logs_job_id"), table_name="ingestion_logs")
        if _has_index("ingestion_logs", op.f("ix_ingestion_logs_id")):
            op.drop_index(op.f("ix_ingestion_logs_id"), table_name="ingestion_logs")
        op.drop_table("ingestion_logs")

    if _has_table("commodities"):
        if _has_index("commodities", op.f("ix_commodities_region")):
            op.drop_index(op.f("ix_commodities_region"), table_name="commodities")
        if _has_index("commodities", op.f("ix_commodities_name")):
            op.drop_index(op.f("ix_commodities_name"), table_name="commodities")
        if _has_index("commodities", op.f("ix_commodities_id")):
            op.drop_index(op.f("ix_commodities_id"), table_name="commodities")
        if _has_index("commodities", op.f("ix_commodities_date")):
            op.drop_index(op.f("ix_commodities_date"), table_name="commodities")
        op.drop_table("commodities")

    if _has_table("data_sources"):
        if _has_index("data_sources", op.f("ix_data_sources_id")):
            op.drop_index(op.f("ix_data_sources_id"), table_name="data_sources")
        op.drop_table("data_sources")