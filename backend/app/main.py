from datetime import datetime
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.services.ocr_parser import create_parse_response
from app.storage.db import get_dataset, init_db, insert_dataset, insert_parse, list_datasets

app = FastAPI(title="Table OCR Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.post("/api/uploads/table-image")
async def upload_table_image(file: UploadFile = File(...), parser: str = "auto") -> JSONResponse:
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        return JSONResponse(
            {
                "ok": False,
                "parser": parser,
                "columns": [],
                "rows": [],
                "cell_conf": [],
                "warnings": ["Only PNG/JPG images are supported."],
                "parse_id": "",
            }
        )
    file_bytes = await file.read()
    result = create_parse_response(file_bytes, parser)
    if result["parse_id"]:
        insert_parse(
            parse_id=result["parse_id"],
            created_at=result["created_at"],
            parser=result["parser"],
            columns=result["columns"],
            rows=result["rows"],
            cell_conf=result["cell_conf"],
            warnings=result["warnings"],
        )
    return JSONResponse(result)


@app.post("/api/datasets")
async def create_dataset(payload: Dict[str, Any]) -> JSONResponse:
    name = payload.get("name")
    columns = payload.get("columns")
    rows = payload.get("rows")
    source_parse_id = payload.get("source_parse_id")
    if not name or not isinstance(columns, list) or not isinstance(rows, list):
        raise HTTPException(status_code=400, detail="Invalid payload")
    dataset_id = payload.get("dataset_id") or str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    insert_dataset(dataset_id, name, created_at, source_parse_id, columns, rows)
    return JSONResponse({"ok": True, "dataset_id": dataset_id})


@app.get("/api/datasets")
async def get_datasets() -> List[Dict[str, Any]]:
    return list_datasets()


@app.get("/api/datasets/{dataset_id}")
async def get_dataset_detail(dataset_id: str) -> Dict[str, Any]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def _normalize(values: List[Optional[float]]) -> List[float]:
    filtered = [v for v in values if v is not None]
    if not filtered:
        return [0.0 for _ in values]
    min_val = min(filtered)
    max_val = max(filtered)
    if min_val == max_val:
        return [50.0 if v is not None else 0.0 for v in values]
    return [((v - min_val) / (max_val - min_val)) * 100 if v is not None else 0.0 for v in values]


def _find_field(rows: List[Dict[str, Any]], targets: List[str]) -> Optional[str]:
    if not rows:
        return None
    sample_keys = {key.lower(): key for row in rows for key in row.keys()}
    for target in targets:
        if target.lower() in sample_keys:
            return sample_keys[target.lower()]
    return None


@app.get("/api/analysis/heatmap")
async def analysis_heatmap(dataset_id: str) -> Dict[str, Any]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    rows = dataset["rows"]
    warnings: List[str] = []
    rel_field = "RelVolTo90D" if any("RelVolTo90D" in r for r in rows) else "RelNotionalTo90D"
    price_field = _find_field(rows, ["PriceChgPct", "% Chg", "Change", "Change%"])
    rsi_field = _find_field(rows, ["RSI", "RSI14"])
    sma_field = _find_field(rows, ["SMA", "SMA20", "SMA50"])
    ivr_field = "IVR"
    rel_values = [r.get(rel_field) for r in rows]
    price_values = [r.get(price_field) if price_field else None for r in rows]
    ivr_values = [r.get(ivr_field) for r in rows]
    rsi_values = [r.get(rsi_field) if rsi_field else None for r in rows]
    sma_values = [r.get(sma_field) if sma_field else None for r in rows]
    rel_norm = _normalize([v if isinstance(v, (int, float)) else None for v in rel_values])
    price_norm = _normalize([v if isinstance(v, (int, float)) else None for v in price_values])
    ivr_norm = _normalize([v if isinstance(v, (int, float)) else None for v in ivr_values])
    rsi_norm = _normalize([v if isinstance(v, (int, float)) else None for v in rsi_values])
    sma_norm = _normalize([v if isinstance(v, (int, float)) else None for v in sma_values])
    if all(v == 0.0 for v in rel_norm) and all(v == 0.0 for v in rsi_norm):
        warnings.append("Relative volume/notional field missing; heatmap score uses price change only.")
    results = []
    for idx, row in enumerate(rows):
        score = rel_norm[idx] + price_norm[idx] + (ivr_norm[idx] if ivr_norm[idx] else 0.0)
        if rsi_field or sma_field:
            score = price_norm[idx] + rsi_norm[idx] + sma_norm[idx]
        score = max(0.0, min(score / 3 * 1.5, 100.0))
        results.append({"symbol": row.get("symbol") or row.get("Symbol"), "Score": round(score, 2), **row})
    results_sorted = sorted(results, key=lambda r: r.get("Score", 0), reverse=True)
    for rank, item in enumerate(results_sorted, start=1):
        item["Rank"] = rank
    return {"rows": results_sorted, "warnings": warnings}


@app.get("/api/analysis/momentum-stocks")
async def analysis_momentum(dataset_id: str, top: int = 10) -> Dict[str, Any]:
    dataset = get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    rows = dataset["rows"]
    warnings: List[str] = []
    rel_field = "RelVolTo90D" if any("RelVolTo90D" in r for r in rows) else "RelNotionalTo90D"
    results = []
    for row in rows:
        price = row.get("PriceChgPct") or 0
        rel = row.get(rel_field) or 0
        put_pct = row.get("PutPct")
        put_bonus = 0
        if put_pct is not None:
            put_bonus = max(0.0, (100 - put_pct) / 100 * 10)
        score = float(price) + float(rel) + put_bonus
        results.append({"symbol": row.get("symbol") or row.get("Symbol"), "StockScore": round(score, 2), **row})
    if not results:
        warnings.append("No rows available for momentum analysis.")
    results_sorted = sorted(results, key=lambda r: r.get("StockScore", 0), reverse=True)[:top]
    return {"rows": results_sorted, "warnings": warnings}
