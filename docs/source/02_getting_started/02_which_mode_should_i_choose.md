# How to know which mode I should choose? 

- If you want to **call a kedro pipeline programatically in a third party application** launched with its own command (eg. ``streamlit run``, ``uvicorn run``, datarobot...), see the [standalone mode](../04_standalone_mode/01_getting_started_standalone_mode.md) and the concept of ``KedroBootSession``.
- If you want to **change the behaviour of ``kedro run`` CLI command** (e.g. to loop over the session multiple times), see the [embedded mode](../05_embedded_mode/01_getting_started_embedded_mode.md) and the concept of ``KedroBootApp`` (which is powered by the ``KedroBootSession``).
- if you want to **serve a kedro pipeline as an API**, see the [KedroBootFastapi tutorial](../06_fastapi_pipeline_serving/01_getting_started_kedro_fast_api_app.md) (which is a specific type of ``KedroBootApp``)

```{tip}
You will notice that the different components are not independent, and it is preferable to follow the documentation linearly to get a better understanding of the concepts: ``KedroFastAPI`` is a specific type of ``KedroBootApp`` which is itself powered by the ``KedroBootSession``.

However, if you are in a hurry you can just go to the "getting started" section of each mode which is self contained.
```