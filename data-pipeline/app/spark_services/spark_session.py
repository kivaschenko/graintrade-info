# src/data_pipeline/spark_services/spark_session.py
from pyspark.sql import SparkSession
from delta.pip_utils import configure_spark_with_delta_pip
from app.config import settings
from app.logger import logger

_spark_session = None


def get_spark_session(app_name: str = None) -> SparkSession:
    """
    Get or create a Spark session with Delta Lake support
    """
    global _spark_session
    
    if _spark_session is not None:
        return _spark_session
    
    app_name = app_name or settings.SPARK_APP_NAME
    
    logger.info(f"Creating Spark session: {app_name}")
    
    try:
        builder = (
            SparkSession.builder
            .appName(app_name)
            .master(settings.SPARK_MASTER)
            # Memory configuration
            .config("spark.driver.memory", "2g")
            .config("spark.executor.memory", "2g")
            .config("spark.driver.maxResultSize", "1g")
            # Delta Lake configuration
            .config("spark.jars.packages", "io.delta:delta-spark_2.13:4.0.0,org.postgresql:postgresql:42.7.3")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            # Performance optimization
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            # Python worker configuration
            .config("spark.python.worker.reuse", "true")
        )
        
        _spark_session = configure_spark_with_delta_pip(builder).getOrCreate()
        
        logger.info(f"Spark session created: {_spark_session}")
        logger.info(f"Spark version: {_spark_session.version}")
        
        return _spark_session
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}", exc_info=True)
        _spark_session = None
        raise


def stop_spark_session():
    """
    Stop the current Spark session
    """
    global _spark_session
    
    if _spark_session is not None:
        logger.info("Stopping Spark session...")
        _spark_session.stop()
        _spark_session = None
        logger.info("Spark session stopped")
