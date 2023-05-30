from RDT_LIBRARY import RDTUtility

# Setup server
server_addr = ('140.128.101.141', 7000)
client_addr = ('172.23.8.60', 7000)
server = RDTUtility(server_addr, client_addr)

# run server
server.start_server()
