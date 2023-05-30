from RDT_LIBRARY import RDTUtility

# Setup Client
server_addr = ('140.128.101.141', 8002)
client_addr = ('172.23.8.60', 8001)
client = RDTUtility(client_addr, server_addr)

# run client
client.start_client()
