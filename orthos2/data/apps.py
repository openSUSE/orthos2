from django.apps import AppConfig


class DataConfig(AppConfig):
    name = 'data'

    def ready(self):
        import data.signals

        # prepare types for fast and developer-friendly handling
        self.get_model('Architecture').Type.prep()
        self.get_model('System').Type.prep()
