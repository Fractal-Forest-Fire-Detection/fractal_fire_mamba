# Fractal Fire Mamba - Setup Guide

## 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Fractal-Forest-Fire-Detection/fractal_fire_mamba.git
cd fractal_fire_mamba
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Download Mamba Model (Crucial Step!)

The large Mamba model weights (500MB+) are **not included in the git repository** to keep it lightweight. You must download them manually using the included script:

```bash
python scripts/download_mamba.py
```

This will fetch the `state-spaces/mamba-130m-hf` model from Hugging Face and save it to `models/mamba-130m/`.

## 3. Run the Server

Start the backend server:

```bash
uvicorn server:app --reload
```

The application will automatically detect the downloaded model and print:
`✅ HF Mamba-130m Active (Neural Adapter Loaded)`
