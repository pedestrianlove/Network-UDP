from RDT_LIBRARY import RDTUtility

# Setup server
server_addr = ('140.128.101.141', 8002)
client_addr = ('172.23.8.60', 8001)
server = RDTUtility(server_addr, client_addr)

# run server
server.start_server()
