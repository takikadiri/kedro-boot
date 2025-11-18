---
myst:
  html_meta:
    "description lang=en": |
      Top-level documentation for kedro-boot, with links to the rest
      of the site.
html_theme.sidebar_secondary.remove: true
---

# The kedro-boot plugin

``kedro-boot`` is a Kedro [plugin](https://docs.kedro.org/en/stable/extend_kedro/plugins.html) to run programmatically kedro pipelines from other applications (e.g. fastapi, streamlit, python scripts, airflow...).

Its main features are: 
- the ``KedroBootSession``, an improved ``KedroSession`` which gives you advancded control to run kedro programtically thanks to its many new functionalities: 
  - easy to setup (one line and you're good to go!)
  - much faster (thanks to multi-runs support,  artifact preloading, caching ...)
  - runtime data injection
  - runtime paramter injection
- the ``KedroBootApp``s, a way to modify how ``kedro run`` behaves (e.g. looping over a pipeline) with a one-line change in ``setting.py``
- ``Kedro Boot FastApi``, a default ``KedroBootApp`` to serve your kedro pipelines as API with one line of code.  


::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card}
:link: source/03_standalone_mode/01_getting_started_standalone_mode.html
:link-type: url
:class-header: bg-light

{fas}`code fa-xl;pst-color-primary` Programatically run kedro pipelines
^^^

Create a ``KedroBootSession`` to run pipelines programatically with fine grained control and speed

:::

:::{grid-item-card}
:link: source/04_embedded_mode/01_getting_started_embedded_mode.html
:link-type: url
:class-header: bg-light

{fas}`fa-tablet-screen-button fa-xl;pst-color-primary` Custom running logics  
^^^

Customize how ``kedro run`` works, e.g. for running it multiple times, with ``KedroBootApp``s
:::

::::

<!-- ## Resources

::::{grid} 1 1 3 3
:gutter: 3

:::{grid-item-card}
:link: source/02_gettnig_started/01_installation/01_installation.html
:link-type: url
:class-header: bg-light

{fas}`fa-solid fa-graduation-cap fa-xl;pst-color-primary` Quickstart
^^^

Get started in **1 mn** with experiment tracking!
+++
Try out {fas}`arrow-right fa-xl`
:::

:::{grid-item-card}
:link: https://github.com/Galileo-Galilei/kedro-mlflow-tutorial
:link-type: url
:class-header: bg-light

{fas}`fa-solid fa-chalkboard-user fa-xl;pst-color-primary` Advanced tutorial
^^^

The ``kedro-mlflow-tutorial`` github repo contains a step-by-step tutorial to learn how to use kedro-mlflow as a mlops framework!

+++
Try on github {fab}`github;fa-xl`
:::

:::{grid-item-card}
:link: https://www.youtube.com/watch?v=Az_6UKqbznw
:link-type: url
:class-header: bg-light

{fas}`fa-solid fa-video fa-xl;pst-color-primary` Demonstration in video
^^^

A youtube video by the kedro team to introduce the plugin, with live coding.

+++
See on youtube {fab}`youtube;fa-xl`
:::

::::

```{toctree}
---
maxdepth: 1
hidden: true
---
source/01_introduction/index
source/02_getting_started/index
source/03_experiment_tracking/index
source/04_pipeline_as_model/index
source/05_API/index
Changelog <https://github.com/Galileo-Galilei/kedro-mlflow/releases>
source/06_migration_guide/index
``` -->
