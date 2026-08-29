PRINOVA FINAL PROJECT

BACKEND
Open PowerShell:
cd C:\PRINOVA\web\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000

Check:
curl.exe http://127.0.0.1:8000/health

FRONTEND
Open a SECOND PowerShell:
cd C:\PRINOVA\web\frontend
npm install
npm run dev

Then open the Vite URL, normally http://localhost:5173

Important: npm run dev must be run inside the frontend folder, not C:\PRINOVA\web.

The project includes:
- /analyze upload workflow
- stored latent representation
- /latent/{id}/preview for live 2-D visualization
- PCA page
- Latent Space page
- /molecular/clustering page
- /molecular/robustness page
- /molecular/biological-validation page
