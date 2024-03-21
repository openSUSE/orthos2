#!/usr/bin/python3

import signal
import socketserver
import threading
from typing import Optional

from ipmisim.ipmisim import IpmiServer

done_event = threading.Event()
server: Optional[socketserver.UDPServer] = None


def shutdownHandler(msg, evt):
    global server

    if server is not None:
        print("shutdown handler called. shutting down on thread id:%x" % (id(threading.current_thread())))
        server.shutdown()
        server.server_close()
        print("shutdown complete")
    else:
        print("No server to shutdown")
    evt.set()
    return


def terminate(signal, frame):
    print("terminate handle on thread id:%x" % (id(threading.current_thread())))
    t = threading.Thread(target=shutdownHandler, args=('SIGTERM received', done_event))
    t.start()


def main(address: str = "0.0.0.0", port: int = 9001):
    global server
    print("main thread id:%x" % (id(threading.current_thread())))
    signal.signal(signal.SIGTERM, terminate)
    server = socketserver.UDPServer((address, port), IpmiServer)
    server.serve_forever()
    done_event.wait()


if __name__ == "__main__":
    main()
