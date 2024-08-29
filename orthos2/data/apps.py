from django.apps import AppConfig


class DataConfig(AppConfig):
    name = "orthos2.data"

    def ready(self) -> None:
        # prepare types for fast and developer-friendly handling
        self.get_model("Architecture").Type.prep()  # type: ignore
        self.get_model("System").Type.prep()  # type: ignore
