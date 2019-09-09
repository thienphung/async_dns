import socket
import random
from . import types

__all__ = [
    'Address',
    'NameServers',
    'InvalidHost',
]

class InvalidHost(Exception):
    pass

class Address:
    def __init__(self, hostname, port=0, allow_domain=False):
        self.parse(hostname, port, allow_domain)

    def __eq__(self, other):
        return self.host == other.host and self.port == other.port

    def __repr__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.to_addr())

    def parse(self, hostname, port=0, allow_domain=False):
        if isinstance(hostname, tuple):
            self.parse_tuple(hostname, allow_domain)
        elif isinstance(hostname, Address):
            self.parse_address(hostname)
        elif hostname.count(':') > 1:
            self.parse_ipv6(hostname, port)
        else:
            self.parse_ipv4_or_domain(hostname, port, allow_domain)

    def parse_tuple(self, addr, allow_domain=False):
        host, port = addr
        self.parse(host, port, allow_domain)

    def parse_address(self, addr):
        self.host, self.port, self.ip_type = addr.host, addr.port, addr.ip_type

    def parse_ipv4_or_domain(self, hostname, port=None, allow_domain=False):
        try:
            self.parse_ipv4(hostname, port)
        except InvalidHost as e:
            if not allow_domain:
                raise e
            host, _, port_s = hostname.partition(':')
            if _:
                port = int(port_s)
            self.host, self.port, self.ip_type = host, port, None

    def parse_ipv4(self, hostname, port=None):
        host, _, port_s = hostname.partition(':')
        if _:
            port = int(port_s)
        try:
            socket.inet_pton(socket.AF_INET, host)
        except OSError:
            raise InvalidHost(host)
        self.host, self.port, self.ip_type = host, port, types.A

    def parse_ipv6(self, hostname, port=None):
        if hostname.startswith('['):
            i = hostname.index(']')
            host = hostname[1 : i]
            port_s = hostname[i + 1 :]
            if port_s:
                if not port_s.startswith(':'):
                    raise InvalidHost(hostname)
                port = int(port_s[1:])
        else:
            host = hostname
        try:
            socket.inet_pton(socket.AF_INET6, host)
        except OSError:
            raise InvalidHost(host)
        self.host, self.port, self.ip_type = host, port, types.AAAA

    def to_str(self, default_port = 0):
        if default_port is None or self.port == default_port:
            return self.host
        if self.ip_type is types.A:
            return '%s:%d' % self.to_addr()
        elif self.ip_type is types.AAAA:
            return '[%s]:%d' % self.to_addr()

    def to_addr(self):
        return self.host, self.port

class NameServers:
    def __init__(self, nameservers=None, default_port=53):
        self.default_port = default_port
        self.data = set()
        self._tuple = ()
        if nameservers:
            for nameserver in nameservers:
                self.add(nameserver)

    def __bool__(self):
        return len(self.data) > 0

    def __iter__(self):
        return iter(self._tuple)

    def __repr__(self):
        return '<NameServers [%s]>' % ','.join(map(str, self.data))

    def get(self):
        return random.choice(self._tuple)

    def add(self, addr):
        self.data.add(Address(addr, self.default_port))
        self._tuple = tuple(self.data)

    def fail(self, addr):
        self.data.discard(addr)
        self._tuple = tuple(self.data)
