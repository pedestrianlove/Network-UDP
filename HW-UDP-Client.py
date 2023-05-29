
"""# 1. 設定環境"""

# Import dependencies for TCP/UDP
import socket
import time
HOST = '140.128.101.141'
PORT = 7000

# Setup Client IP and port
server_addr = (HOST, PORT)

# Setup renderImage() function
import cv2
from matplotlib import pyplot as plt
def renderImage(imagePath):
  imageObject = cv2.imread(imagePath, -1)
  plt.imshow(imageObject)
  plt.axis("off")
  plt.show()

import pickle

# Setup packet forging function
def packet(seq, binary_data):
  # combine the sequence number and payload data into a tuple
  packet = (seq, binary_data)
  # serialize the packet to bytes using pickle
  packet_bytes = pickle.dumps(packet)

  return packet_bytes

# Setup packet decode function
def dec_packet(binary_packet):
  # deserialize the packet from bytes using pickle
  packet = pickle.loads(binary_packet)
  seq, binary_data = packet
  return seq, binary_data
  
# Setup function for udp listening
def UDP_LISTEN(SOCKET_ADDR):
  # Setup socket for recieving ACK packet
  conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  # Requesting client port to listen on
  conn.bind(SOCKET_ADDR)
  return conn

# Setup function for udp sending
def UDP_PREPARE():
  # Setup socket for recieving ACK packet
  conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  return conn

"""## c. 設定客戶端"""

def client():
  # Setup target socket
  s = UDP_PREPARE()
  s.connect(server_addr)
  #client_addr = s.getsockname()
  client_addr = ('172.23.8.60', 6000)
  # Setup socket for recieving ACK packet
  r = UDP_LISTEN(client_addr)

  # Client starting
  print("Client: Client starting at...", str(client_addr))

  # Sending file
  print("Client: Sending the following image:")
  renderImage("test.jpg")
  counter = 0
  testFile = open('test.jpg', 'rb')
  buf = testFile.read(1024)
  while (buf):
    print("Client: Sending packet with SEQ...", counter)
    s.sendto(packet(counter, buf), server_addr)
    seq, data_binary = dec_packet(r.recvfrom(1024 * 2)[0])
    while (seq != counter or data_binary.decode() != "ACK"):
      print("Client: Not receiving packet with ACK...", counter, ", resending...")
      s.sendto(packet(counter, buf), server_addr)
      seq, data_binary = dec_packet(r.recvfrom(1024 * 2)[0])
    print ("Client: Received packet with ACK...", counter)
    counter += 1
    buf = testFile.read(1024)
  
  # Stopping client
  print("File sent.")
  s.sendto(packet(counter, "stop".encode()), server_addr)
  seq, data_binary = dec_packet(r.recvfrom(1024 * 2)[0])
  while(seq != counter or data_binary.decode() != "ACK"):
    print("Client: Not receiving packet with ACK...", counter, ", resending...")
    s.sendto(packet(counter, buf), server_addr)
    seq, data_binary = dec_packet(r.recvfrom(1024 * 2)[0])

  s.close()
  print("Client stopped.")

"""# 2. 執行"""

client()

