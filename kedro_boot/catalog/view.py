from typing import Optional


class CatalogView:
    """a view of the catalog that map an app pipeline's view"""

    def __init__(
        self,
        name: Optional[str] = None,
        inputs: Optional[dict] = None,
        outputs: Optional[dict] = None,
        parameters: Optional[dict] = None,
        artifacts: Optional[dict] = None,
        templates: Optional[dict] = None,
        unmanaged: Optional[dict] = None,
    ) -> None:
        """Init ``CatalogView`` with a name and a categorisation of the datasets that are exposed to the app.

        Args:
            name (str): A view name. It should be unique per AppCatalog views.
            inputs dict: Inputs datasets that will be injected by the app data at iteration time.
            outputs dict: Outputs dataset that hold the iteration run results.
            parameters dict: Parameters that will be injected by the app data at iteration time.
            artifacts dict: Artifacts datasets that will be materialized (loaded as MemoryDataset) at startup time.
            templates dict: Templates datasets that contains jinja expressions in this form [[ expressions ]].
            unmanaged dict: Datasets that will not undergo any operation and keeped as is
        """
        self.name = name

        self.inputs = inputs or {}
        self.outputs = outputs or {}
        self.artifacts = artifacts or {}
        self.templates = templates or {}
        self.parameters = parameters or {}
        self.unmanaged = unmanaged or {}
