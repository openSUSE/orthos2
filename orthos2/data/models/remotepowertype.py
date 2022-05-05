import logging


class RemotePowerType:
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
        logging.info("Initialiced RemotePowerType for %s", self.fence)
        self.use_hostname_as_port = options.get('use_hostname_as_port', False)
        self.options = options.get('options', None)
