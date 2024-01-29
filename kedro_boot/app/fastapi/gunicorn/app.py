import sys

from gunicorn.app.wsgiapp import WSGIApplication


class GunicornApp(WSGIApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        configs = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in configs.items():
            self.cfg.set(key.lower(), value)

        from . import config

        cfg = vars(config)

        for k, v in cfg.items():
            # Ignore unknown names
            if k not in self.cfg.settings:
                continue
            try:
                self.cfg.set(k.lower(), v)
            except Exception:
                print("Invalid value for %s: %s \n" % (k, v), file=sys.stderr)
                sys.stderr.flush()
                raise

    def load(self):
        return self.application
