from fastapi import FastAPI

from kedro_boot.app.fastapi import KedroFastApi

app = FastAPI()


@app.get("/run", tags=["Run Pipeline"])
def run_pipeline(run_results: KedroFastApi):
    return run_results
