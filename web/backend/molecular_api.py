
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException


# ============================================================
# PRINOVA MOLECULAR ANALYSIS API
# Phase 3
# ============================================================

router = APIRouter(
    prefix="/molecular",
    tags=["Molecular Analysis"]
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESULTS_DIR = (
    PROJECT_ROOT
    / "results"
    / "molecular"
)

CLUSTERING_COMPARISON_FILE = (
    RESULTS_DIR
    / "clustering_comparison_results.csv"
)

CLUSTER_EVALUATION_FILE = (
    RESULTS_DIR
    / "molecular_cluster_evaluation.csv"
)

ROBUSTNESS_FILE = (
    RESULTS_DIR
    / "molecular_robustness_results.csv"
)

BIOLOGICAL_VALIDATION_DIR = (
    RESULTS_DIR
    / "biological_validation"
)

BIOLOGICAL_CLUSTER_SUMMARY_FILE = (
    BIOLOGICAL_VALIDATION_DIR
    / "biological_cluster_summary.csv"
)

PROTEIN_ANNOTATIONS_FILE = (
    BIOLOGICAL_VALIDATION_DIR
    / "protein_annotations.csv"
)


# ============================================================
# HELPER
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:

    if not path.exists():

        raise HTTPException(
            status_code=500,
            detail={
                "code": "RESULT_FILE_NOT_FOUND",
                "message": (
                    f"Required molecular result file "
                    f"was not found: {path}"
                )
            }
        )

    try:

        return pd.read_csv(path)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "RESULT_FILE_READ_FAILED",
                "message": (
                    f"Unable to read molecular result file: "
                    f"{str(e)}"
                )
            }
        )


# ============================================================
# CLUSTERING
# ============================================================

@router.get("/clustering")
def molecular_clustering():

    comparison = load_csv(
        CLUSTERING_COMPARISON_FILE
    )

    evaluation = load_csv(
        CLUSTER_EVALUATION_FILE
    )


    required_comparison_columns = [
        "dimension",
        "clusters",
        "method",
        "silhouette"
    ]


    required_evaluation_columns = [
        "k",
        "silhouette_score"
    ]


    for column in required_comparison_columns:

        if column not in comparison.columns:

            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INVALID_CLUSTERING_RESULTS",
                    "message": (
                        f"Missing clustering column: "
                        f"{column}"
                    )
                }
            )


    for column in required_evaluation_columns:

        if column not in evaluation.columns:

            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INVALID_CLUSTER_EVALUATION",
                    "message": (
                        f"Missing cluster evaluation column: "
                        f"{column}"
                    )
                }
            )


    # --------------------------------------------------------
    # Best configuration across all tested methods/dimensions
    # --------------------------------------------------------

    best_row = comparison.loc[
        comparison["silhouette"].idxmax()
    ]


    # --------------------------------------------------------
    # Best k from the dedicated cluster evaluation
    # --------------------------------------------------------

    best_k_row = evaluation.loc[
        evaluation["silhouette_score"].idxmax()
    ]


    # --------------------------------------------------------
    # Return all tested configurations
    # --------------------------------------------------------

    configurations = []

    for _, row in comparison.iterrows():

        configurations.append(
            {
                "dimension": int(row["dimension"]),
                "clusters": int(row["clusters"]),
                "method": str(row["method"]),
                "silhouette": float(row["silhouette"])
            }
        )


    k_evaluation = []

    for _, row in evaluation.iterrows():

        k_evaluation.append(
            {
                "k": int(row["k"]),
                "silhouette_score": float(
                    row["silhouette_score"]
                )
            }
        )


    return {

        "status": "success",

        "analysis": "molecular_clustering",

        "best_configuration": {
            "dimension": int(
                best_row["dimension"]
            ),
            "clusters": int(
                best_row["clusters"]
            ),
            "method": str(
                best_row["method"]
            ),
            "silhouette": float(
                best_row["silhouette"]
            )
        },

        "best_k_evaluation": {
            "k": int(
                best_k_row["k"]
            ),
            "silhouette_score": float(
                best_k_row["silhouette_score"]
            )
        },

        "configurations": configurations,

        "k_evaluation": k_evaluation,

        "configuration_count": int(
            len(configurations)
        )
    }


# ============================================================
# ROBUSTNESS
# ============================================================

@router.get("/robustness")
def molecular_robustness():

    df = load_csv(
        ROBUSTNESS_FILE
    )


    required_columns = [
        "seed",
        "dimension",
        "mse",
        "variance_explained",
        "compression_score",
        "prinova_score"
    ]


    for column in required_columns:

        if column not in df.columns:

            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INVALID_ROBUSTNESS_RESULTS",
                    "message": (
                        f"Missing robustness column: "
                        f"{column}"
                    )
                }
            )


    results = []

    for _, row in df.iterrows():

        results.append(
            {
                "seed": int(row["seed"]),
                "dimension": int(
                    row["dimension"]
                ),
                "mse": float(
                    row["mse"]
                ),
                "variance_explained": float(
                    row["variance_explained"]
                ),
                "compression_score": float(
                    row["compression_score"]
                ),
                "prinova_score": float(
                    row["prinova_score"]
                )
            }
        )


    # --------------------------------------------------------
    # Calculate stability range for each dimension
    # --------------------------------------------------------

    stability = []


    for dimension, group in df.groupby(
        "dimension"
    ):

        stability.append(
            {
                "dimension": int(
                    dimension
                ),

                "seeds": int(
                    group["seed"].nunique()
                ),

                "mse_min": float(
                    group["mse"].min()
                ),

                "mse_max": float(
                    group["mse"].max()
                ),

                "mse_range": float(
                    group["mse"].max()
                    - group["mse"].min()
                ),

                "variance_explained_min": float(
                    group[
                        "variance_explained"
                    ].min()
                ),

                "variance_explained_max": float(
                    group[
                        "variance_explained"
                    ].max()
                ),

                "prinova_score_min": float(
                    group[
                        "prinova_score"
                    ].min()
                ),

                "prinova_score_max": float(
                    group[
                        "prinova_score"
                    ].max()
                )
            }
        )


    return {

        "status": "success",

        "analysis": "molecular_robustness",

        "seed_count": int(
            df["seed"].nunique()
        ),

        "dimension_count": int(
            df["dimension"].nunique()
        ),

        "result_count": int(
            len(df)
        ),

        "results": results,

        "stability": stability
    }


# ============================================================
# BIOLOGICAL VALIDATION
# ============================================================

@router.get("/biological-validation")
def molecular_biological_validation():

    summary = load_csv(
        BIOLOGICAL_CLUSTER_SUMMARY_FILE
    )


    annotations = load_csv(
        PROTEIN_ANNOTATIONS_FILE
    )


    # --------------------------------------------------------
    # Validate summary columns
    # --------------------------------------------------------

    required_summary_columns = [
        "cluster",
        "proteins",
        "organisms",
        "annotated_functions",
        "proteins_with_go"
    ]


    for column in required_summary_columns:

        if column not in summary.columns:

            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INVALID_BIOLOGICAL_SUMMARY",
                    "message": (
                        f"Missing biological summary column: "
                        f"{column}"
                    )
                }
            )


    # --------------------------------------------------------
    # Validate annotation columns
    # --------------------------------------------------------

    required_annotation_columns = [
        "protein_id",
        "cluster",
        "protein_name",
        "organism",
        "function",
        "go_terms"
    ]


    for column in required_annotation_columns:

        if column not in annotations.columns:

            raise HTTPException(
                status_code=500,
                detail={
                    "code": "INVALID_PROTEIN_ANNOTATIONS",
                    "message": (
                        f"Missing annotation column: "
                        f"{column}"
                    )
                }
            )


    # --------------------------------------------------------
    # Cluster summary
    # --------------------------------------------------------

    cluster_summary = []

    for _, row in summary.iterrows():

        cluster_summary.append(
            {
                "cluster": int(
                    row["cluster"]
                ),

                "proteins": int(
                    row["proteins"]
                ),

                "organisms": int(
                    row["organisms"]
                ),

                "annotated_functions": int(
                    row["annotated_functions"]
                ),

                "proteins_with_go": int(
                    row["proteins_with_go"]
                )
            }
        )


    # --------------------------------------------------------
    # Protein annotations
    # --------------------------------------------------------

    protein_annotations = []

    for _, row in annotations.iterrows():

        protein_annotations.append(
            {
                "protein_id": str(
                    row["protein_id"]
                ),

                "cluster": int(
                    row["cluster"]
                ),

                "protein_name": str(
                    row["protein_name"]
                ),

                "organism": str(
                    row["organism"]
                ),

                "function": str(
                    row["function"]
                ),

                "go_terms": str(
                    row["go_terms"]
                )
            }
        )


    return {

        "status": "success",

        "analysis": "molecular_biological_validation",

        "cluster_count": int(
            len(cluster_summary)
        ),

        "annotated_protein_count": int(
            len(protein_annotations)
        ),

        "cluster_summary": cluster_summary,

        "protein_annotations": protein_annotations
    }