import logging
from kedro_boot.app import AbstractKedroBootApp
from kedro_boot.framework.session import KedroBootSession

LOGGER = logging.getLogger(__name__)


class MonteCarloApp(AbstractKedroBootApp):
    def _run(self, kedro_boot_session: KedroBootSession):
        # leveraging config_loader to manage app's configs
        monte_carlo_params = kedro_boot_session.config_loader["monte_carlo"]
        num_samples = monte_carlo_params["num_samples"]
        radius = monte_carlo_params["radius"]

        distances = []
        for _ in range(num_samples):
            distance = kedro_boot_session.run(
                namespace="simulate_distance", parameters={"radius": radius}
            )
            distances.append(distance)

        estimated_pi = kedro_boot_session.run(
            namespace="estimate_pi",
            inputs={"distances": distances},
            parameters={"num_samples": num_samples, "radius": radius},
        )

        print(f"Estimated Pi : {estimated_pi}")

        return estimated_pi
