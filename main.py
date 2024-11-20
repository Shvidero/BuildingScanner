from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import shutil
import os
from datetime import datetime
import json

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("page-input.html", {"request": request})

@app.post("/page-output", response_class=HTMLResponse)
async def output(request: Request, x1: float = Form(...), y1: float = Form(...), x2: float = Form(...), y2: float = Form(...), img: UploadFile = File(...)):
    file_location = f"static/uploads/{img.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(img.file, buffer)

    img_url = f"/static/uploads/{img.filename}"

    data = {
        "date": datetime.now(),
        "coords": f"{x1}, {y1}, {x2}, {y2}",
        "object": "8 корпус",
        "address": "улица Образцова, 9с2",
        "floors": "5",
        "type": "Университет",
        "condition": "Удовлетворительно",
        "img": img_url,
    }

    return templates.TemplateResponse("page-output.html", {
        "request": request,
        **data
        })

@app.post("/export-geojson")
async def export_geojson(request: Request, date: str = Form(...), coords: str = Form(...), object: str = Form(...), address: str = Form(...), floors: str = Form(...), type: str = Form(...), condition: str = Form(...)):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": list(map(float, coords.split(',')))
                },
                "properties": {
                    "date": date,
                    "object": object,
                    "address": address,
                    "floors": floors,
                    "building_type": type,
                    "building_condition": condition,
                }
            }
        ]
    }

    geojson_file = "static/uploads/export.geojson"
    with open(geojson_file, "w") as f:
        json.dump(geojson_data, f)

    return FileResponse(geojson_file, filename="export.geojson", media_type="application/geo+json")
