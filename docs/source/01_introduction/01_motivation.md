# Overview

``kedro-boot`` tries to solve 3 differents issues of kedro (as of ``kedro==0.19.X``) which occur when deploying kedro projects. 

## The standalone mode - Programmatically call the Kedro Session

```{note}
Detailed motivations and issues with current kedro beahviour is described in the [Universal Kedro Deployment (Part 4) - Embedding kedro pipelines in third-party applications design document](https://github.com/kedro-org/kedro/issues/3540).
```

We want to use the ``KedroSession`` object programmatically *outside a kedro project* to control its behaviour in another application.

The **key feature is to make the ``KedroSession`` runnable multiple times**, so that we do not have to rebuilt the entire objects (which is slow and complicated) for each execution. This needs a couple of optimization for speed and flexibility:

- **runtime data injection**: we should be able to pass data in memory to the session to override a dataset, and not force the dataset to read it from a persisted source
- **runtime params injection**: we should be able to modify parameters between each execution to modify the behaviour
- **artifacts preloading**: we should be able to preload and cache once for all session exeuxtions some input data with a high I/O cost (e.g. a machine learning model should not be hot reloaded on eeach predict, but only once )

Basically, we would like to be able to execute the following code: 

```python
# PSEUDO CODE - Non runnable  in plain kedro, this is a fictitious API
session=KedroSession.create(project_path)
session.preload(artifacts=["my_model", "my_encoder"]) # :sparkles: FEATURE 1: preload artifacts, cache them and not not release them between runs for speed
session.run(pipeline="my_pipeline", runtime_data={"data": data1}) # :sparkles: FEATURE 2: inject data at runtime from the session
session.run(pipeline="my_pipeline", runtime_params= {"customer_id": id}) # :sparkles: FEATURE 3: run the same session mulitple times + :sparkles: FEATURE 4: inject runtime params at... runtime  (as the name says!) instead of instantation time 
```

```tip
Running the session programatically is very convenient when you want to call kedro in a programm that owns the entrypoint (e.g. you launch the app with a command different from ``kedro run`` like ``streamlit run``, ``uvicorn run``...)
```

``kedro-boot`` offers the [``KedroBootSession`` object]() to achieve this behaviour.

## The embedded mode - Modify the ``kedro run`` behaviour

```{note}
Detailed motivations and issues with current kedro beahviour is described in the [Universal Kedro deployment (Part 3) - Add the ability to extend and distribute the project running logic ](https://github.com/kedro-org/kedro/issues/1041).
```

Kedro offers a lot of way to modify the way the ``KedroSession`` behaves (mainly through hooks), but we sometimes want to modify the way the ``KedroSession`` is ran. The most common use case is when you want to loop over the ``KedroSession`` and run it multiples times with different parameters, e.g. for hyperparameter tuning. 