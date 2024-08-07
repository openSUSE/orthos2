from django.apps import AppConfig


class DataConfig(AppConfig):
    name = "orthos2.data"

    def ready(self):
        # prepare types for fast and developer-friendly handling
        self.get_model("Architecture").Type.prep()
        self.get_model("System").Type.prep()
