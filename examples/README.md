# Kedro Boot Examples

In this tutorial, we construct pipelines and applications for a price-prediction model to illustrate the steps of a typical [Kedro Boot](https://github.com/takikadiri/kedro-boot) workflow.

_It is 2160, and the space tourism industry is booming. Globally, thousands of space shuttle companies take tourists to the Moon and back. You have been able to source data that lists the amenities offered in each space shuttle, customer reviews, and company information._

Project: You want to construct a model that predicts the price for each trip to the Moon and the corresponding return flight. The model need to be deployed in a REST API and in a Data App.

In addition, this project offers a bonus tutorial on using [Kedro Boot](https://github.com/takikadiri/kedro-boot) to conduct a Monte Carlo simulation for estimating Pi

If you're new to [kedro](https://github.com/kedro-org/kedro), we invite you to visit [kedro docs](https://docs.kedro.org/en/stable/)

## Install the project

To install the project and its dependencies, run pip install command in a virtual environment :

```
pip install .
````

## Data preparation and model training

You can begin by feeding the features-store using ``data_processing`` pipeline. 

```
kedro run --pipeline data_processing
```

Then you need to train a regressor using features-store data.

```
kedro run --pipeline training
```

## Model deployment

In order to expose your kedro pipelines to a kedro boot application, you need to create namespaced pipelines. All namespaced datasets of the pipeline (inputs, outputs, parameters) will be exposed to the app. 

```python
# create inference namespace. All the inference pipeline's datasets will be exposed to the app, except "regressor" and "model_options.
inference_pipeline = pipeline(
    [features_nodes, prediction_nodes],
    inputs={"regressor": "training.regressor"},
    parameters="model_options",
    namespace="inference",
)
# create evaluation namespace. All the evaluation pipeline's datasets will be exposed to the app, except "feature_store", "regressor" and "model_options.
evaluation_pipeline = pipeline(
    [model_input_nodes, prediction_nodes, evaluation_nodes],
    inputs={"features_store": "features_store", "regressor": "training.regressor"},
    parameters="model_options",
    namespace="evaluation",
)

spaceflights_app_pipelines = inference_pipeline + evaluation_pipeline

return {"__default__": spaceflights_app_pipelines}
```

### Rest API with Kedro FastAPI Server

The FastApi app run inside the [Kedro FastAPI Server](../README.md#consuming-kedro-pipeline-through-rest-api). It serves two endpoints:

- /predict : take the shuffle features, run the inference pipeline and get the prediction results
- /evaluate : trigger the evaluation pipeline, while injecting eval_date as path parameter and r2_multioutput as query parameter. at each run it save the evaluation results in ``data/07/model_output/regression_score_${itertime_params:eval_date}.json`` eval_date is mapped to the itertime_params and r2_multioutput is mapped to kedro parameters

You can start your FastAPI App with

```
kedro boot fastapi --app spaceflights_kedro_fastapi.app.app
```

Then go to http://localhost:8000/docs for trying out your FastAPI App.

![fastapi](.github/fastapi.png)

The gunicorn or uvicorn (web server) args can be updated using conf/base/fastapi.yml
<!-- 
### Rest API with FastAPI

The FastApi app is integrated into kedro project in an [embedded mode](https://github.com/takikadiri/kedro-boot#embedded-mode--model-serving-with-fastapi). It serve two endpoints :

- /predict : take the shuffle features, run the inference pipeline and get the prediction results
- /evaluate : trigger the evaluation pipeline, at each run it save the evaluation results in ``data/07/model_output/regression_score_[[ eval_date ]].json`` eval_date is rendered at iteration time.

You can start the FatApi App by running : 

```
kedro boot --app spaceflights_fastapi.app.FastApiApp
```

Then go to http://localhost:8000/docs for trying out your FastAPi App.

![fastapi](.github/fastapi.png)

The uvicorn or gunicorn (web server) args can be updated using conf/base/fastapi.yml -->

### Data App with Streamlit (Standalone mode)

The Streamlit app consume kedro pipeline in a [standalone mode](../README.md#standalone-mode-the-application-hold-the-entry-point).

You can start the Streamlit App by running : 

```
streamlit run src/spaceflights_streamlit/app.py
```

Streamlit typically opens your Streamlit app in a new browser tab. If it doesn't, you can obtain the local URL from the terminal. 
You can try the app by modifying the shuttle features and calculating the associate prediction.

![streamlit](.github/streamlit.png)

## Monte Carlo Simulation (Embeded mode)

The Monte Carlo App consume kedro pipeline in an [embeded mode](../README.md#embedded-mode--the-application-is-embeded-inside-kedro-project).
In this example we'll estimate Pi using monte carlo simulation. This demonstrates how to utilize [Kedro Boot](https://github.com/takikadiri/kedro-boot) in a dynamic pipeline scenario. The monte carlo app perform multiple pipeline runs and merge their results to calculate Pi.

You can configure the app using ``conf/base/monte_carlo.yml`` and start it by running : 

```
kedro boot run --app monte_carlo_pi.app.MonteCarloApp --pipeline monte_carlo
```

You can disable logs using logging.yml to speed up simulation.





