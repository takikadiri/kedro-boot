from datetime import datetime
import uvicorn
from fastapi import FastAPI
from kedro_boot.app import AbstractKedroBootApp
from kedro_boot.framework.session import KedroBootSession
from pydantic import BaseModel


class FastApiApp(AbstractKedroBootApp):
    def _run(self, kedro_boot_session: KedroBootSession) -> None:
        # Create fastapi app while injecting kedro_boot_session.
        fastapi_app = fastapi_app_factory(kedro_boot_session)

        # A kedro boot app leverage config_loader to manage it's configs
        fastapi_args = kedro_boot_session.config_loader["fastapi"].get("server", {})

        uvicorn.run(fastapi_app, **fastapi_args)


def fastapi_app_factory(kedro_boot_session: KedroBootSession) -> FastAPI:
    # Create an instance of the FastAPI class
    app = FastAPI(title="Spaceflights shuttle price prediction")

    # Define a Pydantic model for the JSON data
    class ShuttleFeature(BaseModel):
        engines: int = 2
        passenger_capacity: int = 5
        crew: int = 5
        d_check_complete: bool = False
        moon_clearance_complete: bool = False
        iata_approved: bool = False
        company_rating: float = 0.95
        review_scores_rating: int = 88

    # Create a POST endpoint to receive JSON data
    @app.post("/predict", tags=["prediction"])
    def predict_shutlle_price(shuttle_features: ShuttleFeature):
        # Replace the kedro datasets "items" with this json data, then run the pipeline. Would be more clean if we used the dependency injection mechanisms for injecting the kedro_boot_session into this endpoint.
        shuttle_price = kedro_boot_session.run(
            namespace="inference", inputs={"features_store": shuttle_features.dict()}
        )
        return shuttle_price

    @app.get("/evaluate", tags=["evaluation"])
    def run_evaluation_pipeline():
        # Render the Jinja Template from the Path parameter received by the endpoint. Here we used another pipeline namespace to perform the logic of this endpoint
        current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        kedro_boot_session.run(
            namespace="evaluation", itertime_params={"eval_date": current_datetime}
        )
        # response example
        return {
            "status": "success",
            "app_pipeline": "evaluation",
            "template_params": {"eval_date": current_datetime},
        }

    return app
