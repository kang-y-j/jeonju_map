import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
import pandas as pd

app = FastAPI()

DATA_DIR = "data"


def _read_csv(name: str, required: list[str]) -> list[dict]:
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path, encoding="utf-8-sig")
    df = df.dropna(subset=[c for c in required if c in df.columns])
    return df.to_dict(orient="records")


@app.get("/api/bus-stops")
def get_bus_stops():
    return _read_csv("bus_stop_utf8.csv", ["위도", "경도"])


@app.get("/api/parks")
def get_parks():
    return _read_csv("park_utf8.csv", ["위도", "경도"])


@app.get("/api/parkings")
def get_parkings():
    return _read_csv("parking_utf8.csv", ["위도", "경도"])


@app.get("/")
def read_index():
    return FileResponse("index.html")
