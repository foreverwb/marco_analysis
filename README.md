# Table OCR Parser (FastAPI + React)

This project provides a simple OCR pipeline for table screenshots, MarketChameleon parser support, and a lightweight React UI for editing and analysis.

## Requirements

### Tesseract OCR (system dependency)

- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download installer from https://github.com/UB-Mannheim/tesseract/wiki

If Tesseract is missing, the backend returns an error message indicating that it must be installed.

## Backend (FastAPI)

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

The frontend will proxy `/api` to `http://localhost:8000`.

## Samples

Binary sample images are not included to keep the repo compatible with environments that reject binary files.
Place your own screenshots under `samples/` (see `samples/README.md`).

## Sample curl

### Upload image

```bash
curl -F "file=@samples/sample_table.png" "http://localhost:8000/api/uploads/table-image?parser=auto"
```

### Create dataset

```bash
curl -X POST http://localhost:8000/api/datasets \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo","columns":["symbol"],"rows":[{"symbol":"AAPL"}],"source_parse_id":"demo"}'
```

### Heatmap analysis

```bash
curl "http://localhost:8000/api/analysis/heatmap?dataset_id=<dataset_id>"
```

### Momentum analysis

```bash
curl "http://localhost:8000/api/analysis/momentum-stocks?dataset_id=<dataset_id>&top=10"
```
