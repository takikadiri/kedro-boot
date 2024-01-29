from kedro.framework.hooks import hook_impl
from kedro.framework.context import KedroContext


class KedroBootHook:
    @hook_impl
    def after_context_created(
        self,
        context: KedroContext,
    ) -> None:
        """Hooks to be invoked after a `KedroContext` is created. This is the earliest
        hook triggered within a Kedro run. The `KedroContext` stores useful information
        such as `credentials`, `config_loader` and `env`.
        Args:
            context: The context that was created.
        """

        context.config_loader._register_new_resolvers(
            {
                "itertime_params": lambda variable,
                default_value=None: f"${{oc.select:{variable},{default_value}}}",
            }
        )


kedro_boot_hook = KedroBootHook()
