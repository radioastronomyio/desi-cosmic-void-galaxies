#!/usr/bin/env python3
"""
Script Name  : 01-validate-integrity.py
Description  : Stage 1 database integrity validation for DESI catalogs
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-08-04
Phase        : Phase 02 - Catalog Validation
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Validates the integrity of DESI cosmic void analysis databases. Performs
foundational checks on schema structure, primary key uniqueness, foreign key
relationships, and NULL value assessment. Part of a three-stage validation
framework: integrity → plausibility → systematic uncertainty.

Usage
-----
    python 01-validate-integrity.py

Examples
--------
    python 01-validate-integrity.py
        Runs all Stage 1 integrity checks and outputs to validation_stage1.log.
"""

# =============================================================================
# Imports
# =============================================================================

import configparser
import logging
import sys

import pandas as pd
import psycopg2

# =============================================================================
# Configuration
# =============================================================================

LOG_FILE = "validation_stage1.log"

# =============================================================================
# Functions
# =============================================================================


def setup_logging() -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def load_config() -> dict:
    """Load database configuration from config.ini."""
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config["database"]


def get_db_connection(db_config: dict, database_name: str):
    """Establish database connection."""
    try:
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=database_name,
        )
        return conn
    except psycopg2.Error as e:
        raise Exception(f"Failed to connect to {database_name}: {e}")


def execute_query(conn, query: str, description: str = "Query") -> tuple:
    """Execute a query and return results."""
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        return results, columns
    except psycopg2.Error as e:
        raise Exception(f"{description} failed: {e}")


class Stage1Validator:
    """
    Validates database integrity for DESI catalogs.
    
    Part of a three-stage validation framework:
      Stage 1 (this): Schema, keys, NULLs, data types — "is the data structurally sound?"
      Stage 2: Physical plausibility — "do values make astrophysical sense?"
      Stage 3: Systematic uncertainty — "how do algorithm choices affect results?"
    
    Stage 1 must pass before Stage 2 is meaningful. Database schema and
    completeness issues would invalidate any scientific analysis downstream.
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.db_config = load_config()
        self.validation_results = {
            "schema_checks": {},
            "data_integrity": {},
            "completeness": {},
            "summary": {"total_checks": 0, "passed": 0, "failed": 0, "warnings": 0},
        }

    def log_result(
        self, check_name: str, status: str, details: str = None, warning: bool = False
    ) -> None:
        """Log and track validation results."""
        self.validation_results["summary"]["total_checks"] += 1

        if status == "PASS":
            self.validation_results["summary"]["passed"] += 1
            self.logger.info(f"✅ {check_name}: PASS")
        elif warning:
            self.validation_results["summary"]["warnings"] += 1
            self.logger.warning(f"⚠️  {check_name}: WARNING - {details}")
        else:
            self.validation_results["summary"]["failed"] += 1
            self.logger.error(f"❌ {check_name}: FAIL - {details}")

        if details:
            self.logger.info(f"   Details: {details}")

    def validate_schema_existence(self) -> None:
        """Validate that expected databases and schemas exist."""
        self.logger.info("\n=== SCHEMA EXISTENCE VALIDATION ===")

        # Check FastSpecFit database and schema
        try:
            conn = get_db_connection(
                self.db_config, self.db_config["dbname_fastspecfit"]
            )

            query = """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'raw_catalogs';
            """
            results, _ = execute_query(conn, query, "FastSpecFit schema check")

            if results:
                self.log_result("FastSpecFit raw_catalogs schema exists", "PASS")
            else:
                self.log_result(
                    "FastSpecFit raw_catalogs schema exists",
                    "FAIL",
                    "raw_catalogs schema not found",
                )

            query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'raw_catalogs' AND tablename = 'fastspecfit_galaxies';
            """
            results, _ = execute_query(conn, query, "FastSpecFit table check")

            if results:
                self.log_result("fastspecfit_galaxies table exists", "PASS")
            else:
                self.log_result(
                    "fastspecfit_galaxies table exists",
                    "FAIL",
                    "fastspecfit_galaxies table not found in raw_catalogs",
                )

            conn.close()

        except Exception as e:
            self.log_result("FastSpecFit database connection", "FAIL", str(e))

        # Check DESIVAST database and schema
        try:
            conn = get_db_connection(self.db_config, self.db_config["dbname_desivast"])

            query = """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'raw_catalogs';
            """
            results, _ = execute_query(conn, query, "DESIVAST schema check")

            if results:
                self.log_result("DESIVAST raw_catalogs schema exists", "PASS")
            else:
                self.log_result(
                    "DESIVAST raw_catalogs schema exists",
                    "FAIL",
                    "raw_catalogs schema not found",
                )

            query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'raw_catalogs' AND tablename = 'desivast_voids';
            """
            results, _ = execute_query(conn, query, "DESIVAST table check")

            if results:
                self.log_result("desivast_voids table exists", "PASS")
            else:
                self.log_result(
                    "desivast_voids table exists",
                    "FAIL",
                    "desivast_voids table not found in raw_catalogs",
                )

            conn.close()

        except Exception as e:
            self.log_result("DESIVAST database connection", "FAIL", str(e))

    def validate_row_counts(self) -> None:
        """
        Validate expected row counts.
        
        Expected counts are based on DESI DR1 Value Added Catalog specifications:
          - FastSpecFit: ~6.4M galaxies from BGS + LRG + ELG samples
          - DESIVAST: ~25K voids across 4 algorithms × 2 galactic caps
        
        Lower counts aren't necessarily errors — could indicate partial loads
        or different quality cuts applied upstream. Flagged as warnings.
        """
        self.logger.info("\n=== ROW COUNT VALIDATION ===")

        # FastSpecFit row count
        try:
            conn = get_db_connection(
                self.db_config, self.db_config["dbname_fastspecfit"]
            )
            query = """
            SELECT COUNT(*) 
            FROM raw_catalogs.fastspecfit_galaxies;
            """
            results, _ = execute_query(conn, query, "FastSpecFit row count")

            row_count = results[0][0]
            self.logger.info(f"FastSpecFit galaxies: {row_count:,} rows")

            # AI NOTE: These row count thresholds (6M galaxies, 20K voids) are based
            # on DESI DR1 VAC specifications. If future data releases change these
            # expectations, update thresholds here — not in the comparison logic.
            if row_count > 6000000:
                self.log_result(
                    "FastSpecFit row count reasonable", "PASS", f"{row_count:,} rows"
                )
            elif row_count > 0:
                self.log_result(
                    "FastSpecFit row count reasonable",
                    "PASS",
                    f"{row_count:,} rows (lower than expected ~6.4M)",
                    warning=True,
                )
            else:
                self.log_result(
                    "FastSpecFit row count reasonable", "FAIL", "No data found"
                )

            conn.close()

        except Exception as e:
            self.log_result("FastSpecFit row count check", "FAIL", str(e))

        # DESIVAST row count
        try:
            conn = get_db_connection(self.db_config, self.db_config["dbname_desivast"])
            query = """
            SELECT COUNT(*) 
            FROM raw_catalogs.desivast_voids;
            """
            results, _ = execute_query(conn, query, "DESIVAST row count")

            row_count = results[0][0]
            self.logger.info(f"DESIVAST voids: {row_count:,} rows")

            if row_count > 20000:
                self.log_result(
                    "DESIVAST row count reasonable", "PASS", f"{row_count:,} rows"
                )
            elif row_count > 0:
                self.log_result(
                    "DESIVAST row count reasonable",
                    "PASS",
                    f"{row_count:,} rows (lower than expected ~25K)",
                    warning=True,
                )
            else:
                self.log_result(
                    "DESIVAST row count reasonable", "FAIL", "No data found"
                )

            conn.close()

        except Exception as e:
            self.log_result("DESIVAST row count check", "FAIL", str(e))

    def validate_primary_key_uniqueness(self) -> None:
        """Validate primary key uniqueness constraints."""
        self.logger.info("\n=== PRIMARY KEY UNIQUENESS VALIDATION ===")

        # FastSpecFit TARGETID uniqueness
        try:
            conn = get_db_connection(
                self.db_config, self.db_config["dbname_fastspecfit"]
            )
            query = """
            SELECT targetid, COUNT(*) as duplicate_count
            FROM raw_catalogs.fastspecfit_galaxies
            GROUP BY targetid
            HAVING COUNT(*) > 1
            LIMIT 10;
            """
            results, _ = execute_query(conn, query, "FastSpecFit TARGETID uniqueness")

            if not results:
                self.log_result(
                    "FastSpecFit TARGETID uniqueness",
                    "PASS",
                    "No duplicate TARGETIDs found",
                )
            else:
                duplicates = len(results)
                self.log_result(
                    "FastSpecFit TARGETID uniqueness",
                    "FAIL",
                    f"Found {duplicates} duplicate TARGETID groups",
                )

            conn.close()

        except Exception as e:
            self.log_result("FastSpecFit TARGETID uniqueness check", "FAIL", str(e))

        # Check DESIVAST columns
        try:
            conn = get_db_connection(self.db_config, self.db_config["dbname_desivast"])

            query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw_catalogs' 
            AND table_name = 'desivast_voids'
            ORDER BY ordinal_position;
            """
            results, _ = execute_query(conn, query, "DESIVAST columns check")

            columns = [row[0] for row in results]
            self.logger.info(
                f"DESIVAST columns: {', '.join(columns[:10])}{'...' if len(columns) > 10 else ''}"
            )

            if "id" in columns:
                query = """
                SELECT id, COUNT(*) as duplicate_count
                FROM raw_catalogs.desivast_voids
                GROUP BY id
                HAVING COUNT(*) > 1
                LIMIT 10;
                """
                results, _ = execute_query(conn, query, "DESIVAST ID uniqueness")

                if not results:
                    self.log_result(
                        "DESIVAST ID uniqueness", "PASS", "No duplicate IDs found"
                    )
                else:
                    duplicates = len(results)
                    self.log_result(
                        "DESIVAST ID uniqueness",
                        "FAIL",
                        f"Found {duplicates} duplicate ID groups",
                    )
            else:
                self.log_result(
                    "DESIVAST primary key check",
                    "PASS",
                    "No obvious primary key column found - may be composite",
                    warning=True,
                )

            conn.close()

        except Exception as e:
            self.log_result("DESIVAST uniqueness check", "FAIL", str(e))

    def validate_null_assessment(self) -> None:
        """Assess NULL and special values in critical columns."""
        self.logger.info("\n=== NULL VALUE ASSESSMENT ===")

        # FastSpecFit critical columns
        try:
            conn = get_db_connection(
                self.db_config, self.db_config["dbname_fastspecfit"]
            )

            critical_columns = ["targetid", "ra", "dec", "z", "logmstar", "sfr"]

            for column in critical_columns:
                query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'raw_catalogs' 
                AND table_name = 'fastspecfit_galaxies'
                AND column_name = '{column}';
                """
                results, _ = execute_query(
                    conn, query, f"Column {column} existence check"
                )

                if not results:
                    self.log_result(
                        f"FastSpecFit {column} NULL check",
                        "FAIL",
                        f"Column {column} does not exist",
                    )
                    continue

                query = f"""
                SELECT 
                    SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS null_count,
                    COUNT(*) AS total_rows
                FROM raw_catalogs.fastspecfit_galaxies;
                """
                results, _ = execute_query(
                    conn, query, f"FastSpecFit {column} NULL check"
                )
                null_count, total_rows = results[0]

                null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

                if null_count == 0:
                    self.log_result(
                        f"FastSpecFit {column} completeness", "PASS", "No NULL values"
                    )
                elif null_pct < 5:
                    self.log_result(
                        f"FastSpecFit {column} completeness",
                        "PASS",
                        f"{null_pct:.2f}% NULL",
                        warning=True,
                    )
                else:
                    self.log_result(
                        f"FastSpecFit {column} completeness",
                        "FAIL",
                        f"{null_pct:.2f}% NULL",
                    )

            conn.close()

        except Exception as e:
            self.log_result("FastSpecFit NULL assessment", "FAIL", str(e))

        # DESIVAST critical columns assessment
        try:
            conn = get_db_connection(self.db_config, self.db_config["dbname_desivast"])

            query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'raw_catalogs' 
            AND table_name = 'desivast_voids'
            ORDER BY ordinal_position
            LIMIT 10;
            """
            results, _ = execute_query(conn, query, "DESIVAST columns")

            columns_to_check = [row[0] for row in results[:5]]

            for column in columns_to_check:
                query = f"""
                SELECT 
                    SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS null_count,
                    COUNT(*) AS total_rows
                FROM raw_catalogs.desivast_voids;
                """
                results, _ = execute_query(
                    conn, query, f"DESIVAST {column} NULL check"
                )
                null_count, total_rows = results[0]

                null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

                if null_count == 0:
                    self.log_result(
                        f"DESIVAST {column} completeness", "PASS", "No NULL values"
                    )
                elif null_pct < 5:
                    self.log_result(
                        f"DESIVAST {column} completeness",
                        "PASS",
                        f"{null_pct:.2f}% NULL",
                        warning=True,
                    )
                else:
                    self.log_result(
                        f"DESIVAST {column} completeness",
                        "FAIL",
                        f"{null_pct:.2f}% NULL",
                    )

            conn.close()

        except Exception as e:
            self.log_result("DESIVAST NULL assessment", "FAIL", str(e))

    def validate_data_types_and_ranges(self) -> None:
        """Validate data types and reasonable value ranges."""
        self.logger.info("\n=== DATA TYPE AND RANGE VALIDATION ===")

        try:
            conn = get_db_connection(
                self.db_config, self.db_config["dbname_fastspecfit"]
            )

            # Check RA range (0-360 degrees)
            query = """
            SELECT 
                MIN(ra) as min_ra, 
                MAX(ra) as max_ra,
                COUNT(*) as total_count,
                SUM(CASE WHEN ra < 0 OR ra > 360 THEN 1 ELSE 0 END) as invalid_ra
            FROM raw_catalogs.fastspecfit_galaxies
            WHERE ra IS NOT NULL;
            """
            results, _ = execute_query(conn, query, "RA range check")

            if results:
                min_ra, max_ra, total_count, invalid_ra = results[0]
                if invalid_ra == 0:
                    self.log_result(
                        "RA value ranges",
                        "PASS",
                        f"RA range: {min_ra:.2f} to {max_ra:.2f} degrees",
                    )
                else:
                    self.log_result(
                        "RA value ranges",
                        "FAIL",
                        f"{invalid_ra} invalid RA values (outside 0-360°)",
                    )

            # Check DEC range (-90 to +90 degrees)
            query = """
            SELECT 
                MIN(dec) as min_dec, 
                MAX(dec) as max_dec,
                SUM(CASE WHEN dec < -90 OR dec > 90 THEN 1 ELSE 0 END) as invalid_dec
            FROM raw_catalogs.fastspecfit_galaxies
            WHERE dec IS NOT NULL;
            """
            results, _ = execute_query(conn, query, "DEC range check")

            if results:
                min_dec, max_dec, invalid_dec = results[0]
                if invalid_dec == 0:
                    self.log_result(
                        "DEC value ranges",
                        "PASS",
                        f"DEC range: {min_dec:.2f} to {max_dec:.2f} degrees",
                    )
                else:
                    self.log_result(
                        "DEC value ranges",
                        "FAIL",
                        f"{invalid_dec} invalid DEC values (outside ±90°)",
                    )

            # Check redshift range (should be positive)
            query = """
            SELECT 
                MIN(z) as min_z, 
                MAX(z) as max_z,
                SUM(CASE WHEN z < 0 THEN 1 ELSE 0 END) as negative_z
            FROM raw_catalogs.fastspecfit_galaxies
            WHERE z IS NOT NULL;
            """
            results, _ = execute_query(conn, query, "Redshift range check")

            if results:
                min_z, max_z, negative_z = results[0]
                if negative_z == 0:
                    self.log_result(
                        "Redshift value ranges",
                        "PASS",
                        f"z range: {min_z:.4f} to {max_z:.4f}",
                    )
                else:
                    self.log_result(
                        "Redshift value ranges",
                        "FAIL",
                        f"{negative_z} negative redshift values",
                    )

            conn.close()

        except Exception as e:
            self.log_result("Data range validation", "FAIL", str(e))

    def run_validation(self) -> bool:
        """Run complete Stage 1 validation."""
        self.logger.info("🔍 STARTING STAGE 1 DATABASE INTEGRITY VALIDATION")
        self.logger.info("=" * 60)

        try:
            self.validate_schema_existence()
            self.validate_row_counts()
            self.validate_primary_key_uniqueness()
            self.validate_null_assessment()
            self.validate_data_types_and_ranges()

        except Exception as e:
            self.logger.error(f"Validation failed with critical error: {e}")
            return False

        # Print summary
        summary = self.validation_results["summary"]
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 STAGE 1 VALIDATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Checks: {summary['total_checks']}")
        self.logger.info(f"✅ Passed: {summary['passed']}")
        self.logger.info(f"⚠️  Warnings: {summary['warnings']}")
        self.logger.info(f"❌ Failed: {summary['failed']}")

        success_rate = (
            (summary["passed"] / summary["total_checks"] * 100)
            if summary["total_checks"] > 0
            else 0
        )
        self.logger.info(f"Success Rate: {success_rate:.1f}%")

        if summary["failed"] == 0:
            self.logger.info("🎉 DATABASE INTEGRITY VALIDATION PASSED!")
            return True
        else:
            self.logger.error("💥 DATABASE INTEGRITY ISSUES DETECTED!")
            self.logger.error("Please address failed checks before proceeding with analysis.")
            return False


def main() -> int:
    """Entry point for script execution."""
    logger = setup_logging()

    try:
        validator = Stage1Validator(logger)
        success = validator.run_validation()

        if success:
            logger.info("\n✅ Stage 1 validation completed successfully.")
            logger.info("Database is ready for Stage 2 (Physical Plausibility) validation.")
            return 0
        else:
            logger.error("\n❌ Stage 1 validation failed.")
            logger.error("Fix integrity issues before proceeding.")
            return 1

    except Exception as e:
        logger.error(f"Critical error during validation: {e}")
        return 1


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
