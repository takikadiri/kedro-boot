# Installing kedro-boot

```{important}
``kedro-boot`` only support ``kedro>=0.19``
```

## Installing from PyPI (Recommended)

``kedro-boot`` is distributed as [python package on PyPI](https://pypi.org/project/kedro-boot/). You can install it with your favourite package manger, e.g.

```bash
pip install kedro-boot
```

```{important}
It is very recommended to install it inside a virtual environment.
```

## Installing from source

You can also install the latest development version directly from github (only if you want to use the latest features) :

```bash
pip install git+https://github.com/takikadiri/kedro-boot.git
```


## Check the install

``kedro-boot`` is a kedro plugin and will automatically be registered if you are in a kedro project, hence its commands will be automatically available. You can check that it is properly discovered by kedro by launching ``kedro info`` command. You should see a message displaying the kedro boot version. 

