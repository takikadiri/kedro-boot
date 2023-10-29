![Kedro Boot Logo - Ligh](.github/logo_light.png#gh-light-mode-only)
![Kedro Boot Logo - Dark](.github/logo_dark.png#gh-dark-mode-only)
[![Python version](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://pypi.org/project/kedro/)
[![PyPI version](https://badge.fury.io/py/kedro-boot.svg)](https://badge.fury.io/py/kedro-boot)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/takikadiri/kedro-boot/blob/main/LICENSE)
[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)

# What is kedro-boot ?
Kedro Boot is a [kedro plugin](https://docs.kedro.org/en/stable/extend_kedro/plugins.html) that streamlines the integration between Kedro projects and external applications. It offers a structured method for seamlessly interacting with kedro's pipeline and catalog. This include features like injecting application data into kedro catalog and dynamically orchestrating multiple kedro pipeline runs.

This enable using Kedro pipelines in a wide range of online and low latency use cases, including model serving, data apps (streamlit, dash), statistical simulations, paralell processing of unstructured data, streaming, and more.

_If you're new to [kedro](https://github.com/kedro-org/kedro), we invite you to visit [kedro docs](https://docs.kedro.org/en/stable/)_

# How do I install Kedro Boot ?

``kedro-boot`` is available on PyPI, so you can install it with pip:

```
pip install kedro-boot
```

Kedro Boot requires Kedro version 0.18.1 or higher and has Kedro as its only dependency

# How do I use Kedro Boot ? 

Kedro Boot provides utilities and abstractions for registering application pipelines and implementing Kedro Boot apps. In the following section, we'll guide you through an example that demonstrates how to use Kedro Boot in a model serving scenario. This example will help you grasp Kedro Boot's interface and concepts as we show you how to register an inference pipeline and use it in two model serving deployment patterns: a REST API with FastAPI and a Data App with Streamlit.

## Registring the application pipeline

To register an application pipeline, you need to create an ``AppPipeline`` in the ``pipeline_registry`` using ``app_pipeline`` factory : 

pipeline_registry.py
```python
from kedro_boot.pipeline import app_pipeline

app_inference_pipeline = app_pipeline(
        inference_pipeline,
        name="inference",
        inputs="features_store",
        artifacts="training.regressor",
        outputs="inference.predictions",
    )

return {"__default__": app_inference_pipeline}
```

Here the ``app_pipeline`` take a Kedro ``Pipeline`` and define an applicatif view on top of it. The ``AppPipeline`` will be used to compile the ``AppCatalog``, making it ready for the iteractions with the Kedro Boot app. Below are the different categories of datasets in the ``AppCatalog``.

- Inputs: inputs datasets that will be injected by the app at iteration time.
- Outputs: outputs dataset that hold the run results.
- Parameters: parameters that will be injected by the app at iteration time.
- Artifacts: artifacts datasets that will be materialized (loaded as MemoryDataset) at startup time.
- Templates: template datasets that contains jinja expressions in this form "[[ expression ]]". These templates will be rendered by the app template_params at iteration time

You can perform a dry run to compile the ``AppCatalog`` without actually using it in a Kedro Boot app. This is helpful when letting the ``app_pipeline`` automatically infer artifact datasets or to verify if the template datasets are correctly detected.

```
kedro boot --dry-run
```
Compilation results:
```
INFO  catalog compilation completed for the pipeline view 'inference'. Here is the report:                                                          
        - Input datasets to be replaced/rendered at iteration time: {'features_store'}
        - Output datasets that hold the results of a run at iteration time: {'inference.predictions'}
        - Parameter datasets to be replaced/rendered at iteration time: set()
        - Artifact datasets to be materialized (preloader as memory dataset) at startup time: {'training.regressor'}
        - Template datasets to be rendered at iteration time: set()
		
INFO  Catalog compilation completed.           
```

## Implementing and integrating the application

There is two way of integrating an application with Kedro using Kedro Boot. In both approaches, Kedro Boot create a ``KedroBootSession`` for the application to manage it's interactions with kedro project.

### Embedded mode : Model serving with FastApi 

This mode involves using Kedro Boot to embed an application inside a Kedro project, leveraging kedro's entry points, session and config loader for managing application lifecycle. It's suitable for use cases when the application is lightweight and owned by the same team that developed the kedro pipelines.

Here, we present an example of low-latency model serving using a FastAPI app as a Kedro Boot App. We serve an entire Kedro pipeline, including not just the model artifact, but also any preprocessing and postprocessing steps typically included within the prediction endpoints. 
As the model dataset has been registered as an artifact, it will be materialized/loaded as a MemoryDataset at catalog compilation time to optimize inference speed.
```python
from datetime import datetime
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from kedro_boot.app import AbstractKedroBootApp
from kedro_boot.session import KedroBootSession


class FastApiApp(AbstractKedroBootApp):
    def _run(self, kedro_boot_session: KedroBootSession) -> None:

        # Create fastapi app
        fastapi_app = fastapi_app_factory(kedro_boot_session)

        # A kedro boot apps leverage config_loader to manage it's configs
        fastapi_args = kedro_boot_session.config_loader.get("fastapi.yml")

        uvicorn.run(fastapi_app, **fastapi_args)


def fastapi_app_factory(kedro_boot_session: KedroBootSession) -> FastAPI:
    # Create an instance of the FastAPI class
    app = FastAPI(title="Spaceflight shuttle Price prediction")

    # Define a Pydantic model for Shuttle Feature
    class ShuttleFeature(BaseModel):
        engines: int = 2
        passenger_capacity: int = 5
        crew: int = 5
        d_check_complete: bool = False
        moon_clearance_complete: bool = False
        iata_approved: bool = False
        company_rating: float = 0.95
        review_scores_rating: int = 88

    # Create a POST endpoint to receive shuttle features JSON data
    @app.post("/predict")
    def predict_shutlle_price(shuttle_features: ShuttleFeature):

        shuttle_price = kedro_boot_session.run(
            name="inference", inputs={"features_store": shuttle_features.dict()}
        )
        return shuttle_price.tolist()

    return app
```

An embedded Kedro Boot app is an implementation of the ``AbstractKedroBootApp``. In this implementation, we define the ``_run`` method, which involves creating the FastAPI app, retrieving configurations using the config_loader, and then launching the Uvicorn web server.

The FastAPI app utilizes the ``KedroBootSession`` to perform runs on the inference pipeline, injecting data and retrieving outputs at each run iteration.

Here is the command to run a kedro boot app. You can refer to ``--help`` for more options details

```
kedro boot --app <package_name>.<module_name>.FastApiApp
```

You can found the complete example code in the [Kedro Boot Examples](https://github.com/takikadiri/kedro-boot-examples) repo. We invite you to test it to gain a better understanding of Kedro Boot

### Standalone mode : Data App with Streamlit	
This mode refers to using Kedro Boot in an external application that has its own entry point. It's suitable for scripting apps that need their own runner tool or for large application that already exist before the kedro project, and may have been developed by a different team.

```python
import pandas as pd
import streamlit as st
from kedro_boot.booter import boot_session

kedro_boot_session = boot_session()

st.title("Spaceflight shuttle Price prediction")

with st.container():
    with st.form("my_form"):
        st.write("Shuttle Price Prediction")
        shuttle = {
            "engines": st.slider("engines", 0, 12, 2),
            "passenger_capacity": st.slider("passenger_capacity", 1, 20, 5),
            "crew": st.slider("crew", 0, 20, 5),
            "d_check_complete": st.checkbox("d_check_complete"),
            "moon_clearance_complete": st.checkbox("moon_clearance_complete"),
            "iata_approved": st.checkbox("iata_approved"),
            "company_rating": st.slider("company_rating", 0.0, 1.0, 0.95),
            "review_scores_rating": st.slider("review_score_rating", 20, 100, 88),
        }

        submitted = st.form_submit_button("Predict Price")

if submitted:
    shuttle_df = pd.DataFrame(shuttle, index=[0])
    # Running inference app_pipeline
	shuttle_price = kedro_boot_session.run(
        name="inference", inputs={"features_store": shuttle_df}
    )
    shuttle_price = shuttle_price.tolist()
    formated_shuttle_price = round(shuttle_price[0], 3)

    st.success(f"The predicted shuttle price is {formated_shuttle_price} $")

```

A Standalone app uses ``boot_session`` to create a ``KedroBootSession`` within the app. The app then leverages the ``KedroBootSession`` to perform multiple ``AppPipeline`` runs, similar to the embedded mode.

This streamlit app own the entry point, so we can start the app by : 

```
streamlit run /path/to/streamlit_app/script.py
```

Note that in this example, we don't provide any arguments to ``boot_session``. By default, it expects the current working directory to point to a Kedro project. If the Kedro project is located elsewhere, you can pass the ``project_path`` to ``boot_session`` to help it locate the Kedro project. Additionally, you can pass additional arguments for Kedro session creation and running. For more details, please refer to the ``boot_session`` docstring

You can found the complete example code in the [Kedro Boot Examples](https://github.com/takikadiri/kedro-boot-examples) repo. We invite you to test it to gain a better understanding of Kedro Boot

The [Kedro Boot Examples](https://github.com/takikadiri/kedro-boot-examples) repo contains also an example of monte carlo simulation for Pi estimation, showing a way to dynamically compose/orchestrate kedro pipelines at runtime, while using [kedro-mlflow](https://github.com/Galileo-Galilei/kedro-mlflow) hooks to track simulation's metrics

## Why does Kedro Boot exist ?

Kedro Boot unlock the value of your kedro pipelines by giving you a structured way for integrating them in a larger application. We developed kedro-boot to achieve the following : 

- Streamline deployment of kedro pipelines in a non-batch world : web services (Rest API, Data apps, ...), streaming, HPC
- Encourage reuse and prevent rewriting pipeline's logic from the team that own the front application
- Leverage kedro's capabilities for business logic separation and authoring
- Leverage kedro's capabilities for managing application lifecycle

Kedro Boot apps utilize Kedro's pipeline as a means to construct and manage business logic. Kedro's underlying principles and internals ensure the maintainability, clarity, reuse, and visibility (kedro-viz) of business logic within Kedro Boot apps, thanks to Kedro's declarative nature.

While Kedro Boot apps adopts the declarative approach for handling its business logic, it opt for an explicit and imperative approach for orchestrating and utilizing this logic, allowing for a wide range of use cases. We believe that this blend of declarative and imperative approaches through Kedro Boot can enable the development of end-to-end production-ready data science applications.

## Where do I test Kedro Boot ?

You can refer to the Kedro Boot Examples repository; it will guide you through three examples of Kedro Boot usages.

## Can I contribute ?

We'd be happy to receive help to maintain and improve the package. Any PR will be considered.