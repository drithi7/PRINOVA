from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import io
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from prinova_engine import run_prinova
from molecular_api import router as molecular_router


app = FastAPI(
    title="PRINOVA API",
    description="Protein Representation and Latent Structure Analysis",
    version="3.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    molecular_router
)


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parents[1]

LATENT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "api_latent"
)

LATENT_OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


@app.get("/")
def root():

    return {
        "name": "PRINOVA",
        "version": "3.0.0",
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "PRINOVA backend",
        "version": "3.0.0"
    }


def load_csv(
    contents: bytes
) -> np.ndarray:

    try:

        df = pd.read_csv(
            io.BytesIO(contents)
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_CSV",
                "message": (
                    f"Unable to read CSV file: {str(e)}"
                )
            }
        )

    numeric_df = df.select_dtypes(
        include=[np.number]
    )

    if numeric_df.empty:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "NO_NUMERIC_COLUMNS",
                "message": (
                    "CSV does not contain numeric "
                    "embedding columns."
                )
            }
        )

    return numeric_df.to_numpy(
        dtype=np.float32
    )


def load_npy(
    contents: bytes
) -> np.ndarray:

    try:

        array = np.load(
            io.BytesIO(contents),
            allow_pickle=False
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_NPY",
                "message": (
                    f"Unable to read NPY file: {str(e)}"
                )
            }
        )

    try:

        return np.asarray(
            array,
            dtype=np.float32
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_ARRAY",
                "message": (
                    f"Unable to convert uploaded array "
                    f"to float32: {str(e)}"
                )
            }
        )


def validate_embeddings(
    X: np.ndarray
):

    if X.ndim != 2:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SHAPE",
                "message": (
                    "The embedding matrix must be "
                    "2-dimensional."
                )
            }
        )

    samples = X.shape[0]
    dimensions = X.shape[1]

    if samples == 0:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "EMPTY_DATASET",
                "message": (
                    "The uploaded file contains "
                    "no samples."
                )
            }
        )

    if dimensions != 1024:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_DIMENSIONS",
                "message": (
                    "Expected 1024 embedding dimensions, "
                    f"but received {dimensions}."
                )
            }
        )

    if not np.isfinite(X).all():

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_VALUES",
                "message": (
                    "The embedding matrix contains "
                    "NaN or infinite values."
                )
            }
        )

    if samples < 256:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INSUFFICIENT_SAMPLES",
                "message": (
                    "At least 256 samples are required "
                    "for the current PCA-256 analysis, "
                    f"but received {samples}."
                )
            }
        )

    return {
        "samples": int(samples),
        "dimensions": int(dimensions)
    }


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_FILENAME",
                "message": "No filename was provided."
            }
        )

    original_filename = file.filename

    filename = original_filename.lower()

    supported_extensions = (
        ".csv",
        ".npy"
    )

    if not filename.endswith(
        supported_extensions
    ):

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": (
                    "Unsupported file type. "
                    "Please upload a CSV or NPY file."
                ),
                "supported_types": [
                    ".csv",
                    ".npy"
                ]
            }
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "EMPTY_FILE",
                "message": (
                    "The uploaded file is empty."
                )
            }
        )

    if filename.endswith(".csv"):

        X = load_csv(
            contents
        )

    else:

        X = load_npy(
            contents
        )

    input_info = validate_embeddings(
        X
    )

    try:

        analysis_results = run_prinova(
            X
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail={
                "code": "PRINOVA_VALIDATION_ERROR",
                "message": str(e)
            }
        )

    except FileNotFoundError as e:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "REFERENCE_RESULTS_NOT_FOUND",
                "message": str(e)
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "PRINOVA_ANALYSIS_FAILED",
                "message": (
                    f"PRINOVA analysis failed: {str(e)}"
                )
            }
        )

    latent = analysis_results.pop(
        "_latent",
        None
    )

    if latent is None:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "LATENT_REPRESENTATION_MISSING",
                "message": (
                    "PRINOVA analysis completed, but "
                    "no latent representation was returned."
                )
            }
        )

    latent = np.asarray(
        latent,
        dtype=np.float32
    )

    if latent.ndim != 2:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "INVALID_LATENT_SHAPE",
                "message": (
                    "The generated latent representation "
                    "is not a 2-dimensional matrix."
                )
            }
        )

    if not np.isfinite(
        latent
    ).all():

        raise HTTPException(
            status_code=500,
            detail={
                "code": "INVALID_LATENT_VALUES",
                "message": (
                    "The generated latent representation "
                    "contains NaN or infinite values."
                )
            }
        )

    latent_id = uuid.uuid4().hex

    latent_path = (
        LATENT_OUTPUT_DIR
        / f"{latent_id}.npz"
    )

    try:

        np.savez_compressed(
            latent_path,
            latent=latent
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail={
                "code": "LATENT_SAVE_FAILED",
                "message": (
                    f"Unable to save latent representation: "
                    f"{str(e)}"
                )
            }
        )

    return {

        "status": "success",

        "filename": original_filename,

        "input": input_info,

        "analysis": analysis_results,

        "latent": {

            "id": latent_id,

            "shape": [
                int(latent.shape[0]),
                int(latent.shape[1])
            ],

            "dimensions": int(
                latent.shape[1]
            ),

            "samples": int(
                latent.shape[0]
            ),

            "dtype": str(
                latent.dtype
            ),

            "format": "NPZ",

            "download_endpoint": (
                f"/latent/{latent_id}"
            )
        }
    }



@app.get("/latent/{latent_id}/preview")
def get_latent_preview(latent_id: str, limit: int = 1500):
    """Return a lightweight 2-D preview derived from the stored latent matrix."""
    if not latent_id or not latent_id.isalnum():
        raise HTTPException(status_code=400, detail={"code": "INVALID_LATENT_ID", "message": "Invalid latent representation ID."})

    latent_path = LATENT_OUTPUT_DIR / f"{latent_id}.npz"
    if not latent_path.exists():
        raise HTTPException(status_code=404, detail={"code": "LATENT_NOT_FOUND", "message": "The requested latent representation was not found."})

    try:
        with np.load(latent_path) as data:
            latent = np.asarray(data["latent"], dtype=np.float64)

        if latent.ndim != 2 or latent.shape[1] < 2:
            raise ValueError("Latent representation must contain at least two dimensions.")

        # The first two PCA latent coordinates are used for visualization only.
        coords = latent[:, :2]
        if limit > 0 and coords.shape[0] > limit:
            indices = np.linspace(0, coords.shape[0] - 1, limit, dtype=int)
            coords = coords[indices]

        return {
            "status": "success",
            "latent_id": latent_id,
            "points": [{"x": float(row[0]), "y": float(row[1])} for row in coords],
            "axis_labels": ["Latent Dimension 1", "Latent Dimension 2"],
            "sample_count": int(latent.shape[0]),
            "displayed_samples": int(coords.shape[0])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "LATENT_PREVIEW_FAILED", "message": str(e)})


@app.get(
    "/latent/{latent_id}"
)
def get_latent(
    latent_id: str
):

    if (
        not latent_id
        or not latent_id.isalnum()
        or "/" in latent_id
        or "\\" in latent_id
        or ".." in latent_id
    ):

        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_LATENT_ID",
                "message": (
                    "Invalid latent representation ID."
                )
            }
        )

    latent_path = (
        LATENT_OUTPUT_DIR
        / f"{latent_id}.npz"
    )

    if not latent_path.exists():

        raise HTTPException(
            status_code=404,
            detail={
                "code": "LATENT_NOT_FOUND",
                "message": (
                    "The requested latent representation "
                    "was not found."
                )
            }
        )

    return FileResponse(
        path=str(latent_path),
        media_type="application/octet-stream",
        filename=f"{latent_id}.npz"
    )