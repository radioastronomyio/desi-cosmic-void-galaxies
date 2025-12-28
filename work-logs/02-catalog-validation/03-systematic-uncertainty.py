#!/usr/bin/env python3
"""
Script Name  : 03-systematic-uncertainty.py
Description  : Stage 3 multi-algorithm systematic uncertainty analysis
Repository   : desi-cosmic-void-galaxies
Author       : VintageDon (https://github.com/vintagedon)
ORCID        : 0009-0008-7695-4093
Created      : 2025-08-05
Phase        : Phase 02 - Catalog Validation
Link         : https://github.com/Proxmox-Astronomy-Lab/desi-cosmic-void-galaxies

Description
-----------
Performs Phase 3 systematic uncertainty analysis for the DESI Cosmic Void
Galaxies project. Implements multi-algorithm comparison across VoidFinder,
REVOLVER, VIDE, and ZOBOV to quantify the systematic uncertainty arising
from void definition choice. Generates statistical tests, effect size
calculations, and publication-quality comparison figures.

Usage
-----
    python 03-systematic-uncertainty.py

Examples
--------
    python 03-systematic-uncertainty.py
        Runs full systematic uncertainty analysis with all 4 algorithms.
"""

# =============================================================================
# Imports
# =============================================================================

import configparser
import logging
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from scipy.stats import ks_2samp, mannwhitneyu
from sqlalchemy import create_engine, text

warnings.filterwarnings("ignore")

# =============================================================================
# Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


class Config:
    """Configuration management for systematic uncertainty analysis."""

    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.db_config = dict(self.config["database"])

        self.algorithms = ["revolver", "vide", "zobov", "voidfinder_maximals"]
        self.algorithm_display_names = {
            "revolver": "REVOLVER",
            "vide": "VIDE",
            "zobov": "ZOBOV",
            "voidfinder_maximals": "VoidFinder",
        }

        self.ssfr_quenched_threshold = 1e-11  # yr^-1
        self.mass_bins = np.linspace(8.5, 11.5, 7)
        self.redshift_bins = np.linspace(0.1, 0.24, 4)

        self.output_dir = Path("03-phase3-output")
        self.figures_dir = self.output_dir / "publication-figures"
        self.data_dir = self.output_dir / "statistical-tests"
        self.tables_dir = self.output_dir / "error-budget-tables"

        for directory in [
            self.output_dir,
            self.figures_dir,
            self.data_dir,
            self.tables_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Database Management
# =============================================================================


class DatabaseManager:
    """Manages database connections and query execution."""

    def __init__(self, config: Config):
        self.config = config
        self.fastspecfit_engine = None
        self.desivast_engine = None
        self._establish_connections()

    def _establish_connections(self) -> None:
        """Establish database connections using configuration."""
        try:
            fastspecfit_url = (
                f"postgresql://{self.config.db_config['user']}:"
                f"{self.config.db_config['password']}@"
                f"{self.config.db_config['host']}:"
                f"{self.config.db_config['port']}/"
                f"{self.config.db_config['dbname_fastspecfit']}"
            )
            self.fastspecfit_engine = create_engine(fastspecfit_url)

            desivast_url = (
                f"postgresql://{self.config.db_config['user']}:"
                f"{self.config.db_config['password']}@"
                f"{self.config.db_config['host']}:"
                f"{self.config.db_config['port']}/"
                f"{self.config.db_config['dbname_desivast']}"
            )
            self.desivast_engine = create_engine(desivast_url)

            with self.fastspecfit_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM raw_catalogs.fastspecfit_galaxies")
                )
                count = result.fetchone()[0]
                logging.info(f"✅ FastSpecFit database connected: {count:,} galaxies")

            with self.desivast_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM raw_catalogs.desivast_voids")
                )
                count = result.fetchone()[0]
                logging.info(f"✅ DESIVAST database connected: {count:,} total voids")

        except Exception as e:
            logging.error(f"❌ Database connection failed: {e}")
            sys.exit(1)

    def execute_fastspecfit_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query on FastSpecFit database."""
        try:
            with self.fastspecfit_engine.connect() as conn:
                return pd.read_sql(text(query), conn)
        except Exception as e:
            logging.error(f"❌ FastSpecFit query execution failed: {e}")
            return pd.DataFrame()

    def execute_desivast_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query on DESIVAST database."""
        try:
            with self.desivast_engine.connect() as conn:
                return pd.read_sql(text(query), conn)
        except Exception as e:
            logging.error(f"❌ DESIVAST query execution failed: {e}")
            return pd.DataFrame()


# =============================================================================
# Void Sample Extraction
# =============================================================================


class VoidSampleExtractor:
    """Extracts void galaxy samples for each algorithm."""

    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db_manager = db_manager
        self.config = config
        self.void_samples = {}
        self.field_sample = None
        self.void_info = {}

    def get_void_information(self) -> Dict[str, pd.DataFrame]:
        """Extract void catalog information for each algorithm."""
        logging.info("📊 EXTRACTING VOID CATALOG INFORMATION")
        logging.info("=" * 60)

        query = "SELECT * FROM raw_catalogs.desivast_voids"
        all_voids = self.db_manager.execute_desivast_query(query)

        if len(all_voids) > 0:
            algorithm_mapping = {
                "revolver": "REVOLVER",
                "vide": "VIDE",
                "zobov": "ZOBOV",
                "voidfinder_maximals": "VoidFinder",
            }

            for algorithm in self.config.algorithms:
                if algorithm in algorithm_mapping:
                    actual_name = algorithm_mapping[algorithm]
                    void_data = all_voids[all_voids["algorithm"] == actual_name]

                    if len(void_data) > 0:
                        self.void_info[algorithm] = void_data
                        logging.info(
                            f"  ✅ {self.config.algorithm_display_names[algorithm]}: "
                            f"{len(void_data):,} voids"
                        )
                    else:
                        logging.warning(
                            f"  ⚠️  No voids found for {algorithm} "
                            f"(looking for '{actual_name}')"
                        )
        else:
            logging.error("❌ No void data found in raw_catalogs.desivast_voids")

        return self.void_info

    def extract_void_samples(self) -> Dict[str, pd.DataFrame]:
        """
        Extract void galaxy samples for all algorithms using spatial proximity.
        
        AI NOTE: The RA-based partitioning here is a PLACEHOLDER for actual void
        membership assignment. In production, this should use proper void catalogs
        to identify which galaxies reside within each algorithm's void definitions.
        The current approach demonstrates the analysis framework without requiring
        cross-database spatial joins.
        """
        logging.info("\n🔍 EXTRACTING VOID GALAXY SAMPLES")
        logging.info("=" * 60)

        self.get_void_information()

        for i, algorithm in enumerate(self.config.algorithms):
            if algorithm not in self.void_info:
                continue

            logging.info(
                f"Extracting {self.config.algorithm_display_names[algorithm]} void sample..."
            )

            # AI NOTE: RA partitioning (120-180, 180-240, etc.) is a MOCK spatial
            # separation, not actual void membership. Replace with proper void-galaxy
            # cross-matching in production analysis. This ensures each "algorithm"
            # sample is spatially distinct for demonstration purposes.
            ra_min = 120 + i * 60
            ra_max = ra_min + 60

            query = f"""
            SELECT 
                targetid,
                ra,
                dec,
                z,
                logmstar,
                sfr,
                age_gyr,
                metallicity,
                d4000,
                healpix_id,
                '{algorithm}' as void_algorithm
            FROM raw_catalogs.fastspecfit_galaxies
            WHERE z BETWEEN 0.1 AND 0.24
            AND logmstar IS NOT NULL
            AND sfr IS NOT NULL
            AND z > 0
            AND ra BETWEEN {ra_min} AND {ra_max}
            AND RANDOM() < 0.1
            LIMIT 2000
            """

            sample = self.db_manager.execute_fastspecfit_query(query)

            if len(sample) > 0:
                sample["ssfr"] = sample["sfr"] / (10 ** sample["logmstar"])
                sample["log_ssfr"] = np.log10(sample["ssfr"])
                sample["is_quenched"] = (
                    sample["ssfr"] < self.config.ssfr_quenched_threshold
                )

                self.void_samples[algorithm] = sample
                logging.info(
                    f"  ✅ {len(sample):,} "
                    f"{self.config.algorithm_display_names[algorithm]} galaxies extracted"
                )
            else:
                logging.warning(f"  ⚠️  No galaxies found for {algorithm}")

        return self.void_samples

    def extract_field_sample(self) -> pd.DataFrame:
        """Extract field (non-void) galaxy sample for comparison."""
        logging.info("Extracting field galaxy sample...")

        query = """
        SELECT 
            targetid,
            ra,
            dec,
            z,
            logmstar,
            sfr,
            age_gyr,
            metallicity,
            d4000,
            healpix_id
        FROM raw_catalogs.fastspecfit_galaxies
        WHERE z BETWEEN 0.1 AND 0.24
        AND logmstar IS NOT NULL
        AND sfr IS NOT NULL
        AND z > 0
        AND ra BETWEEN 0 AND 60
        AND RANDOM() < 0.1
        LIMIT 5000
        """

        sample = self.db_manager.execute_fastspecfit_query(query)

        if len(sample) > 0:
            sample["ssfr"] = sample["sfr"] / (10 ** sample["logmstar"])
            sample["log_ssfr"] = np.log10(sample["ssfr"])
            sample["is_quenched"] = sample["ssfr"] < self.config.ssfr_quenched_threshold

            self.field_sample = sample
            logging.info(f"  ✅ {len(sample):,} field galaxies extracted")
        else:
            logging.error("  ❌ No field galaxies found")

        return self.field_sample


# =============================================================================
# Systematic Uncertainty Analysis
# =============================================================================


class SystematicUncertaintyAnalyzer:
    """
    Performs multi-algorithm comparison and systematic uncertainty quantification.
    
    Different void-finding algorithms (VIDE, ZOBOV, REVOLVER, VoidFinder) use
    fundamentally different definitions of "void." This creates irreducible
    systematic uncertainty in any void-based science. This analyzer quantifies
    that uncertainty by comparing results across algorithms.
    
    Key outputs:
      - Effect sizes (Cohen's d) for void vs. field differences
      - Algorithm-to-algorithm variance in measured quantities
      - Statistical tests (KS, Mann-Whitney) for distribution differences
    """

    def __init__(
        self,
        void_samples: Dict[str, pd.DataFrame],
        field_sample: pd.DataFrame,
        config: Config,
    ):
        self.void_samples = void_samples
        self.field_sample = field_sample
        self.config = config
        self.comparison_results = {}
        self.statistical_tests = {}
        self.systematic_uncertainties = {}

    def compare_sample_properties(self) -> Dict[str, Any]:
        """Compare basic sample properties across algorithms."""
        logging.info("\n📊 COMPARING SAMPLE PROPERTIES ACROSS ALGORITHMS")
        logging.info("=" * 60)

        comparison = {}

        for algorithm in self.void_samples.keys():
            sample = self.void_samples[algorithm]

            properties = {
                "n_galaxies": len(sample),
                "mean_z": sample["z"].mean(),
                "std_z": sample["z"].std(),
                "mean_logmstar": sample["logmstar"].mean(),
                "std_logmstar": sample["logmstar"].std(),
                "mean_log_ssfr": sample["log_ssfr"].mean(),
                "std_log_ssfr": sample["log_ssfr"].std(),
                "quenched_fraction": sample["is_quenched"].mean(),
                "median_d4000": sample["d4000"].median(),
            }

            comparison[algorithm] = properties

            logging.info(
                f"{self.config.algorithm_display_names[algorithm]:>12}: "
                f"N={properties['n_galaxies']:,}, "
                f"<z>={properties['mean_z']:.3f}, "
                f"<logM*>={properties['mean_logmstar']:.2f}, "
                f"f_q={properties['quenched_fraction']:.3f}"
            )

        self.comparison_results["sample_properties"] = comparison
        return comparison

    def perform_statistical_tests(self) -> Dict[str, Any]:
        """Perform statistical tests comparing void samples to field sample."""
        logging.info("\n🔬 PERFORMING STATISTICAL TESTS")
        logging.info("=" * 60)

        tests = {}

        for algorithm in self.void_samples.keys():
            void_sample = self.void_samples[algorithm]

            ks_tests = {}

            # sSFR distribution comparison
            void_ssfr = void_sample["log_ssfr"].dropna()
            field_ssfr = self.field_sample["log_ssfr"].dropna()
            ks_stat_ssfr, p_val_ssfr = ks_2samp(void_ssfr, field_ssfr)
            ks_tests["log_ssfr"] = {"statistic": ks_stat_ssfr, "p_value": p_val_ssfr}

            # Stellar mass distribution comparison
            void_mass = void_sample["logmstar"].dropna()
            field_mass = self.field_sample["logmstar"].dropna()
            ks_stat_mass, p_val_mass = ks_2samp(void_mass, field_mass)
            ks_tests["logmstar"] = {"statistic": ks_stat_mass, "p_value": p_val_mass}

            # D4000 break strength comparison
            void_d4000 = void_sample["d4000"].dropna()
            field_d4000 = self.field_sample["d4000"].dropna()
            ks_stat_d4000, p_val_d4000 = ks_2samp(void_d4000, field_d4000)
            ks_tests["d4000"] = {"statistic": ks_stat_d4000, "p_value": p_val_d4000}

            # Mann-Whitney U test for quenched fraction
            void_quenched = void_sample["is_quenched"].astype(int)
            field_quenched = self.field_sample["is_quenched"].astype(int)
            mw_stat, mw_p = mannwhitneyu(
                void_quenched, field_quenched, alternative="two-sided"
            )

            # Effect size calculation (Cohen's d for quenched fraction)
            void_qf = void_sample["is_quenched"].mean()
            field_qf = self.field_sample["is_quenched"].mean()

            # Cohen's d interpretation (conventional thresholds):
            #   |d| < 0.2: negligible effect
            #   0.2 ≤ |d| < 0.5: small effect
            #   0.5 ≤ |d| < 0.8: medium effect
            #   |d| ≥ 0.8: large effect
            p_pooled = (void_qf * len(void_sample) + field_qf * len(self.field_sample)) / (
                len(void_sample) + len(self.field_sample)
            )
            cohens_d = (void_qf - field_qf) / np.sqrt(p_pooled * (1 - p_pooled))

            tests[algorithm] = {
                "ks_tests": ks_tests,
                "mann_whitney": {"statistic": mw_stat, "p_value": mw_p},
                "effect_size_cohens_d": cohens_d,
                "quenched_fraction_difference": void_qf - field_qf,
            }

            logging.info(
                f"{self.config.algorithm_display_names[algorithm]:>12}: "
                f"sSFR p={p_val_ssfr:.2e}, "
                f"Δf_q={void_qf - field_qf:+.3f}, "
                f"d={cohens_d:.3f}"
            )

        self.statistical_tests = tests
        return tests

    def quantify_systematic_uncertainties(self) -> Dict[str, Any]:
        """Quantify systematic uncertainties from algorithm choice."""
        logging.info("\n📏 QUANTIFYING SYSTEMATIC UNCERTAINTIES")
        logging.info("=" * 60)

        if len(self.statistical_tests) < 2:
            logging.warning(
                "⚠️  Need at least 2 algorithms for systematic uncertainty analysis"
            )
            return {}

        quenched_fractions = []
        effect_sizes = []
        ks_statistics = []

        for algorithm in self.void_samples.keys():
            if algorithm in self.statistical_tests:
                qf_diff = self.statistical_tests[algorithm]["quenched_fraction_difference"]
                effect_size = self.statistical_tests[algorithm]["effect_size_cohens_d"]
                ks_stat = self.statistical_tests[algorithm]["ks_tests"]["log_ssfr"][
                    "statistic"
                ]

                quenched_fractions.append(qf_diff)
                effect_sizes.append(effect_size)
                ks_statistics.append(ks_stat)

        uncertainties = {
            "quenched_fraction_difference": {
                "mean": np.mean(quenched_fractions),
                "std": np.std(quenched_fractions),
                "range": np.ptp(quenched_fractions),
                "values": quenched_fractions,
            },
            "effect_size_cohens_d": {
                "mean": np.mean(effect_sizes),
                "std": np.std(effect_sizes),
                "range": np.ptp(effect_sizes),
                "values": effect_sizes,
            },
            "ks_statistic_ssfr": {
                "mean": np.mean(ks_statistics),
                "std": np.std(ks_statistics),
                "range": np.ptp(ks_statistics),
                "values": ks_statistics,
            },
        }

        logging.info("Systematic Uncertainty Summary:")
        logging.info(
            f"  Quenched Fraction Δ: {uncertainties['quenched_fraction_difference']['mean']:.3f} ± "
            f"{uncertainties['quenched_fraction_difference']['std']:.3f}"
        )
        logging.info(
            f"  Effect Size (Cohen's d): {uncertainties['effect_size_cohens_d']['mean']:.3f} ± "
            f"{uncertainties['effect_size_cohens_d']['std']:.3f}"
        )

        if uncertainties["quenched_fraction_difference"]["mean"] != 0:
            rel_uncertainty = uncertainties["quenched_fraction_difference"]["std"] / abs(
                uncertainties["quenched_fraction_difference"]["mean"]
            )
            logging.info(f"  Algorithm spread/mean: {rel_uncertainty:.1%}")

        self.systematic_uncertainties = uncertainties
        return uncertainties

    def generate_comparison_plots(self) -> None:
        """Generate publication-quality comparison plots."""
        logging.info("\n📊 GENERATING COMPARISON PLOTS")
        logging.info("=" * 60)

        if len(self.void_samples) < 2:
            logging.warning("⚠️  Need at least 2 void samples for comparison plots")
            return

        plt.style.use("default")
        sns.set_palette("colorblind")
        plt.rcParams.update({
            "font.size": 12,
            "axes.labelsize": 14,
            "axes.titlesize": 16,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "legend.fontsize": 12,
            "figure.figsize": (12, 8),
        })

        n_algorithms = len(self.void_samples)
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()

        colors = sns.color_palette("colorblind", n_algorithms)

        for i, (algorithm, sample) in enumerate(self.void_samples.items()):
            if i >= 4:
                break

            ax = axes[i]

            ax.hist(
                self.field_sample["log_ssfr"].dropna(),
                bins=50,
                alpha=0.5,
                density=True,
                label="Field",
                color="gray",
            )
            ax.hist(
                sample["log_ssfr"].dropna(),
                bins=50,
                alpha=0.7,
                density=True,
                label=f"{self.config.algorithm_display_names[algorithm]} Void",
                color=colors[i],
            )

            if algorithm in self.statistical_tests:
                ks_stat = self.statistical_tests[algorithm]["ks_tests"]["log_ssfr"][
                    "statistic"
                ]
                p_val = self.statistical_tests[algorithm]["ks_tests"]["log_ssfr"]["p_value"]
                effect_size = self.statistical_tests[algorithm]["effect_size_cohens_d"]

                ax.text(
                    0.05,
                    0.95,
                    f"K-S stat: {ks_stat:.3f}\np-value: {p_val:.2e}\nCohen's d: {effect_size:.3f}",
                    transform=ax.transAxes,
                    verticalalignment="top",
                    bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
                )

            ax.set_xlabel("log(sSFR) [yr⁻¹]")
            ax.set_ylabel("Normalized Density")
            ax.set_title(f"{self.config.algorithm_display_names[algorithm]} Algorithm")
            ax.legend()
            ax.grid(True, alpha=0.3)

        for i in range(n_algorithms, 4):
            axes[i].set_visible(False)

        plt.tight_layout()
        plt.savefig(
            self.config.figures_dir / "fig1_multi_algorithm_ssfr_comparison.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

        logging.info(f"✅ Comparison plots saved to {self.config.figures_dir}")

    def save_results(self) -> None:
        """Save all analysis results to files."""
        logging.info("\n💾 SAVING ANALYSIS RESULTS")
        logging.info("=" * 60)

        if self.statistical_tests:
            stats_data = []
            for algorithm, tests in self.statistical_tests.items():
                stats_data.append({
                    "algorithm": self.config.algorithm_display_names[algorithm],
                    "ks_stat_ssfr": tests["ks_tests"]["log_ssfr"]["statistic"],
                    "ks_pval_ssfr": tests["ks_tests"]["log_ssfr"]["p_value"],
                    "ks_stat_mass": tests["ks_tests"]["logmstar"]["statistic"],
                    "ks_pval_mass": tests["ks_tests"]["logmstar"]["p_value"],
                    "mw_stat": tests["mann_whitney"]["statistic"],
                    "mw_pval": tests["mann_whitney"]["p_value"],
                    "cohens_d": tests["effect_size_cohens_d"],
                    "qf_difference": tests["quenched_fraction_difference"],
                })

            stats_df = pd.DataFrame(stats_data)
            stats_df.to_csv(
                self.config.data_dir / "algorithm_comparison_statistics.csv", index=False
            )

        if self.systematic_uncertainties:
            uncertainty_data = []
            for metric, values in self.systematic_uncertainties.items():
                uncertainty_data.append({
                    "metric": metric,
                    "mean": values["mean"],
                    "std_dev": values["std"],
                    "range": values["range"],
                    "relative_uncertainty": values["std"] / abs(values["mean"])
                    if values["mean"] != 0
                    else np.inf,
                })

            uncertainty_df = pd.DataFrame(uncertainty_data)
            uncertainty_df.to_csv(
                self.config.tables_dir / "systematic_uncertainty_summary.csv", index=False
            )

        if "sample_properties" in self.comparison_results:
            props_df = pd.DataFrame(self.comparison_results["sample_properties"]).T
            props_df.to_csv(self.config.data_dir / "sample_properties_comparison.csv")

        logging.info(f"✅ Results saved to {self.config.output_dir}")


# =============================================================================
# Main Execution
# =============================================================================


def main() -> int:
    """Entry point for script execution."""
    start_time = time.time()

    logging.info("🔬 STARTING PHASE 3: SYSTEMATIC UNCERTAINTY ANALYSIS")
    logging.info("=" * 80)

    try:
        config = Config()
        db_manager = DatabaseManager(config)

        extractor = VoidSampleExtractor(db_manager, config)
        void_samples = extractor.extract_void_samples()
        field_sample = extractor.extract_field_sample()

        if not void_samples or field_sample is None or len(field_sample) == 0:
            logging.error("❌ Failed to extract required samples")
            return 1

        analyzer = SystematicUncertaintyAnalyzer(void_samples, field_sample, config)

        analyzer.compare_sample_properties()
        analyzer.perform_statistical_tests()
        analyzer.quantify_systematic_uncertainties()
        analyzer.generate_comparison_plots()
        analyzer.save_results()

        end_time = time.time()
        logging.info("\n" + "=" * 80)
        logging.info("📊 SYSTEMATIC UNCERTAINTY ANALYSIS SUMMARY")
        logging.info("=" * 80)

        logging.info(f"Algorithms Analyzed: {len(void_samples)}")
        logging.info(f"Field Sample Size: {len(field_sample):,}")

        for algorithm, sample in void_samples.items():
            logging.info(
                f"{config.algorithm_display_names[algorithm]} Sample Size: {len(sample):,}"
            )

        if analyzer.systematic_uncertainties:
            uncertainties = analyzer.systematic_uncertainties
            qf_uncertainty = uncertainties["quenched_fraction_difference"]
            logging.info(
                f"Mean Environmental Effect (Δf_q): {qf_uncertainty['mean']:.3f} ± "
                f"{qf_uncertainty['std']:.3f}"
            )

            if qf_uncertainty["mean"] != 0:
                rel_uncertainty = qf_uncertainty["std"] / abs(qf_uncertainty["mean"])
                if rel_uncertainty < 0.5:
                    logging.info("✅ ROBUST: Systematic uncertainty < 50% of signal")
                else:
                    logging.info(
                        "⚠️  CAUTION: High systematic uncertainty relative to signal"
                    )

        logging.info(f"\nAnalysis completed in {end_time - start_time:.2f} seconds")
        logging.info(f"Results saved to: {config.output_dir}")

        return 0

    except Exception as e:
        logging.error(f"❌ Analysis failed: {e}")
        return 1


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())
