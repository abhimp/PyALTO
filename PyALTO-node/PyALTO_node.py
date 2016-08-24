import logging
import asyncio
import os

# Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("PyALTO NODE is starting")

# Start event loop
loop = asyncio.get_event_loop()
loop.set_debug(True)

# Create a TCP connection to the ALTO server


