"""
THIS IS MOSTLY AN EXACT REPLICATION OF THE EXAMPLE CODE FOUND IN
THE PIKA GITHUB REPOSITORY (https://github.com/pika/pika).
I HAVE PACKAGED THE CODE PURELY TO MAKE IT PIP INSTALLABLE AND
CANNOT ACCEPT ANY ACCOLADE (OR BLAME) FOR THE CODE.

View the original source here:

    https://github.com/pika/pika/tree/574ad47de9da4dba2cda977aa52cd10c5c8acb91/examples

"""

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from .async_publisher import AsyncPublisher  # noqa
from .async_consumer import AsyncConsumer  # noqa
from .connection import EnvConnectionParameters  # noqa
from .simple_async_consumer import SimpleAsyncConsumer  # noqa
from .simple_async_publisher import SimpleAsyncPublisher  # noqa
