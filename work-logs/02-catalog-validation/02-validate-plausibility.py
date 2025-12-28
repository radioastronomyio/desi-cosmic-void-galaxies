#!/usr/bin/env python3
"""
Script Name  : 02-validate-plausibility.py
Description  : Stage 2 physical plausibility validation for DESI catalogs
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-08-04
Phase        : Phase 02 - Catalog Validation
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Validates the physical plausibility of DESI cosmic void analysis data. Applies
quality cuts, generates distribution diagnostic plots, validates astrophysical
scaling relations (mass-z, SFR-mass main sequence, sSFR quenching), and
analyzes void-finder systematics. Produces publication-quality figures.

Usage
-----
    python 02-validate-plausibility.py

Examples
--------
    python 02-validate-plausibility.py
        Runs full Stage 2 validation on complete dataset.
"""

# =============================================================================
# Imports
# =============================================================================

import configparser
import logging
import os
import sys
import warnings
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # Server-optimized backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr

warnings.filterwarnings("ignore")

# =============================================================================
# Configuration
# =============================================================================

LOG_FILE = "validation_stage2.log"

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


def setup_plotting() -> None:
    """Configure maximum quality plotting parameters."""
    plt.rcParams.update({
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "figure.figsize": (12, 9),
        "font.size": 14,
        "axes.linewidth": 1.5,
        "lines.linewidth": 2,
        "patch.linewidth": 1.5,
        "grid.linewidth": 1,
        "xtick.major.width": 1.5,
        "ytick.major.width": 1.5,
        "font.family": "serif",
        "mathtext.fontset": "dejavuserif",
        "axes.formatter.use_mathtext": True,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1,
        "savefig.format": "png",
    })
    sns.set_palette("deep")
    sns.set_style("whitegrid", {"grid.linewidth": 0.5})


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


def create_output_directories() -> None:
    """Create organized output directory structure."""
    directories = [
        "validation_plots",
        "validation_plots/distributions",
        "validation_plots/scaling_relations",
        "validation_plots/void_analysis",
        "validation_plots/publication_ready",
        "validation_data",
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


class Stage2Validator:
    """
    Validates physical plausibility for DESI catalogs.
    
    Stage 2 applies astrophysical domain knowledge to verify that data values
    are scientifically reasonable. This catches issues that pass structural
    validation but would produce nonsensical science (e.g., negative stellar
    masses, impossible redshifts, broken scaling relations).
    
    Key validations:
      - Distribution shapes match expected survey populations
      - Scaling relations (mass-z, SFR-mass main sequence) show expected behavior
      - Void-finder algorithms produce consistent (if not identical) results
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.db_config = load_config()
        self.validation_results = {
            "distribution_checks": {},
            "scaling_relations": {},
            "void_systematics": {},
            "summary": {"total_plots": 0, "warnings": [], "red_flags": []},
        }
        create_output_directories()

    def log_result(
        self, check_name: str, status: str, details: str = None, warning: bool = False
    ) -> None:
        """Log and track validation results."""
        if warning:
            self.validation_results["summary"]["warnings"].append(
                f"{check_name}: {details}"
            )
            self.logger.warning(f"⚠️  {check_name}: {details}")
        elif status == "RED_FLAG":
            self.validation_results["summary"]["red_flags"].append(
                f"{check_name}: {details}"
            )
            self.logger.error(f"🚨 RED FLAG - {check_name}: {details}")
        else:
            self.logger.info(f"✅ {check_name}: {status}")
            if details:
                self.logger.info(f"   {details}")

    def load_galaxy_data(self, sample_size: int = None) -> pd.DataFrame:
        """
        Load galaxy data from FastSpecFit catalog with quality cuts.
        
        Quality cuts remove edge cases that would distort distributions:
          - z: 0.001-1.0 excludes failed redshifts and high-z interlopers
          - logmstar: 6-13 spans dwarf to BCG masses (log solar masses)
          - d4000: 0.5-5.0 covers physical range of 4000Å break
          - sfr > -50: allows quenched galaxies while excluding failures
        
        These are deliberately relaxed cuts — Stage 2 is about identifying
        outliers, not removing them preemptively.
        """
        self.logger.info("Loading galaxy data from FastSpecFit catalog...")

        try:
            conn = get_db_connection(
                self.db_config, self.db_config["dbname_fastspecfit"]
            )

            query = """
            SELECT 
                targetid, ra, dec, z, z_err, 
                logmstar, logmstar_err, sfr, sfr_err,
                age_gyr, metallicity, d4000, healpix_id
            FROM raw_catalogs.fastspecfit_galaxies
            WHERE z IS NOT NULL 
            AND logmstar IS NOT NULL 
            AND sfr IS NOT NULL
            AND logmstar BETWEEN 6.0 AND 13.0
            AND d4000 BETWEEN 0.5 AND 5.0
            AND z BETWEEN 0.001 AND 1.0
            AND sfr > -50
            """

            if sample_size:
                query += f" ORDER BY RANDOM() LIMIT {sample_size}"

            self.logger.info(
                "Executing query... (this may take a few minutes for full dataset)"
            )
            df = pd.read_sql(query, conn)
            conn.close()

            # Derived quantities for quenching analysis.
            # AI NOTE: The 1e-15 floor in log_ssfr prevents -inf from zero SFR.
            # This is a numerical convenience, not a physical limit. Downstream
            # analysis should treat log_ssfr < -14 as "effectively zero SFR."
            self.logger.info("Calculating derived quantities...")
            df["ssfr"] = df["sfr"] / (10 ** df["logmstar"])
            df["log_ssfr"] = np.log10(df["ssfr"] + 1e-15)
            df["stellar_mass"] = 10 ** df["logmstar"]

            df["high_quality"] = (
                (df["z_err"] < 0.001)
                & (df["logmstar_err"] < 0.05)
                & (df["sfr_err"] < df["sfr"])
            )

            self.logger.info(
                f"Loaded {len(df):,} galaxies with relaxed quality cuts applied"
            )
            self.logger.info(
                f"Quality cuts removed ~{(6445927 - len(df))/6445927*100:.1f}% of raw data"
            )
            return df

        except Exception as e:
            self.logger.error(f"Failed to load galaxy data: {e}")
            raise

    def load_void_data(self) -> pd.DataFrame:
        """Load void data from DESIVAST catalog."""
        self.logger.info("Loading void data from DESIVAST catalog...")

        try:
            conn = get_db_connection(self.db_config, self.db_config["dbname_desivast"])

            query = """
            SELECT 
                void_id, algorithm, original_void_index, 
                ra, dec, x_mpc_h, y_mpc_h, z_mpc_h, 
                radius_mpc_h, edge_flag, redshift,
                galactic_cap, source_file
            FROM raw_catalogs.desivast_voids
            WHERE algorithm IS NOT NULL
            AND radius_mpc_h IS NOT NULL
            """

            df = pd.read_sql(query, conn)
            conn.close()

            self.logger.info(
                f"Loaded {len(df):,} voids across algorithms: {df['algorithm'].unique()}"
            )
            return df

        except Exception as e:
            self.logger.error(f"Failed to load void data: {e}")
            raise

    def plot_distribution_diagnostics(self, galaxy_df: pd.DataFrame) -> None:
        """Generate comprehensive distribution diagnostic plots."""
        self.logger.info("\n=== GENERATING DISTRIBUTION DIAGNOSTICS ===")

        # 1. Stellar Mass Distribution
        plt.figure(figsize=(12, 9))
        plt.hist(
            galaxy_df["logmstar"],
            bins=100,
            density=True,
            alpha=0.7,
            color="steelblue",
            edgecolor="black",
            linewidth=0.5,
        )
        plt.axvline(
            galaxy_df["logmstar"].median(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f'Median: {galaxy_df["logmstar"].median():.2f}',
        )
        plt.xlabel(r"Stellar Mass (log$_{10}$ M$_{\odot}$)")
        plt.ylabel("Normalized Density")
        plt.title(
            "FastSpecFit v3.0 Stellar Mass Distribution\nDESI DR1 Validation",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        mean_mass = galaxy_df["logmstar"].mean()
        std_mass = galaxy_df["logmstar"].std()
        plt.text(
            0.95,
            0.95,
            f"Mean: {mean_mass:.2f}\nStd: {std_mass:.2f}\nN: {len(galaxy_df):,}",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        plt.savefig(
            "validation_plots/distributions/stellar_mass_distribution.png", dpi=300
        )
        plt.close()

        if galaxy_df["logmstar"].min() < 5.0 or galaxy_df["logmstar"].max() > 14.0:
            self.log_result(
                "Stellar mass range",
                "RED_FLAG",
                f"Extreme masses detected: {galaxy_df['logmstar'].min():.1f} to {galaxy_df['logmstar'].max():.1f}",
            )
        else:
            self.log_result(
                "Stellar mass distribution",
                "PASS",
                f"Survey-appropriate range: {galaxy_df['logmstar'].min():.1f} to {galaxy_df['logmstar'].max():.1f}",
            )

        # 2. Star Formation Rate Distribution
        plt.figure(figsize=(12, 9))

        sfr_positive = galaxy_df[galaxy_df["sfr"] > 0]["sfr"]
        log_sfr = np.log10(sfr_positive)

        plt.hist(
            log_sfr,
            bins=100,
            density=True,
            alpha=0.7,
            color="orange",
            edgecolor="black",
            linewidth=0.5,
        )
        plt.axvline(
            log_sfr.median(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Median: {log_sfr.median():.2f}",
        )
        plt.xlabel(r"Star Formation Rate (log$_{10}$ M$_{\odot}$ yr$^{-1}$)")
        plt.ylabel("Normalized Density")
        plt.title(
            "FastSpecFit v3.0 Star Formation Rate Distribution\nDESI DR1 Validation",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        zero_sfr_fraction = (galaxy_df["sfr"] == 0).sum() / len(galaxy_df) * 100
        plt.text(
            0.95,
            0.95,
            f"Zero SFR: {zero_sfr_fraction:.1f}%\nN > 0: {len(sfr_positive):,}",
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        plt.savefig("validation_plots/distributions/sfr_distribution.png", dpi=300)
        plt.close()

        negative_sfr = (galaxy_df["sfr"] < 0).sum()
        if negative_sfr > 0:
            self.log_result(
                "SFR physical validity",
                "RED_FLAG",
                f"{negative_sfr} galaxies with negative SFR",
            )
        else:
            self.log_result("SFR distribution", "PASS", "No negative SFR values")

        # 3. Redshift Distribution
        plt.figure(figsize=(12, 9))
        plt.hist(
            galaxy_df["z"],
            bins=100,
            density=True,
            alpha=0.7,
            color="green",
            edgecolor="black",
            linewidth=0.5,
        )
        plt.axvline(
            galaxy_df["z"].median(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f'Median: {galaxy_df["z"].median():.3f}',
        )
        plt.xlabel("Redshift (z)")
        plt.ylabel("Normalized Density")
        plt.title("DESI DR1 Redshift Distribution\nBright Galaxy Survey", fontsize=16)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        plt.text(
            0.95,
            0.95,
            f'Range: {galaxy_df["z"].min():.3f} - {galaxy_df["z"].max():.3f}\nN: {len(galaxy_df):,}',
            transform=plt.gca().transAxes,
            ha="right",
            va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        plt.savefig(
            "validation_plots/distributions/redshift_distribution.png", dpi=300
        )
        plt.close()

        # 4. D4000 Break Strength Distribution
        plt.figure(figsize=(12, 9))
        d4000_clean = galaxy_df["d4000"].dropna()

        if len(d4000_clean) > 0:
            plt.hist(
                d4000_clean,
                bins=100,
                density=True,
                alpha=0.7,
                color="purple",
                edgecolor="black",
                linewidth=0.5,
            )
            plt.axvline(
                d4000_clean.median(),
                color="red",
                linestyle="--",
                linewidth=2,
                label=f"Median: {d4000_clean.median():.2f}",
            )
            plt.xlabel("4000Å Break Strength (D4000)")
            plt.ylabel("Normalized Density")
            plt.title(
                "4000Å Break Strength Distribution\nStar Formation Indicator",
                fontsize=16,
            )
            plt.legend(fontsize=12)
            plt.grid(True, alpha=0.3)

            # D4000 > 1.6 is the canonical threshold for "passive" galaxies.
            # This break strength indicates an old stellar population with few
            # hot O/B stars to fill in the 4000Å absorption feature.
            passive_fraction = (d4000_clean > 1.6).sum() / len(d4000_clean) * 100
            plt.text(
                0.95,
                0.95,
                f"D4000 > 1.6: {passive_fraction:.1f}%\nN: {len(d4000_clean):,}",
                transform=plt.gca().transAxes,
                ha="right",
                va="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )

            plt.savefig(
                "validation_plots/distributions/d4000_distribution.png", dpi=300
            )
            plt.close()

            if d4000_clean.min() < 0.5 or d4000_clean.max() > 5.0:
                self.log_result(
                    "D4000 distribution",
                    "PASS",
                    f"Some outliers remain: {d4000_clean.min():.2f} to {d4000_clean.max():.2f}",
                    warning=True,
                )
            else:
                self.log_result(
                    "D4000 distribution",
                    "PASS",
                    f"Excellent range: {d4000_clean.min():.2f} to {d4000_clean.max():.2f}",
                )
        else:
            self.log_result(
                "D4000 distribution", "FAIL", "No valid D4000 measurements found"
            )

        self.log_result(
            "Distribution diagnostics", "COMPLETE", "Generated 4 distribution plots"
        )

    def plot_scaling_relations(self, galaxy_df: pd.DataFrame) -> None:
        """Generate critical astrophysical scaling relation diagnostics."""
        self.logger.info("\n=== GENERATING SCALING RELATION DIAGNOSTICS ===")

        # 1. Mass vs Redshift (FastSpecFit v1.0 bug test)
        plt.figure(figsize=(14, 10))

        plt.hexbin(
            galaxy_df["z"],
            galaxy_df["logmstar"],
            gridsize=75,
            cmap="viridis",
            mincnt=1,
            alpha=0.8,
        )
        cb = plt.colorbar(label="Galaxy Count")
        cb.ax.tick_params(labelsize=12)

        z_data = galaxy_df["z"].values
        mass_data = galaxy_df["logmstar"].values

        # Mass-redshift correlation test: A strong positive correlation in a
        # magnitude-limited survey is expected (Malmquist bias — at higher z,
        # only intrinsically brighter/more massive galaxies are detectable).
        # HOWEVER, FastSpecFit v1.0 had a known bug causing spurious mass-z
        # correlation from incorrect template matching. This plot distinguishes
        # expected selection effects from systematic fitting errors.
        corr_coeff, p_value = pearsonr(z_data, mass_data)

        z_bins = np.linspace(galaxy_df["z"].min(), galaxy_df["z"].max(), 20)
        z_bin_centers = (z_bins[:-1] + z_bins[1:]) / 2
        median_masses = []

        for i in range(len(z_bins) - 1):
            mask = (z_data >= z_bins[i]) & (z_data < z_bins[i + 1])
            if mask.sum() > 10:
                median_masses.append(np.median(mass_data[mask]))
            else:
                median_masses.append(np.nan)

        plt.plot(
            z_bin_centers,
            median_masses,
            "r-",
            linewidth=3,
            label=f"Running Median\nr = {corr_coeff:.3f}",
        )

        plt.xlabel("Redshift (z)", fontsize=14)
        plt.ylabel(r"Stellar Mass (log$_{10}$ M$_{\odot}$)", fontsize=14)
        plt.title(
            "CRITICAL: Mass vs Redshift Diagnostic (Quality Sample)\n"
            "Test for FastSpecFit v1.0 Systematic Bias",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        plt.text(
            0.05,
            0.95,
            f"Pearson r = {corr_coeff:.4f}\np-value = {p_value:.2e}\nN = {len(galaxy_df):,}",
            transform=plt.gca().transAxes,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
        )

        plt.savefig(
            "validation_plots/scaling_relations/mass_vs_redshift_critical.png", dpi=300
        )
        plt.close()

        # AI NOTE: Correlation thresholds are empirically calibrated:
        #   r > 0.8: Likely systematic error (too strong for selection alone)
        #   0.5 < r < 0.8: Consistent with Malmquist bias in magnitude-limited survey
        #   r < 0.5: Acceptable; selection effects not dominant
        # These boundaries are approximate — consult literature if recalibrating.
        if abs(corr_coeff) > 0.8:
            self.log_result(
                "Mass-Redshift Correlation",
                "RED_FLAG",
                f"Extremely strong correlation r={corr_coeff:.3f} suggests systematic bias",
            )
        elif abs(corr_coeff) > 0.5:
            self.log_result(
                "Mass-Redshift Correlation",
                "PASS",
                f"Strong correlation r={corr_coeff:.3f} - consistent with survey selection (Malmquist bias)",
                warning=True,
            )
        else:
            self.log_result(
                "Mass-Redshift Correlation",
                "PASS",
                f"Moderate correlation r={corr_coeff:.3f} - acceptable for magnitude-limited survey",
            )

        # 2. SFR-Mass Main Sequence
        plt.figure(figsize=(14, 10))

        sf_galaxies = galaxy_df[galaxy_df["sfr"] > 0].copy()

        if len(sf_galaxies) > 0:
            plt.hexbin(
                sf_galaxies["logmstar"],
                np.log10(sf_galaxies["sfr"]),
                gridsize=75,
                cmap="plasma",
                mincnt=1,
                alpha=0.8,
            )
            cb = plt.colorbar(label="Galaxy Count")
            cb.ax.tick_params(labelsize=12)

            mass_bins = np.linspace(
                sf_galaxies["logmstar"].min(), sf_galaxies["logmstar"].max(), 15
            )
            mass_centers = (mass_bins[:-1] + mass_bins[1:]) / 2
            median_sfr = []

            for i in range(len(mass_bins) - 1):
                mask = (sf_galaxies["logmstar"] >= mass_bins[i]) & (
                    sf_galaxies["logmstar"] < mass_bins[i + 1]
                )
                if mask.sum() > 10:
                    log_sfr_bin = np.log10(sf_galaxies.loc[mask, "sfr"])
                    median_sfr.append(np.median(log_sfr_bin))
                else:
                    median_sfr.append(np.nan)

            valid_mask = ~np.isnan(median_sfr)
            plt.plot(
                mass_centers[valid_mask],
                np.array(median_sfr)[valid_mask],
                "r-",
                linewidth=3,
                label="Main Sequence",
            )

            if np.sum(valid_mask) > 3:
                main_seq_fit = np.polyfit(
                    mass_centers[valid_mask], np.array(median_sfr)[valid_mask], 1
                )
                slope, intercept = main_seq_fit

                plt.text(
                    0.05,
                    0.95,
                    f"Main Sequence Slope: {slope:.2f}\nIntercept: {intercept:.2f}",
                    transform=plt.gca().transAxes,
                    ha="left",
                    va="top",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
                )

                # The star-forming main sequence has a well-established slope
                # of ~0.6-1.0 in the local universe. Slopes outside 0.4-1.2
                # suggest systematic issues with SFR or mass estimates.
                if 0.4 < slope < 1.2:
                    self.log_result(
                        "Main Sequence Slope",
                        "PASS",
                        f"Slope {slope:.2f} within expected range",
                    )
                else:
                    self.log_result(
                        "Main Sequence Slope",
                        "RED_FLAG",
                        f"Slope {slope:.2f} outside expected range (0.4-1.2)",
                    )

        plt.xlabel(r"Stellar Mass (log$_{10}$ M$_{\odot}$)", fontsize=14)
        plt.ylabel(r"Star Formation Rate (log$_{10}$ M$_{\odot}$ yr$^{-1}$)", fontsize=14)
        plt.title(
            "Star Formation Main Sequence (Quality Sample)\n"
            "DESI DR1 FastSpecFit Validation",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        plt.savefig(
            "validation_plots/scaling_relations/sfr_mass_main_sequence.png", dpi=300
        )
        plt.close()

        # 3. Specific Star Formation Rate vs Mass
        plt.figure(figsize=(14, 10))

        plt.hexbin(
            galaxy_df["logmstar"],
            galaxy_df["log_ssfr"],
            gridsize=75,
            cmap="coolwarm",
            mincnt=1,
            alpha=0.8,
        )
        cb = plt.colorbar(label="Galaxy Count")
        cb.ax.tick_params(labelsize=12)

        # log(sSFR) = -11 yr^-1 is the standard quenching threshold.
        # Galaxies below this have specific star formation rates too low to
        # significantly grow their stellar mass on cosmological timescales.
        quench_threshold = -11.0
        plt.axhline(
            quench_threshold,
            color="black",
            linestyle="--",
            linewidth=2,
            label=f"Quenching Threshold\nlog(sSFR) = {quench_threshold}",
        )

        plt.xlabel(r"Stellar Mass (log$_{10}$ M$_{\odot}$)", fontsize=14)
        plt.ylabel(r"Specific SFR (log$_{10}$ yr$^{-1}$)", fontsize=14)
        plt.title(
            "Specific Star Formation Rate vs Mass (Quality Sample)\n"
            "Quenching Analysis Diagnostic",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)

        quenched_fraction = (
            (galaxy_df["log_ssfr"] < quench_threshold).sum() / len(galaxy_df) * 100
        )
        plt.text(
            0.05,
            0.05,
            f"Quenched Fraction: {quenched_fraction:.1f}%\nN = {len(galaxy_df):,}",
            transform=plt.gca().transAxes,
            ha="left",
            va="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
        )

        plt.savefig(
            "validation_plots/scaling_relations/ssfr_vs_mass_quenching.png", dpi=300
        )
        plt.close()

        self.log_result(
            "Scaling relations", "COMPLETE", "Generated 3 scaling relation plots"
        )

    def plot_void_systematics(self, void_df: pd.DataFrame) -> None:
        """Analyze systematic differences between void-finding algorithms."""
        self.logger.info("\n=== ANALYZING VOID-FINDER SYSTEMATICS ===")

        algorithms = void_df["algorithm"].unique()
        self.logger.info(f"Found algorithms: {algorithms}")

        # 1. Void Size Distribution Comparison
        plt.figure(figsize=(14, 10))

        colors = ["red", "blue", "green", "orange", "purple"]
        for i, algo in enumerate(algorithms):
            algo_data = void_df[void_df["algorithm"] == algo]

            plt.hist(
                algo_data["radius_mpc_h"],
                bins=50,
                alpha=0.6,
                density=True,
                label=f"{algo} (N={len(algo_data):,})",
                color=colors[i % len(colors)],
                edgecolor="black",
                linewidth=0.5,
            )

        plt.xlabel("Void Radius (Mpc/h)", fontsize=14)
        plt.ylabel("Normalized Density", fontsize=14)
        plt.title(
            "Void Size Distribution by Algorithm\n"
            "DESIVAST DR1 Systematic Comparison",
            fontsize=16,
        )
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.yscale("log")

        plt.savefig(
            "validation_plots/void_analysis/void_size_distributions.png", dpi=300
        )
        plt.close()

        size_stats = void_df.groupby("algorithm")["radius_mpc_h"].agg(
            ["count", "mean", "std", "median"]
        )
        self.logger.info("Void size statistics by algorithm:")
        self.logger.info("\n" + size_stats.to_string())

        # 2. Galactic Cap Distribution Analysis
        if "galactic_cap" in void_df.columns:
            plt.figure(figsize=(12, 9))

            cap_algo_counts = (
                void_df.groupby(["algorithm", "galactic_cap"]).size().unstack(fill_value=0)
            )
            cap_algo_counts.plot(kind="bar", stacked=True, color=["red", "blue"], alpha=0.7)

            plt.xlabel("Algorithm")
            plt.ylabel("Number of Voids")
            plt.title(
                "Void Distribution by Algorithm and Galactic Cap\nNGC vs SGC Coverage"
            )
            plt.legend(title="Galactic Cap")
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(
                "validation_plots/void_analysis/void_galactic_cap_distribution.png",
                dpi=300,
            )
            plt.close()

        # 3. Void Spatial Distribution
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()

        for i, algo in enumerate(algorithms[:4]):
            if i < len(axes):
                algo_data = void_df[void_df["algorithm"] == algo]

                scatter = axes[i].scatter(
                    algo_data["ra"],
                    algo_data["dec"],
                    c=algo_data["radius_mpc_h"],
                    cmap="viridis",
                    s=20,
                    alpha=0.7,
                )
                axes[i].set_xlabel("RA (degrees)")
                axes[i].set_ylabel("DEC (degrees)")
                axes[i].set_title(f"{algo} Void Distribution\n(N={len(algo_data):,})")
                axes[i].grid(True, alpha=0.3)

                cbar = plt.colorbar(scatter, ax=axes[i])
                cbar.set_label("Radius (Mpc/h)", fontsize=10)

        for i in range(len(algorithms), len(axes)):
            fig.delaxes(axes[i])

        plt.tight_layout()
        plt.savefig(
            "validation_plots/void_analysis/void_spatial_distribution.png", dpi=300
        )
        plt.close()

        algo_counts = void_df["algorithm"].value_counts()
        algo_median_sizes = void_df.groupby("algorithm")["radius_mpc_h"].median()

        count_ratio = algo_counts.max() / algo_counts.min()
        size_ratio = algo_median_sizes.max() / algo_median_sizes.min()

        if count_ratio > 5:
            self.log_result(
                "Void count systematic",
                "RED_FLAG",
                f"Large count differences between algorithms (ratio: {count_ratio:.1f})",
            )
        else:
            self.log_result(
                "Void count variation",
                "PASS",
                f"Reasonable count variation (ratio: {count_ratio:.1f})",
            )

        if size_ratio > 2:
            self.log_result(
                "Void size systematic",
                "PASS",
                f"Moderate size differences (ratio: {size_ratio:.1f})",
                warning=True,
            )
        else:
            self.log_result(
                "Void size consistency",
                "PASS",
                f"Good size consistency (ratio: {size_ratio:.1f})",
            )

        self.log_result(
            "Void systematics", "COMPLETE", f"Analyzed {len(algorithms)} algorithms"
        )

    def generate_summary_report(
        self, galaxy_df: pd.DataFrame, void_df: pd.DataFrame
    ) -> None:
        """Generate comprehensive validation summary."""
        self.logger.info("\n=== GENERATING VALIDATION SUMMARY ===")

        summary_stats = {
            "Galaxy Sample (Quality Cuts Applied)": {
                "Total Galaxies": f"{len(galaxy_df):,}",
                "Quality Cut Retention": f"{len(galaxy_df)/6445927*100:.1f}% of raw data",
                "Redshift Range": f'{galaxy_df["z"].min():.3f} - {galaxy_df["z"].max():.3f}',
                "Mass Range (log)": f'{galaxy_df["logmstar"].min():.2f} - {galaxy_df["logmstar"].max():.2f}',
                "SFR Range (log)": f'{np.log10(galaxy_df[galaxy_df["sfr"] > 0]["sfr"]).min():.2f} - {np.log10(galaxy_df[galaxy_df["sfr"] > 0]["sfr"]).max():.2f}',
                "Quenched Fraction": f'{(galaxy_df["log_ssfr"] < -11).sum() / len(galaxy_df) * 100:.1f}%',
                "High Quality": f'{galaxy_df["high_quality"].sum():,} ({galaxy_df["high_quality"].mean()*100:.1f}%)',
            },
            "Void Sample": {
                "Total Voids": f"{len(void_df):,}",
                "Algorithms": ", ".join(void_df["algorithm"].unique()),
                "Radius Range": f'{void_df["radius_mpc_h"].min():.1f} - {void_df["radius_mpc_h"].max():.1f} Mpc/h',
                "Median Radius": f'{void_df["radius_mpc_h"].median():.1f} Mpc/h',
            },
        }

        with open("validation_data/stage2_summary.txt", "w") as f:
            f.write("DESI Cosmic Void Analysis - Stage 2 Validation Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for category, stats in summary_stats.items():
                f.write(f"{category}:\n")
                for key, value in stats.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")

            if self.validation_results["summary"]["red_flags"]:
                f.write("RED FLAGS:\n")
                for flag in self.validation_results["summary"]["red_flags"]:
                    f.write(f"  🚨 {flag}\n")
                f.write("\n")

            if self.validation_results["summary"]["warnings"]:
                f.write("WARNINGS:\n")
                for warning in self.validation_results["summary"]["warnings"]:
                    f.write(f"  ⚠️  {warning}\n")

        self.logger.info("Summary report saved to validation_data/stage2_summary.txt")

    def run_validation(self, sample_size: int = None) -> bool:
        """Run complete Stage 2 validation."""
        self.logger.info("🔬 STARTING STAGE 2 PHYSICAL PLAUSIBILITY VALIDATION")
        self.logger.info("=" * 70)

        try:
            self.logger.info("Loading datasets...")
            galaxy_df = self.load_galaxy_data(sample_size)
            void_df = self.load_void_data()

            self.plot_distribution_diagnostics(galaxy_df)
            self.plot_scaling_relations(galaxy_df)
            self.plot_void_systematics(void_df)

            self.generate_summary_report(galaxy_df, void_df)

            n_red_flags = len(self.validation_results["summary"]["red_flags"])
            n_warnings = len(self.validation_results["summary"]["warnings"])

            self.logger.info("\n" + "=" * 70)
            self.logger.info("📊 STAGE 2 VALIDATION SUMMARY")
            self.logger.info("=" * 70)
            self.logger.info(f"🚨 Red Flags: {n_red_flags}")
            self.logger.info(f"⚠️  Warnings: {n_warnings}")

            plot_counts = 0
            for subdir in ["distributions", "scaling_relations", "void_analysis"]:
                plot_dir = f"validation_plots/{subdir}"
                if os.path.exists(plot_dir):
                    plot_counts += len(
                        [f for f in os.listdir(plot_dir) if f.endswith(".png")]
                    )

            self.logger.info(f"📈 Plots Generated: {plot_counts}")

            if n_red_flags == 0:
                self.logger.info("🎉 PHYSICAL PLAUSIBILITY VALIDATION PASSED!")
                self.logger.info(
                    "Data appears scientifically sound for cosmic void analysis."
                )
                return True
            else:
                self.logger.error("💥 PHYSICAL PLAUSIBILITY ISSUES DETECTED!")
                self.logger.error(
                    "Review red flags before proceeding with scientific analysis."
                )
                return False

        except Exception as e:
            self.logger.error(f"Validation failed with critical error: {e}")
            return False


def main() -> int:
    """Entry point for script execution."""
    logger = setup_logging()
    setup_plotting()

    try:
        validator = Stage2Validator(logger)

        use_sample = False
        sample_size = 100000 if use_sample else None

        if use_sample:
            logger.info(f"Running validation on {sample_size:,} galaxy sample for speed")
        else:
            logger.info("Running validation on FULL dataset for maximum accuracy")

        success = validator.run_validation(sample_size)

        if success:
            logger.info("\n✅ Stage 2 validation completed successfully.")
            logger.info("Data is ready for scientific void analysis.")
            logger.info("\nGenerated plots available in validation_plots/")
            return 0
        else:
            logger.error("\n❌ Stage 2 validation failed.")
            logger.error("Address physical plausibility issues before proceeding.")
            return 1

    except Exception as e:
        logger.error(f"Critical error during validation: {e}")
        return 1


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
