# src/data_pipeline/spark_services/gold_layer.py
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, avg, min, max, count,
    window, date_format
)
from app.config import settings
from app.logger import logger
from app.spark_services.silver_layer import read_silver_table


def create_gold_tables(
    silver_table_name: str,
    commodity_name: str,
    aggregation_level: str = "daily"
) -> dict:
    """
    Create Gold layer tables for specific commodities
    Ready for analytics and ML
    
    Args:
        silver_table_name: Name of the silver table to read
        commodity_name: Name of commodity to filter (e.g., "wheat", "corn")
        aggregation_level: Aggregation level (daily, weekly, monthly)
    
    Returns:
        dict: Processing statistics
    """
    logger.info(f"Creating gold table for commodity: {commodity_name}")
    
    try:
        # Read silver data
        df = read_silver_table(silver_table_name)
        records_read = df.count()
        
        # Filter by commodity
        df_commodity = df.filter(col("name") == commodity_name)
        
        # Apply aggregations and business logic
        df_gold = apply_business_logic(df_commodity, aggregation_level)
        
        records_processed = df_gold.count()
        
        # Write to Gold Delta table
        gold_path = f"{settings.GOLD_LAYER_PATH}/{commodity_name.lower()}"
        
        df_gold.write \
            .format("delta") \
            .mode("append") \
            .partitionBy("region", "date") \
            .option("mergeSchema", "true") \
            .save(gold_path)
        
        logger.info(f"Written {records_processed} records to gold layer: {gold_path}")
        
        return {
            "status": "success",
            "records_read": records_read,
            "records_written": records_processed,
            "output_path": gold_path,
            "commodity": commodity_name,
        }
        
    except Exception as e:
        logger.error(f"Gold table creation failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "records_read": 0,
            "records_written": 0,
        }


def apply_business_logic(df: DataFrame, aggregation_level: str) -> DataFrame:
    """
    Apply business logic and aggregations for gold layer
    
    Args:
        df: Input DataFrame from silver layer
        aggregation_level: Level of aggregation
    
    Returns:
        DataFrame: Processed DataFrame
    """
    # Add business calculations
    df = df.withColumn("_gold_processed_timestamp", current_timestamp())
    
    # Example: Calculate price statistics by region and date
    if aggregation_level == "daily":
        df_agg = df.groupBy("region", "date").agg(
            avg("price").alias("avg_price"),
            min("price").alias("min_price"),
            max("price").alias("max_price"),
            count("*").alias("record_count")
        )
    elif aggregation_level == "weekly":
        df_agg = df.groupBy("region", window("date", "7 days")).agg(
            avg("price").alias("avg_price"),
            min("price").alias("min_price"),
            max("price").alias("max_price"),
            count("*").alias("record_count")
        )
    else:
        # No aggregation, return as is
        df_agg = df
    
    return df_agg


def read_gold_table(commodity_name: str) -> DataFrame:
    """
    Read a gold Delta table for a specific commodity
    
    Args:
        commodity_name: Name of the commodity
    
    Returns:
        DataFrame: Spark DataFrame
    """
    from app.spark_services.spark_session import get_spark_session
    spark = get_spark_session()
    gold_path = f"{settings.GOLD_LAYER_PATH}/{commodity_name.lower()}"
    
    logger.info(f"Reading gold table: {gold_path}")
    
    return spark.read.format("delta").load(gold_path)


def get_commodity_statistics(commodity_name: str, region: str = None) -> dict:
    """
    Get statistics for a commodity from gold layer
    
    Args:
        commodity_name: Name of the commodity
        region: Optional region filter
    
    Returns:
        dict: Statistics
    """
    df = read_gold_table(commodity_name)
    
    if region:
        df = df.filter(col("region") == region)
    
    stats = df.agg(
        avg("avg_price").alias("overall_avg_price"),
        min("min_price").alias("overall_min_price"),
        max("max_price").alias("overall_max_price"),
        count("*").alias("total_records")
    ).collect()[0]
    
    return {
        "commodity": commodity_name,
        "region": region or "all",
        "avg_price": float(stats["overall_avg_price"]) if stats["overall_avg_price"] else None,
        "min_price": float(stats["overall_min_price"]) if stats["overall_min_price"] else None,
        "max_price": float(stats["overall_max_price"]) if stats["overall_max_price"] else None,
        "total_records": int(stats["total_records"]),
    }
