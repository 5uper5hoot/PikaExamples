# -*- coding: utf-8 -*-

import os
import ssl

import pika


# alternate bool constructor that first converts arg to int.
def bool_(s):
    return bool(int(s))


class EnvConnectionParameters(pika.ConnectionParameters):
    """ Values for all connection parameters are established using
    environment variables. If there is not an environment variable
    set for a given attribute, it will fall back to the pika
    default as established in `connection.Parameters` class.

    Format of scalar attribute environment variable is:

    `PIKA_<NAME_OF_ATTR_IN_CAPS>`

    For example, to set host: `export PIKA_HOST = '123.456.789.10'`.

    Scalar attribute names (coerced type, default) are:
        - backpressure_detection (bool, False)
        - blocked_connection_timeout (float, None)
        - channel_max (int, 65535)
        - connection_attempts (int, 1)
        - frame_max (int, 131072)
        - heartbeat* (int, None)
        - host (str, 'localhost')
        - locale (str, 'en_US')
        - retry_delay (float, 2.0)
        - socket_timeout (float, 10.0)
        - ssl (bool, False)
        - port (int, 5672 or 5671 depending on ssl)
        - virtual_host (str, '/')

    Connection parameters that require a collection of values or a
    specific type need to be of the format:

    `PIKA_<ATTR_NAME_IN_CAPS>_<VALUE_NAME_IN_CAPS>`

    Parameter names (default) that require a mapping of values include:
        - client_properties (None)
        - credentials
            (pika_credentials.PlainCredentials('guest', 'guest'))
        - ssl_options (None)
        - tcp_options (None)

    Specific details of the handling of each attribute that requires a
    mapping follows:

    client_properties
    -----------------
    Format env vars as:

        `PIKA_CLIENT_PROPERTIES_<VALUE_NAME_IN_CAPS>`

    Value names that can be set here are 'product', 'platform',
    'information', 'version'. client_properties also accepts a mapping
    called 'capabilities' which can be controlled by setting env vars
    with the format:

        `PIKA_CLIENT_PROPERTIES_CAPABILITIES_<KEY_NAME_IN_CAPS>

    The capabilities key names that are searched for are,
    'authentication_failure_close', 'basic.nack', 'connection.blocked',
    'consumer_cancel_notify', and 'publisher_confirms. All accepting
    boolean values (set env var as 1 or 0).

    credentials
    -----------
    Format env vars as:

        `PIKA_CREDENTIALS_<ATTR_NAME_IN_CAPS>`

    If credentials are passed in via env vars, then the credentials
    object is taken to be a credentials.PlainCredentials object and
    the attrib names that are searched for are, 'username' (str),
    'password' (str), and 'erase_on_connect' (bool, set as 1, or 0).

    ssl_options
    -----------
    Format env vars as:

        `PIKA_SSL_OPTIONS_<ATTR_NAME_IN_CAPS>`

    Where attr name is one of:
        - keyfile (str)
        - key_password (str)
        - certfile (str)
        - server_side (bool)
        - verify_mode* (str)
        - ssl_version* (str)
        - cafile (str)
        - capath (str)
        - cadata (str)
        - do_handshake_on_connect (bool)
        - suppress_ragged_eofs (bool)
        - ciphers (str)
        - server_hostname (str)

    verify_mode must be one of 'CERT_NONE', 'CERT_OPTIONAL' or
    'CERT_REQUIRED', if set. ssl_version must be the name one of the
    protocol instances found in the ssl module, e.g. 'PROTOCOL_TLS'.
    The value will be used to get the object of the same name from the
    ssl module.

    tcp_options
    -----------
    Format env vars as:

        `PIKA_TCP_OPTIONS_<KEY_NAME_IN_CAPS>`

    Key names sought are, 'TCP_KEEPIDLE', 'TCP_KEEPINTVL',
    'TCP_KEEPCNT', 'TCP_USER_TIMEOUT'.
    """

    # Protect against accidental assignment of an invalid attribute
    __slots__ = ()

    def __init__(self, heartbeat_callable=None):

        def _env_or_default(attr, cast):
            """ Return environment variable or existing value."""
            try:
                return cast(os.environ[f'PIKA_{attr.upper()}'])
            except KeyError:
                return getattr(self, attr)

        # pre-populates all attrs with default values
        super(pika.ConnectionParameters, self).__init__()

        for attr, cast in [
            ('backpressure_detection', bool_),
            ('blocked_connection_timeout', float),
            ('channel_max', int),
            ('connection_attempts', int),
            ('frame_max', int),
            ('heartbeat', int),
            ('host', str),
            ('locale', str),
            ('retry_delay', float),
            ('socket_timeout', float),
            ('ssl', bool_),
            ('virtual_host', str)
        ]:
            setattr(self, attr, _env_or_default(attr, cast))

        if os.getenv('PIKA_PORT', None):
            self.port = os.getenv('PIKA_PORT')
        else:
            if self.ssl:
                self.port = \
                    super(pika.ConnectionParameters, self).DEFAULT_SSL_PORT
            else:
                self.port = \
                    super(pika.ConnectionParameters, self).DEFAULT_PORT

        self.client_properties = self._get_client_properties()

        self.credentials = self._get_credentials()

        self.ssl_options = self._get_ssl_options()

        self.tcp_options = self._get_tcp_options()

    @staticmethod
    def _get_related_env_vars(prefix, keys, casts=None):

        if not casts:
            casts = [str for k in keys]

        d = {}
        for k, c in zip(keys, casts):
            try:
                d[k] = c(os.environ[f'{prefix}_{k.upper()}'])
            except KeyError:
                pass
        return d

    def _get_client_properties(self):
        properties_prefix = 'PIKA_CLIENT_PROPERTIES'
        properties_keys = ['product',
                           'platform',
                           'information',
                           'version']
        properties = self._get_related_env_vars(
            properties_prefix, properties_keys)

        capabilities_prefix = 'PIKA_CLIENT_PROPERTIES_CAPABILITIES'
        capabilities_keys = ['authentication_failure_close',
                             'basic.nack',
                             'connection.blocked',
                             'consumer_cancel_notify',
                             'publisher_confirms']
        capabilities_casts = (bool_ for s in capabilities_keys)
        capabilities = self._get_related_env_vars(
            capabilities_prefix, capabilities_keys, capabilities_casts)

        if capabilities:
            properties['capabilities'] = capabilities

        return properties or getattr(self, 'client_properties')

    def _get_credentials(self):
        prefix = 'PIKA_CREDENTIALS'
        keys = ['username',
                'password',
                'erase_on_connect']
        casts = [str, str, lambda s: bool(int(s))]
        credentials = self._get_related_env_vars(prefix, keys, casts)

        if credentials:
            return pika.PlainCredentials(**credentials)
        else:
            return getattr(self, 'credentials')

    def _get_ssl_options(self):
        prefix = 'PIKA_SSL_OPTIONS'
        atrs = {'keyfile': str,
                'key_password': str,
                'certfile': str,
                'server_side': bool_,
                'verify_mode': str,
                'ssl_version': str,
                'cafile': str,
                'capath': str,
                'cadata': str,
                'do_handshake_on_connect': bool_,
                'suppress_ragged_eofs': bool_,
                'ciphers': str,
                'server_hostname': str}

        ssl_options = self._get_related_env_vars(
            prefix, atrs.keys(), atrs.values())

        if ssl_options:
            if 'verify_mode' in ssl_options:
                ssl_options['verify_mode'] = getattr(
                    ssl, ssl_options['verify_mode'])

            if 'ssl_version' in ssl_options:
                ssl_options['ssl_version'] = getattr(
                    ssl, ssl_options['ssl_version'])

            return pika.SSLOptions(**ssl_options)
        else:
            return getattr(self, 'ssl_options')

    def _get_tcp_options(self):
        prefix = 'PIKA_TCP_OPTIONS'
        keys = ['TCP_KEEPIDLE',
                'TCP_KEEPINTVL',
                'TCP_KEEPCNT',
                'TCP_USER_TIMEOUT']
        casts = [int] * 4

        tcp_options = self._get_related_env_vars(prefix, keys, casts)

        return tcp_options or getattr(self, 'tcp_options')
