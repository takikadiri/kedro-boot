# Getting started with the standalone mode - Running a kedro pipeline programatically from anywhere

The 1st key concept of ``kedro-boot`` is the ``KedroBootSession``. It is basically a standard ``KedroSession`` with 2 main differences:

- :zap: you can run the same session multiple times with many speed optimisation (including dataset caching)
- :syringe: you can pass data and parameters at runtime: ``session.run(inputs={"your_dataset_name": your_data}, itertime_params={"my_param": your_new_param})``

## Create a ``KedroBootSession`` object

The ``KedroBootSession`` can be created either: 
- from another kedro project by giving the path to this project
- from a python package (if the project as been previously packaged with ``kedro package``) 

::::{tab-set}

:::{tab-item} From a kedro project

Use the ``boot_project`` function to create the section: 

```python
from kedro_boot.app.booter import boot_project
from kedro_boot.framework.compiler.specs import CompilationSpec

session = boot_project(
    project_path="<your_project_path>",
    compilation_specs=[CompilationSpec(inputs=["your_dataset_name"])], # Would be infered if not given
    kedro_args={ # any arguments you can pass to "kedro run"
        "pipeline": "your_pipeline", # IMPORTANT : You must create one KedroBootSession per pipeline, except for namespaced pipelines
        "conf_source": "<your_conf_source>", # by default uses the one of your project
    },
)

# You can now run the session as many times as you want, and specify different inputs programatically
run_results = session.run(inputs={"your_dataset_name": your_data})
run_results2 = session.run(inputs={"your_dataset_name": your_data2})
```

:::

:::{tab-item} From a package

Use the boot_package function:

```python
from kedro_boot.app.booter import boot_package
from kedro_boot.framework.compiler.specs import CompilationSpec

session = boot_package(
    package_name="<your_package_name>",
    compilation_specs=[CompilationSpec(inputs=["your_dataset_name"])],
    kedro_args={
        "pipeline": "your_pipeline",
        "conf_source": "<your_conf_source>", # must be specified for a packaged project
    },
)

```

:::

::::

```important
You need to create **one ``KedroBootSession`` for per pipeline**, you cannot handle several pipelines in the same ``KedroBootSession`` except namespaced pipelines with the same namespace. 
```

## Run the pipeline programatically

### Running the session for the first time

Now that you have created your ``session object``, you can run it programatically like a standard kedro session. The main difference is that you have to pass your data programatically as inputs

```python
run_results = session.run(inputs={"your_dataset_name": your_data}) # run results will contain outputs as MemoryDataset
```

### Running the same session multiple time

You can run the *same* session multiple times, without recreating it with a different input: 

```python
run_results2 = session.run(inputs={"your_dataset_name": your_data2})
```

### Changing runtime parameters in the catalog between runs

Let assume that your ``catalog`` contains an entry with a ``runtime_parameter``you want to change between different runs on the same session, e.g.

```yaml
my_data: 
    type: pandas.ParquetDataset
    filepath: s3://my-bucket/partition_{$runtime_params:partition_id}.pq
```

With ``kedro-boot``, you need to change the resolver to ``itertime_params", so your code becomes:  

```yaml
my_data: 
    type: pandas.ParquetDataset
    filepath: s3://my-bucket/partition_{$itertime_params:partition_id}.pq
```

And now you can inject the parameter each time you run the session:

```python
run_results3 = session.run(inputs={"your_dataset_name": your_data3}, itertime_params={"partition_id": "03""})
```

<!-- ## Example gallery

You can found a complete example of a streamlit app that serves an ML model in the [Kedro Boot Examples](examples/README.md#data-app-with-streamlit-standalone-mode) project. We invite you to test it to gain a better understanding of Kedro Boot's ``boot_project`` or ``boot_package`` interfaces. 

> [!TIP]  
> The ``CompilationSpec`` gives you advanced control on how to configure the behaviour (which dataset to preload and cache, which arguments to pass on each iteration...). See [the documentation]() for more details.  -->
