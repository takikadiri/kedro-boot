# Changelog

## [Unreleased]

## [0.2.3] - 2024-11-15

### Added

- ✨ enable running kedro boot commands from packaged projects

## [0.2.2] - 2024-04-21

### Added

-   :sparkles: Kedro Boot commands now works inside a subdirectory

### Fixed

-   :bug: Fix Kedro Boot commands by supporting kedro 0.19.4 breaking changes of the `_is_project` utility 

## [0.2.1] - 2024-02-13

### Added

-   :sparkles: Include ["fastapi*/] dynamically in the config loader config patterns

### Fixed

-   :bug: Catch fastapi extra dependecies errors, and make their imports lazy.

## [0.2.0] - 2024-02-12

### Added

-   :sparkles: Introduce Kedro FastAPI Server: A framework for building production-ready REST APIs using Kedro, FastAPI and Gunicorn ([#18](https://github.com/takikadiri/kedro-boot/pull/18))
-   :sparkles: Support dataset factories ([#5](https://github.com/takikadiri/kedro-boot/pull/5))
-   :sparkles: Allow declaring apps through project settings and CLIs ([#16](https://github.com/takikadiri/kedro-boot/pull/16))
-   :sparkles: Adding `boot_project` and `boot_package` allowing standalone apps to boot a session ([#17](https://github.com/takikadiri/kedro-boot/pull/17))

### Changed

-   :boom: :arrow_up: Support kedro 0.19.x and drop support for 0.18.x ([#15](https://github.com/takikadiri/kedro-boot/pull/15))
-   :boom: Drop AppPipeline in favor of pipeline namespaces ([#14](https://github.com/takikadiri/kedro-boot/pull/14))
-   :boom: Adopt OmegaConfigLoader and replace Jinja `template_params` with `itertime_params` resolver ([#13](https://github.com/takikadiri/kedro-boot/pull/13))

## [0.1.0] - 2023-10-29

### Added

-   :tada: Add `KedroBootSession` for managing interaction between external applications and kedro projects
-   :tada: Add `kedro boot` cli for running external applications inside kedro projects
-   :tada: Add `boot_session` utility that create a `KedroBootSession` inside a external standalone App 
-   :tada: Add `AppPipeline` and its `app_pipeline` factory for declaring and registring application views on top of kedro pipelines

[Unreleased]: https://github.com/takikadiri/kedro-boot/compare/0.2.3...HEAD

[0.2.3]: https://github.com/takikadiri/kedro-boot/compare/0.2.2...0.2.3

[0.2.2]: https://github.com/takikadiri/kedro-boot/compare/0.2.1...0.2.2

[0.2.1]: https://github.com/takikadiri/kedro-boot/compare/0.2.0...0.2.1

[0.2.0]: https://github.com/takikadiri/kedro-boot/compare/0.1.0...0.2.0

[0.1.0]: https://github.com/takikadiri/kedro-boot/compare/4126de2a96b11026644853cf49fdb4619269f18b...0.1.0
