import json
import signal
import logging
import sys
import inspect
import os

file_path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, os.path.join(file_path, './'))
from shadowsocks import shell, daemon, eventloop, tcprelay, udprelay, asyncdns

with open("/home/tyrantlucifer/.ssr-command-client/config.json", 'r') as file:
    content = file.read()

config = json.loads(content)

config['daemon'] = sys.argv[1]
config['pid-file'] = '/home/tyrantlucifer/ssr-command-client/shadowsocksr.pid'
config['log-file'] = '/home/tyrantlucifer/ssr-command-client/shadowsocksr.log'
config['port_password'] = None
config['additional_ports'] = {}
config['additional_ports_only'] = False
config['udp_timeout'] = 120
config['udp_cache'] = 64
config['fast_open'] = False
config['verbose'] = False
config['connect_verbose_info'] = 0

if not config.get('dns_ipv6', False):
    asyncdns.IPV6_CONNECTION_SUPPORT = False

daemon.daemon_exec(config)

try:
    dns_resolver = asyncdns.DNSResolver()
    tcp_server = tcprelay.TCPRelay(config, dns_resolver, True)
    udp_server = udprelay.UDPRelay(config, dns_resolver, True)
    loop = eventloop.EventLoop()
    dns_resolver.add_to_loop(loop)
    tcp_server.add_to_loop(loop)
    udp_server.add_to_loop(loop)

    def handler(signum, _):
        logging.warn('received SIGQUIT, doing graceful shutting down..')
        tcp_server.close(next_tick=True)
        udp_server.close(next_tick=True)

    signal.signal(getattr(signal, 'SIGQUIT', signal.SIGTERM), handler)

    def int_handler(signum, _):
        sys.exit(1)

    signal.signal(signal.SIGINT, int_handler)
    daemon.set_user(config.get('user', None))
    loop.run()
except Exception as e:
    shell.print_exception(e)
    sys.exit(1)
