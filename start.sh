#!/usr/bin/env python3
"""Inicia o servidor Flask como daemon (duplo fork)."""
import os
import sys
import atexit
import signal

def daemonize():
    pid = os.fork()
    if pid > 0:
        return pid  # retorna o PID do filho para o pai
    os.setsid()
    pid = os.fork()
    if pid > 0:
        os._exit(0)
    os.chdir('/workspaces/Intelicamp')
    sys.stdout.flush()
    sys.stderr.flush()
    si = open('/dev/null', 'r')
    so = open('/tmp/flask-server.log', 'a+')
    se = open('/tmp/flask-server.log', 'a+')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    return None

if __name__ == '__main__':
    import app as webapp
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    pid = daemonize()
    if pid is not None:
        print(pid)
        sys.exit(0)
    webapp.app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
