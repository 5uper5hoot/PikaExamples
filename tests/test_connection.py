import os
import ssl

import pika
import pytest

from pikaexamples import EnvConnectionParameters


def test_default_params_match_parent_class():
    ecp = EnvConnectionParameters()
    cp = pika.ConnectionParameters()
    for attr in pika.connection.Parameters.__slots__:
        assert getattr(ecp, attr) == getattr(cp, attr)


@pytest.mark.parametrize('attr,setval,res', [
    ('backpressure_detection', "0", False),
    ('blocked_connection_timeout', "1.0", 1.0),
    ('channel_max', '1', 1),
    ('connection_attempts', '1', 1),
    ('frame_max', '10000', 10000),
    ('heartbeat', '1', 1),
    ('host', 'hoststr', 'hoststr'),
    ('locale', 'alocale', 'alocale'),
    ('retry_delay', '1.5', 1.5),
    ('socket_timeout', '1.5', 1.5),
    ('ssl', '1', True),
    ('virtual_host', '/', '/')
])
def test_scalar_attrs(attr, setval, res, monkeypatch):
    env_key = f'PIKA_{attr.upper()}'
    monkeypatch.setenv(env_key, setval)
    cp = EnvConnectionParameters()
    assert getattr(cp, attr) == res


@pytest.mark.parametrize('sslval,res', [
    ('1', pika.connection.Parameters.DEFAULT_SSL_PORT),
    ('0', pika.connection.Parameters.DEFAULT_PORT)
])
def test_port_defaults_respect_ssl_boolean(sslval, res, monkeypatch):
    monkeypatch.setenv('PIKA_SSL', sslval)
    assert EnvConnectionParameters().port == res


@pytest.mark.parametrize('sslval', ['1', '0'])
def test_port_respects_set_value_and_disregards_defaults(sslval, monkeypatch):
    monkeypatch.setenv('PIKA_SSL', sslval)
    monkeypatch.setenv('PIKA_PORT', '10000')
    assert EnvConnectionParameters().port == 10000


@pytest.mark.parametrize('attr', [
    'product',
    'platform',
    'information',
    'version',
    'capabilities_basic.nack',
    'capabilities_connection.blocked',
    'capabilities_consumer_cancel_notify',
    'capabilities_publisher_confirms'
])
def test_any_client_properties_env_var_sets_attr_val(attr, monkeypatch):
    monkeypatch.setenv(f'PIKA_CLIENT_PROPERTIES_{attr.upper()}', '1')
    cp = EnvConnectionParameters()
    assert isinstance(cp.client_properties, dict)
    if attr.startswith('capabilities_'):
        nested_attr = attr.split('_', 1)[1]
        assert 'capabilities' in cp.client_properties
        assert nested_attr in cp.client_properties['capabilities']
    else:
        assert attr in cp.client_properties


def test_credentials(monkeypatch):
    monkeypatch.setenv('PIKA_CREDENTIALS_USERNAME', 'user')
    monkeypatch.setenv('PIKA_CREDENTIALS_PASSWORD', 'pass')
    monkeypatch.setenv('PIKA_CREDENTIALS_ERASE_ON_CONNECT', '1')
    cp = EnvConnectionParameters()
    assert isinstance(cp.credentials, pika.PlainCredentials)
    assert cp.credentials.username == 'user'
    assert cp.credentials.password == 'pass'
    assert cp.credentials.erase_on_connect is True


@pytest.mark.parametrize('attr,envval,res', [
    ('keyfile', '/path/to/clientkey.pem', '/path/to/clientkey.pem'),
    ('key_password', 'thisisthepassword', 'thisisthepassword'),
    ('certfile', '/path/to/clientcert.pem', '/path/to/clientcert.pem'),
    ('server_side', '0', False),
    ('verify_mode', 'CERT_REQUIRED', ssl.CERT_REQUIRED),
    ('ssl_version', 'PROTOCOL_TLS', ssl.PROTOCOL_TLS),
    ('cafile', '/a/path/', '/a/path/'),
    ('capath', '/a/path/', '/a/path/'),
    ('cadata', 'something', 'something'),
    ('do_handshake_on_connect', '1', True),
    ('suppress_ragged_eofs', '0', False),
    ('ciphers', 'a string of ciphers', 'a string of ciphers'),
    ('server_hostname', 'hostname', 'hostname')
])
def test_ssl_options(attr, envval, res, monkeypatch):
    monkeypatch.setenv(f'PIKA_SSL_OPTIONS_{attr.upper()}', envval)
    cp = EnvConnectionParameters()
    assert isinstance(cp.ssl_options, pika.SSLOptions)
    assert getattr(cp.ssl_options, attr) == res


@pytest.mark.parametrize('attr,envval,res', [
    ('TCP_KEEPIDLE', '1', 1),
    ('TCP_KEEPINTVL', '1', 1),
    ('TCP_KEEPCNT', '1', 1),
    ('TCP_USER_TIMEOUT', '1', 1)
])
def test_tcp_options(attr, envval, res, monkeypatch):
    monkeypatch.setenv(f'PIKA_TCP_OPTIONS_{attr.upper()}', envval)
    cp = EnvConnectionParameters()
    assert isinstance(cp.tcp_options, dict)
    assert cp.tcp_options[attr] == res


def test_passing_EnvConnectionParameters_instance_to_connection():
    cp = EnvConnectionParameters()
    conn = pika.SelectConnection(parameters=cp)
    assert isinstance(conn, pika.SelectConnection)
