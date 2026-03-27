import os
import shutil
import subprocess
import sys

from pyspark.sql import SparkSession
from delta.pip_utils import configure_spark_with_delta_pip

from app.config import settings
from app.logger import logger

_spark_session = None


def _build_package_list() -> list[str]:
    packages = [settings.SPARK_DELTA_PACKAGE]
    extra_packages = [item.strip() for item in settings.SPARK_EXTRA_PACKAGES.split(",") if item.strip()]
    packages.extend(extra_packages)
    return packages


def _log_runtime_diagnostics() -> None:
    java_bin = shutil.which("java")
    logger.info("Python executable: %s", sys.executable)
    logger.info("JAVA_HOME: %s", os.getenv("JAVA_HOME", ""))
    logger.info("SPARK_MASTER: %s", settings.SPARK_MASTER)
    logger.info("Spark packages: %s", ", ".join(_build_package_list()))
    logger.info("java binary: %s", java_bin or "not found")

    if not java_bin:
        logger.error("Java runtime not found in PATH. Install OpenJDK 21 and set JAVA_HOME.")
        return

    try:
        result = subprocess.run(
            [java_bin, "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
        java_version_output = (result.stderr or result.stdout).strip()
        if java_version_output:
            logger.info("java -version: %s", java_version_output.replace("\n", " | "))
    except OSError as exc:
        logger.warning("Unable to read Java runtime version: %s", exc)


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
        os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
        os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
        os.environ.setdefault("SPARK_LOCAL_IP", settings.SPARK_LOCAL_IP)
        _log_runtime_diagnostics()

        packages = ",".join(_build_package_list())
        builder = (
            SparkSession.builder
            .appName(app_name)
            .master(settings.SPARK_MASTER)
            # Memory configuration
            .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
            .config("spark.executor.memory", settings.SPARK_EXECUTOR_MEMORY)
            .config("spark.driver.maxResultSize", settings.SPARK_DRIVER_MAX_RESULT_SIZE)
            # Delta Lake configuration
            .config("spark.jars.packages", packages)
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            # Performance optimization
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            # Python worker configuration
            .config("spark.python.worker.reuse", "true")
        )
        
        _spark_session = configure_spark_with_delta_pip(
            builder,
            extra_packages=[pkg for pkg in _build_package_list() if pkg != settings.SPARK_DELTA_PACKAGE],
        ).getOrCreate()
        
        logger.info(f"Spark session created: {_spark_session}")
        logger.info(f"Spark version: {_spark_session.version}")
        
        return _spark_session
    except Exception as e:
        logger.error(
            "Failed to create Spark session. Check Java 21 availability, JAVA_HOME, and Spark/Delta package resolution.",
            exc_info=True,
        )
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
