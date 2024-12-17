from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime #Для криминала
import requests
import shutil
import json

# Делаем чики брик соль
app = FastAPI()

# Говорим, где борзая статика
app.mount("/static", StaticFiles(directory="static"), name="static")

# Говорим, где хтмлы
templates = Jinja2Templates(directory='templates')

kukarekuli = [
    {'name': 'Кукареку Большое'},
    {'name': 'Кукареку Медианное'},
    {'name': 'Кукареку Малое'},
]

# Че должно выводиться по пилипиздрику /
@app.get('/')
def root(request: Request):
    # Возвращаем хтмл, рейх(сам хз зач он нужен), и всякое другое
    return templates.TemplateResponse('page-input.html', 
                                      {'request': request, 
                                        'Poporatsii': 'Ох же и заебали это Попорации',
                                        'kukarekuli': kukarekuli})

# Постая бодяга с координатами для парсинга
scrapping_coords = []

# Какие данные принимаются на адресс /
@app.post('/')
def scrapping_output(request: Request, x: str=Form(...), y: str=Form(...)):
    scrapping_coords.append({'x': float(x), 'y': float(y)})
    context = {
        'request': request,
        'coords': scrapping_coords,
        'coords_count': len(scrapping_coords)
        }
    return templates.TemplateResponse('page-input.html', context)


# Бурдюк для пути шмути
output_data = []

def get_osm_data_by_coordinates(latitude, longitude, radius=100):
    # Формируем запрос для Overpass API
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"](around:{radius},{latitude},{longitude});
      way["amenity"](around:{radius},{latitude},{longitude});
      relation["amenity"](around:{radius},{latitude},{longitude});
    );
    out body;
    """
    
    response = requests.post(overpass_url, data=overpass_query)
    
    if response.status_code != 200:
        print("Ошибка при получении данных от Overpass API")
        return None

    data = response.json()
    
    results = []
    for element in data['elements']:
        name = element.get('tags', {}).get('name', 'Нет названия')
        amenity = element.get('tags', {}).get('amenity', 'Не указано')
        results.append({'name': name, 'amenity': amenity})

    return results

# Андрюху чуп чуп через Яндекс
def get_building_address(lat, lon, api_key_geocode):
    # Получение информации о здании
    geocode_url = f"https://geocode-maps.yandex.ru/1.x/?lang=ru_RU&apikey={api_key_geocode}&geocode={lon},{lat}&format=json"
    geocode_response = requests.get(geocode_url)
    geocode_data = geocode_response.json()

    if geocode_response.status_code == 200:
        found = geocode_data['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found']

        if int(found) > 0:
            # Извлечение адреса
            geo_object = geocode_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
            address_details = geo_object['metaDataProperty']['GeocoderMetaData']['Address']['Components']

            country = next((comp['name'] for comp in address_details if comp['kind'] == 'country'), 'Нет данных')
            province = next((comp['name'] for comp in address_details if comp['kind'] == 'province'), 'Нет данных')
            locality = next((comp['name'] for comp in address_details if comp['kind'] == 'locality'), 'Нет данных')
            street = next((comp['name'] for comp in address_details if comp['kind'] == 'street'), 'Нет данных')
            premise_number = next((comp['name'] for comp in address_details if comp['kind'] == 'house'), 'Нет данных')

            address_parts = [country, 'г. ' + locality if locality != 'Нет данных' else '', street, 'д. ' + premise_number if premise_number != 'Нет данных' else '']
            address = ', '.join(filter(None, address_parts))
            print(f"Адрес: {address}")
            return address

        else:
            print("Информация о здании не найдена.")
    else:
        print(f"Ошибка запроса геокодирования: {geocode_response.status_code}")
        print(f"Сообщение об ошибке: {geocode_data.get('message', 'Нет сообщения об ошибке')}")

@app.post("/page-output", response_class=HTMLResponse)
async def output(request: Request, x1: float = Form(...), y1: float = Form(...), x2: float = Form(...), y2: float = Form(...), img: UploadFile = File(...)):
    
    # Дальше хуй локация файла с имгшками
    file_location = f"static/uploads/{img.filename}"
    # Запаисываем изображение которое сослали
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(img.file, buffer)
    # Ссылка на залипалу нашу
    img_url = f"/static/uploads/{img.filename}"

    # Бодро как    
    for coords in scrapping_coords:
        #Типо тип и типо название
        scrapped_data = get_osm_data_by_coordinates(coords['x'], coords['y'], 50)
        scrapped_names = [i['name'] for i in scrapped_data]
        scrapped_types = [i['amenity'] for i in scrapped_data]
        #Дал на клешню лысому (типо адрес)
        api_key_geocode  = '00536d0e-fff8-47c9-9c3d-ef4298641e85' #мой API ключ для Яндекс.Геокодер
        scrapped_address =  get_building_address(coords['x'], coords['y'], api_key_geocode)
        output_data.append(
            {
            "date": datetime.now(),
            "coords": f'{coords["x"]}, {coords["y"]}',
            "address": scrapped_address,
            "object": scrapped_names,
            "type": scrapped_types,
            "floors": "-",
            "condition": "-",
            }
        )

    return templates.TemplateResponse("page-output.html", {
        "request": request,
        'data': output_data
        })

    
@app.get('/clear')
async def clear_data(request: Request):
    
    global scrapping_coords
    scrapping_coords.clear()
    
    global output_data
    output_data.clear()
    
    context = {
        'request': request
    }
    

    return templates.TemplateResponse("page-output.html", {
        "request": request,
        'data': output_data
        })



@app.post("/export-geojson")
async def export_geojson(request: Request, date: str = Form(...), coords: str = Form(...), object: str = Form(...), address: str = Form(...), floors: str = Form(...), type: str = Form(...), condition: str = Form(...)):
# async def export_geojson(request: Request, data: list[dict[str, str, str, str, str ,str]] = Form(...)):
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
                # 'data': data
            }
        ]
    }

    geojson_file = "static/uploads/export.geojson"
    with open(geojson_file, "w") as f:
        json.dump(geojson_data, f)

    return FileResponse(geojson_file, filename="export.geojson", media_type="application/geo+json")


# Старина
# @app.post("/export-geojson")
# async def export_geojson(request: Request, date: str = Form(...), coords: str = Form(...), object: str = Form(...), address: str = Form(...), floors: str = Form(...), type: str = Form(...), condition: str = Form(...)):
#     geojson_data = {
#         "type": "FeatureCollection",
#         "features": [
#             {
#                 "type": "Feature",
#                 "geometry": {
#                     "type": "Point",
#                     "coordinates": list(map(float, coords.split(',')))
#                 },
#                 "properties": {
#                     "date": date,
#                     "object": object,
#                     "address": address,
#                     "floors": floors,
#                     "building_type": type,
#                     "building_condition": condition,
#                 }
#             }
#         ]
#     }

#     geojson_file = "static/uploads/export.geojson"
#     with open(geojson_file, "w") as f:
#         json.dump(geojson_data, f)

#     return FileResponse(geojson_file, filename="export.geojson", media_type="application/geo+json")