import os

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import r2_score


# ============================================================
# PRINOVA ENGINE
# Phase 2 — Reference-Based Molecular PRINOVA Analysis
# ============================================================

INPUT_DIMENSION = 1024
LATENT_DIMENSION = 256

RECONSTRUCTION_WEIGHT = 0.70
COMPRESSION_WEIGHT = 0.30


# ============================================================
# REFERENCE RESULTS
# ============================================================

REFERENCE_RESULTS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "results",
        "molecular",
        "molecular_prinova_scores.csv"
    )
)


# ============================================================
# LOAD REFERENCE SCORING RANGE
# ============================================================

def load_reference_scores():

    if not os.path.exists(
        REFERENCE_RESULTS_PATH
    ):
        raise FileNotFoundError(
            "Reference PRINOVA results were not found at: "
            f"{REFERENCE_RESULTS_PATH}"
        )

    try:
        df = pd.read_csv(
            REFERENCE_RESULTS_PATH
        )

    except Exception as e:
        raise RuntimeError(
            "Unable to load reference PRINOVA results: "
            f"{str(e)}"
        )

    required_columns = {
        "model",
        "dimension",
        "r2"
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise RuntimeError(
            "Reference PRINOVA CSV is missing required "
            f"columns: {sorted(missing)}"
        )

    if df.empty:
        raise RuntimeError(
            "Reference PRINOVA results are empty."
        )

    r2_values = pd.to_numeric(
        df["r2"],
        errors="coerce"
    ).dropna()

    if r2_values.empty:
        raise RuntimeError(
            "No valid R² values were found in the "
            "reference PRINOVA results."
        )

    r2_min = float(
        r2_values.min()
    )

    r2_max = float(
        r2_values.max()
    )

    if r2_max <= r2_min:
        raise RuntimeError(
            "Invalid reference R² range: "
            f"min={r2_min}, max={r2_max}"
        )

    return {
        "r2_min": r2_min,
        "r2_max": r2_max,
        "configurations": int(
            len(df)
        )
    }


# ============================================================
# RUN PRINOVA
# ============================================================

def run_prinova(
    X: np.ndarray
) -> dict:

    if not isinstance(
        X,
        np.ndarray
    ):
        X = np.asarray(
            X,
            dtype=np.float32
        )

    X = np.asarray(
        X,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if X.ndim != 2:
        raise ValueError(
            "Embedding matrix must be 2-dimensional."
        )

    samples = X.shape[0]
    dimensions = X.shape[1]

    if dimensions != INPUT_DIMENSION:
        raise ValueError(
            f"Expected {INPUT_DIMENSION} embedding dimensions, "
            f"but received {dimensions}."
        )

    if samples < LATENT_DIMENSION:
        raise ValueError(
            f"At least {LATENT_DIMENSION} samples are required "
            f"for PCA-{LATENT_DIMENSION}, but received "
            f"{samples}."
        )

    if not np.isfinite(X).all():
        raise ValueError(
            "Embedding matrix contains NaN or infinite values."
        )

    # --------------------------------------------------------
    # Reference scores
    # --------------------------------------------------------

    reference = load_reference_scores()

    r2_min = reference["r2_min"]
    r2_max = reference["r2_max"]

    # --------------------------------------------------------
    # PCA
    # --------------------------------------------------------

    pca = PCA(
        n_components=LATENT_DIMENSION
    )

    latent = pca.fit_transform(
        X
    )

    # --------------------------------------------------------
    # Reconstruction
    # --------------------------------------------------------

    reconstructed = pca.inverse_transform(
        latent
    )

    # --------------------------------------------------------
    # MSE
    # --------------------------------------------------------

    mse = float(
        np.mean(
            (X - reconstructed) ** 2
        )
    )

    # --------------------------------------------------------
    # R²
    # --------------------------------------------------------

    r2 = float(
        r2_score(
            X,
            reconstructed,
            multioutput="variance_weighted"
        )
    )

    # --------------------------------------------------------
    # Explained variance
    # --------------------------------------------------------

    variance_explained = float(
        np.sum(
            pca.explained_variance_ratio_
        )
    )

    # --------------------------------------------------------
    # Compression
    # --------------------------------------------------------

    compression_score = float(
        1.0
        -
        (
            LATENT_DIMENSION
            /
            INPUT_DIMENSION
        )
    )

    # --------------------------------------------------------
    # Normalize reconstruction
    # --------------------------------------------------------

    normalized_reconstruction = float(
        (
            r2
            -
            r2_min
        )
        /
        (
            r2_max
            -
            r2_min
        )
    )

    normalized_reconstruction = float(
        np.clip(
            normalized_reconstruction,
            0.0,
            1.0
        )
    )

    # --------------------------------------------------------
    # PRINOVA score
    # --------------------------------------------------------

    prinova_score = float(
        RECONSTRUCTION_WEIGHT
        *
        normalized_reconstruction
        +
        COMPRESSION_WEIGHT
        *
        compression_score
    )

    # --------------------------------------------------------
    # Return
    #
    # _latent is removed by main.py before JSON serialization.
    # --------------------------------------------------------

    return {

        "_latent": latent,

        "representation": "PCA",

        "dimension": LATENT_DIMENSION,

        "mse": mse,

        "r2": r2,

        "variance_explained": variance_explained,

        "compression_score": compression_score,

        "normalized_reconstruction": (
            normalized_reconstruction
        ),

        "prinova_score": prinova_score,

        "latent_shape": [
            int(latent.shape[0]),
            int(latent.shape[1])
        ],

        "scoring": {

            "method":
                "reference_min_max_clipped",

            "reference_file": (
                "results/molecular/"
                "molecular_prinova_scores.csv"
            ),

            "reference_r2_min":
                r2_min,

            "reference_r2_max":
                r2_max,

            "reference_configurations":
                reference["configurations"],

            "reconstruction_weight":
                RECONSTRUCTION_WEIGHT,

            "compression_weight":
                COMPRESSION_WEIGHT,

            "normalized_score_range": [
                0.0,
                1.0
            ]
        }
    }