import sys

from orthos2.data.models import ServerConfig
from django.core.management.base import BaseCommand

try:
    from ptyprocess import PtyProcessUnicode
    from terminado import TermSocket, UniqueTermManager
    from terminado.management import MaxTerminalsReached, PtyWithClients
    from terminado.websocket import _cast_unicode
except ImportError:
    print("'terminado' module needed! Run 'pip install terminado'...")
    sys.exit(1)

try:
    import tornado.web
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
except ImportError:
    print("'tornado' module needed! Run 'pip install tornado'...")
    sys.exit(1)


class TermSocketHandler(TermSocket):

    def open(self, url_component=None, hostname=None):
        """Websocket connection opened.

        Call our terminal manager to get a terminal, and connect to it as a
        client.
        """
        self._logger.info("TermSocket.open: %s", url_component)

        url_component = _cast_unicode(url_component)
        self.term_name = url_component or 'tty'
        self.terminal = self.term_manager.get_terminal(url_component, hostname=hostname)

        for s in self.terminal.read_buffer:
            self.on_pty_read(s)
        self.terminal.clients.append(self)

        self.send_json_message(["setup", {}])
        self._logger.info("TermSocket.open: Opened %s", self.term_name)

    def check_origin(self, origin):
        """Disable origin check due to different websocket server."""
        return True


class SerialConsoleTermManager(UniqueTermManager):

    def new_terminal(self, **kwargs):
        """
        Make a new terminal, return a :class: `PtyWithClients` instance.

        Add `hostname` to shell commando.
        """
        hostname = kwargs.pop('hostname', None)

        options = self.term_settings.copy()
        options['shell_command'] = self.shell_command + [hostname]
        options.update(kwargs)
        argv = options['shell_command']
        env = self.make_term_env(**options)
        pty = PtyProcessUnicode.spawn(argv, env=env, cwd=options.get('cwd', None))
        return PtyWithClients(pty)

    def get_terminal(self, url_component=None, hostname=None):
        """Call `new_terminal()` with `hostname` argument."""
        if self.max_terminals and len(self.ptys_by_fd) >= self.max_terminals:
            raise MaxTerminalsReached(self.max_terminals)

        term = self.new_terminal(hostname=hostname)
        self.start_reading(term)
        return term


class Command(BaseCommand):
    help = 'Starts websocket daemon'

    OPTIONS = (
        (('--start', ), {
            'action': 'store_true',
            'help': "Start websocket daemon."
        }),
        (('--wss', ), {
            'action': 'store_true',
            'help': "Use wss websocket (default: ws, needs --crt and --key parameters)."
        }),
        (('--crt', ), {
            'nargs': 1,
            'type': str,
            'help': "Servers certificate file path."
        }),
        (('--key', ), {
            'nargs': 1,
            'type': str,
            'help': "Servers private key file path."
        }),
    )

    def add_arguments(self, parser):
        for (args, kwargs) in self.OPTIONS:
            parser.add_argument(*args, **kwargs)

    def handle(self, *args, **options):
        ssl_ctx = None

        if options['start']:

            if options['wss']:
                import ssl

                if options['crt'] is None or options['key'] is None:
                    self.stdout.write("Websocket wss: --crt and --key parameters needed!")
                    sys.exit(1)

                crt = options['crt'][0]
                key = options['key'][0]

                ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_ctx.load_cert_chain(crt, key)

            port = int(ServerConfig.objects.by_key('websocket.cscreen.port'))
            shell_command = ServerConfig.objects.by_key('websocket.cscreen.command')

            self.stdout.write("Start websocket daemon on port {}...".format(port))

            term_manager = SerialConsoleTermManager(
                shell_command=shell_command.split(' ')
            )
            handlers = [
                (
                    r"/machine/(?P<hostname>[a-zA-Z0-9\-]+)/console",
                    TermSocketHandler,
                    {'term_manager': term_manager}
                ),
            ]
            try:
                app = tornado.web.Application(handlers)

                if options['wss']:
                    server = HTTPServer(app, ssl_options=ssl_ctx)
                else:
                    server = HTTPServer(app)

                server.listen(port)
                IOLoop.current().start()
            except KeyboardInterrupt:
                self.stdout.write("Stop.".format(port))
