from fastapi import FastAPI, APIRouter
from databases import Database
import os
import json

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

database = Database(DATABASE_URL)

app = FastAPI()
router = APIRouter(prefix="/fastapi")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@router.post("/search/part/")
async def search_parts(body: dict):
    mark_name = body.get('mark_name')
    part_name = body.get('part_name')
    params = body.get('params', {})
    page = body.get('page', 1)
    price_gte = body.get('price_gte')
    price_lte = body.get('price_lte')

    query = """
               SELECT parts_part.*, parts_mark.id AS mark_id, parts_mark.name AS mark_name, parts_mark.producer_country_name,
                      parts_model.id AS model_id, parts_model.name AS model_name
               FROM parts_part
               JOIN parts_mark ON parts_part.mark_id = parts_mark.id
               JOIN parts_model ON parts_part.model_id = parts_model.id
               WHERE parts_part.is_visible = TRUE
           """

    conditions = []
    if mark_name:
        conditions.append(f"parts_mark.name ILIKE '%{mark_name}%'")
    if part_name:
        conditions.append(f"parts_part.name ILIKE '%{part_name}%'")
    if 'color' in params:
        conditions.append(f"parts_part.json_data ->> 'color' = '{params['color']}'")
    if 'is_new_part' in params:
        conditions.append(f"parts_part.json_data ->> 'is_new_part' = '{json.dumps(params['is_new_part'])}'")
    if price_gte is not None:
        conditions.append(f"parts_part.price >= {price_gte}")
    if price_lte is not None:
        conditions.append(f"parts_part.price <= {price_lte}")

    if conditions:
        query += " AND " + " AND ".join(conditions)

    count_query = f"SELECT COUNT(*) FROM ({query}) AS count_query"
    total_count = await database.fetch_one(count_query)

    sum_query = f"SELECT SUM(price) FROM ({query}) AS sum_query"
    total_sum = await database.fetch_one(sum_query)

    offset = (page - 1) * 10
    query += f" OFFSET {offset} LIMIT 10"

    parts_result = await database.fetch_all(query)

    results = [
        {
            "mark": {"id": part['mark_id'], "name": part['mark_name'],
                     "producer_country_name": part['producer_country_name']},
            "model": {"id": part['model_id'], "name": part['model_name']},
            "name": part['name'],
            "json_data": part['json_data'],
            "price": part['price']
        }
        for part in parts_result
    ]

    return {"response": results, "count": total_count[0], "summ": total_sum[0]}
