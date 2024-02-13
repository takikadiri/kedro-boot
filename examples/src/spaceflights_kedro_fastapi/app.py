from typing import List
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from kedro_boot.app.fastapi.session import KedroFastApi


app = FastAPI(title="Spaceflights shuttle price prediction")


class ShuttleFeature(BaseModel):
    engines: int = 2
    passenger_capacity: int = 5
    crew: int = 5
    d_check_complete: bool = False
    moon_clearance_complete: bool = False
    iata_approved: bool = False
    company_rating: float = 0.95
    review_scores_rating: int = 88


class ShuttlePrediction(BaseModel):
    shuttles_prices: List[float]


@app.post("/predict", tags=["Inference"], operation_id="inference")
def predictions(
    features_store: ShuttleFeature, kedro_run: KedroFastApi
) -> ShuttlePrediction:
    return {"shuttles_prices": kedro_run}


@app.get("/evaluate/{eval_date}", tags=["Evaluation"], operation_id="evaluation")
async def run_evaluation_pipeline(
    eval_date: str,
    kedro_run: KedroFastApi,
    r2_multioutput: str = Query("uniform_average"),
) -> dict:
    return kedro_run


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")
