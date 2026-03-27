# src/data_pipeline/spark_services/silver_layer.py
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, current_timestamp, to_date, trim, upper, lower,
    when, regexp_replace, coalesce
)

import pandas as pd

from app.config import settings
from app.logger import logger
from app.spark_services.bronze_layer import read_bronze_table


def transform_to_silver(
    bronze_table_name: str | None,
    silver_table_name: str,
    transformation_rules: dict = None,
    source_data=None,
) -> dict:
    """
    Transform and clean Bronze data to Silver layer
    
    Args:
        bronze_table_name: Name of the bronze table to read
        silver_table_name: Name of the silver table to write
        transformation_rules: Optional transformation rules
        source_data: Optional in-memory parser output
    
    Returns:
        dict: Transformation statistics
    """
    logger.info(f"Starting silver transformation: {bronze_table_name} -> {silver_table_name}")
    
    try:
        # Read bronze data
        if source_data is not None:
            from app.spark_services.spark_session import get_spark_session

            spark = get_spark_session()
            if isinstance(source_data, pd.DataFrame):
                df = spark.createDataFrame(source_data)
            elif isinstance(source_data, list):
                df = spark.createDataFrame(source_data)
            elif isinstance(source_data, dict):
                df = spark.createDataFrame([source_data])
            else:
                raise ValueError(f"Unsupported source_data type: {type(source_data)!r}")
        else:
            if not bronze_table_name:
                raise ValueError("bronze_table_name is required when source_data is not provided")
            df = read_bronze_table(bronze_table_name)
        records_read = df.count()
        logger.info(f"Read {records_read} records from bronze")
        
        # Apply data quality and transformation rules
        df_clean = apply_data_quality_rules(df, transformation_rules)
        
        # Add processed timestamp
        df_clean = df_clean.withColumn("_processed_timestamp", current_timestamp())
        
        # Remove duplicates
        df_clean = df_clean.dropDuplicates()
        
        records_after_clean = df_clean.count()
        records_removed = records_read - records_after_clean
        
        logger.info(f"Data cleaned: {records_after_clean} records, {records_removed} removed")
        
        # Write to Silver Delta table
        silver_path = f"{settings.SILVER_LAYER_PATH}/{silver_table_name}"
        
        df_clean.write \
            .format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .save(silver_path)
        
        logger.info(f"Written {records_after_clean} records to silver layer: {silver_path}")
        
        return {
            "status": "success",
            "records_read": records_read,
            "records_written": records_after_clean,
            "records_removed": records_removed,
            "output_path": silver_path,
        }
        
    except Exception as e:
        logger.error(f"Silver transformation failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "records_read": 0,
            "records_written": 0,
        }


def apply_data_quality_rules(df: DataFrame, rules: dict = None) -> DataFrame:
    """
    Apply data quality rules and transformations
    
    Args:
        df: Input DataFrame
        rules: Transformation rules (optional)
    
    Returns:
        DataFrame: Cleaned DataFrame
    """
    # Remove rows with null critical fields (if specified in rules)
    if rules and "required_fields" in rules:
        for field in rules["required_fields"]:
            df = df.filter(col(field).isNotNull())
    
    # Trim string columns
    for field in df.schema.fields:
        if str(field.dataType) == "StringType":
            df = df.withColumn(field.name, trim(col(field.name)))
    
    # Standardize text fields
    if "standardize_fields" in (rules or {}):
        for field in rules["standardize_fields"]:
            df = df.withColumn(field, upper(trim(col(field))))
    
    # Handle invalid numeric values
    numeric_cols = [f.name for f in df.schema.fields 
                   if str(f.dataType) in ["IntegerType", "DoubleType", "FloatType"]]
    
    for col_name in numeric_cols:
        # Replace negative values with null if they should be positive
        if rules and "positive_fields" in rules and col_name in rules["positive_fields"]:
            df = df.withColumn(col_name, when(col(col_name) < 0, None).otherwise(col(col_name)))
    
    return df


def read_silver_table(table_name: str) -> DataFrame:
    """
    Read a silver Delta table
    
    Args:
        table_name: Name of the silver table
    
    Returns:
        DataFrame: Spark DataFrame
    """
    from app.spark_services.spark_session import get_spark_session
    spark = get_spark_session()
    silver_path = f"{settings.SILVER_LAYER_PATH}/{table_name}"
    
    logger.info(f"Reading silver table: {silver_path}")
    
    return spark.read.format("delta").load(silver_path)
