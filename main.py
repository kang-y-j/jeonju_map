from fastapi import FastAPI
from fastapi.responses import FileResponse
import pandas as pd

app = FastAPI()

@app.get("/api/bus-stops")
def get_bus_stops():
    df = pd.read_csv("data/bus_stop_utf8.csv", encoding="utf-8-sig")
    df = df.dropna(subset=["위도", "경도"])
    return df[["정류장명", "위도", "경도"]].to_dict(orient="records")

@app.get("/")
def read_index():
    return FileResponse("index.html")