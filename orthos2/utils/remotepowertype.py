import logging
from django.conf import settings


def get_remote_power_type_choices(device: str = ""):
    if device:
        remotepower_type_choices = [
            (fence['fence'], fence['fence']) for fence in settings.REMOTEPOWER_TYPES
            if fence['device'].lower() == device.lower()
        ]
    else:
        remotepower_type_choices = [(fence['fence'], fence['fence'])
                                    for fence in settings.REMOTEPOWER_TYPES]
    return remotepower_type_choices


class RemotePowerType:
    @classmethod
    def from_fence(cls, fence: str):
        if not fence:
            raise ValueError("Empty Argument")
        obj = [cls(x) for x in settings.REMOTEPOWER_TYPES if x['fence'] == fence][0]
        return obj

    def __init__(self, options: dict):
        self.fence = options.get('fence')
        logging.debug("Initialiced RemotePowerType for %s", self.fence)
        self.device = options.get('device')
        self.username = options.get('username')
        if 'password' in options:
            self.password = options['password']
            self.use_password = True
        else:
            self.use_password = False
        if 'identity_file' in options:
            self.identity_file = options['identity_file']
            self.use_identity_file = True
        else:
            self.use_identity_file = False
        if 'port' in options:
            self.use_port = options['port']
        else:
            self.use_port = False
