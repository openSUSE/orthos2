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
        objs = [cls(x) for x in settings.REMOTEPOWER_TYPES if x['fence'] == fence]
        if not objs:
            logging.error("no fence agent named %s found", fence)
            return None
        return objs[0]

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
        self.use_port = options.get('port', False)
        self.use_hostname_as_port = options.get('use_hostname_as_port', False)
        self.use_options = options.get('options', False)
