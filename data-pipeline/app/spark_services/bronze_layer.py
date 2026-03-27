# src/data_pipeline/spark_services/bronze_layer.py
from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, lit, input_file_name
from typing import Any, Optional

import pandas as pd

from app.config import settings
from app.logger import logger
from app.spark_services.spark_session import get_spark_session


def ingest_to_bronze(
    source_path: str | None = None,
    source_format: str = "csv",
    source_name: str = "unknown_source",
    table_name: str = "raw_data",
    options: Optional[dict] = None,
    source_data: Any = None,
    output_path: str | None = None,
) -> dict:
    """
    Ingest raw data to Bronze layer (Delta Lake)
    
    Args:
        source_path: Path to source data (file path or URL)
        source_format: Format of source data (csv, json, parquet, etc.)
        source_name: Name of the data source
        table_name: Name for the bronze table
        options: Additional options for reading source data
        source_data: In-memory parser output (list[dict], dict, pandas.DataFrame)
        output_path: Optional explicit Delta output path
    
    Returns:
        dict: Ingestion statistics
    """
    spark = get_spark_session()
    options = options or {}
    
    logger.info("Starting bronze ingestion for %s (%s)", source_name, source_format)
    
    try:
        # Read source data
        df = None
        if source_data is not None:
            if isinstance(source_data, pd.DataFrame):
                df = spark.createDataFrame(source_data)
            elif isinstance(source_data, list):
                df = spark.createDataFrame(source_data)
            elif isinstance(source_data, dict):
                df = spark.createDataFrame([source_data])
            else:
                raise ValueError(f"Unsupported source_data type: {type(source_data)!r}")
        elif source_format.lower() == "csv":
            if not source_path:
                raise ValueError("source_path is required for csv ingestion")
            df = spark.read.csv(source_path, header=True, inferSchema=True, **options)
        elif source_format.lower() == "json":
            if not source_path:
                raise ValueError("source_path is required for json ingestion")
            df = spark.read.json(source_path, **options)
        elif source_format.lower() == "parquet":
            if not source_path:
                raise ValueError("source_path is required for parquet ingestion")
            df = spark.read.parquet(source_path, **options)
        else:
            raise ValueError(f"Unsupported source format: {source_format}")
        
        records_read = df.count()
        logger.info(f"Read {records_read} records from source")
        
        # Add metadata columns
        df = (df
              .withColumn("_ingestion_timestamp", current_timestamp())
              .withColumn("_source_name", lit(source_name))
              .withColumn("_source_file", input_file_name()))
        
        # Write to Bronze Delta table
        bronze_path = output_path or f"{settings.BRONZE_LAYER_PATH}/{table_name}"
        
        df.write \
            .format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .save(bronze_path)
        
        logger.info(f"Written {records_read} records to bronze layer: {bronze_path}")
        
        return {
            "status": "success",
            "records_read": records_read,
            "records_written": records_read,
            "output_path": bronze_path,
        }
        
    except Exception as e:
        logger.error(f"Bronze ingestion failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "records_read": 0,
            "records_written": 0,
        }


def read_bronze_table(table_name: str) -> DataFrame:
    """
    Read a bronze Delta table
    
    Args:
        table_name: Name of the bronze table
    
    Returns:
        DataFrame: Spark DataFrame
    """
    spark = get_spark_session()
    bronze_path = f"{settings.BRONZE_LAYER_PATH}/{table_name}"
    
    logger.info(f"Reading bronze table: {bronze_path}")
    
    return spark.read.format("delta").load(bronze_path)
