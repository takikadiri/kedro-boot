from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from kedro_boot.app.fastapi.session import KedroFastApi

app = FastAPI(title="Kedro FastAPI Server")


@app.get("/run", tags=["Run Pipeline"])
async def pipeline(run_results: KedroFastApi):
    return run_results


@app.get("/")
async def docs_redirect():
    return RedirectResponse(url="/docs")
