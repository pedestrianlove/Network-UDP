from RDT_LIBRARY import RDTUtility
import asyncio

# Setup Client
server_addr = ('140.128.101.141', 7000)
client_addr = ('172.23.8.60', 7000)
client = RDTUtility(server_addr, client_addr)

# run client
asyncio.run(client.start_client())
