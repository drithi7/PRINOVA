\# PRINOVA



\### Protein Representation and Latent Structure Analysis Platform



PRINOVA is a data science and molecular representation analysis platform designed to explore high-dimensional protein embedding data through dimensionality reduction, latent space analysis, clustering, robustness evaluation, and biological validation.



The platform provides an interactive web interface where users can upload embedding matrices and analyze their underlying latent structure.



\---



\## Features



\- Upload CSV or NPY embedding matrices

\- PCA-based dimensionality reduction

\- Latent space representation analysis

\- Reconstruction error evaluation

\- Variance explained analysis

\- R² reconstruction scoring

\- Dimensional compression measurement

\- Composite PRINOVA scoring

\- Latent space visualization

\- Clustering analysis

\- Robustness analysis across multiple random seeds

\- Biological validation and protein annotation analysis

\- Interactive React frontend

\- FastAPI backend



\---



\## Project Architecture



```text

PRINOVA/

│

├── web/

│   ├── backend/

│   │   ├── main.py

│   │   ├── molecular\_api.py

│   │   ├── prinova\_engine.py

│   │   └── requirements.txt

│   │

│   └── frontend/

│       ├── src/

│       │   ├── App.jsx

│       │   ├── App.css

│       │   ├── index.css

│       │   └── main.jsx

│       │

│       └── package.json

│

├── results/

│   └── molecular/

│

└── README.md

