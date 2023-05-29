#!/usr/bin/env python
# coding: utf-8

# In[4]:


# Import dependencies for TCP/UDP
import socket
HOST = '140.128.101.141'
PORT = 7000
server_addr = (HOST, PORT)
client_addr = ('172.23.8.60', 6000)

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


# In[5]:


def server():
  # Start listening on server_addr
  print("Server: Server starting...")
  s = UDP_LISTEN(server_addr)
  print('Server: Listening at: ', str(server_addr))
  print('Server: Waiting for data...')
  
    
  # Receiving file
  outputFile = open('received.jpg', 'wb')
  counter = 0
  seq, buf = dec_packet(s.recvfrom(1024*2)[0])
  print('Server: recvfrom: ' + str(client_addr), counter)
  while (buf):
    if (seq != counter):
        print("Server: Receiving wrong packet, resending ACK: ", counter-1, " and waiting for new one...")
        s.sendto(packet(counter-1, "ACK".encode()), client_addr)
        seq, buf = dec_packet(s.recvfrom(1024*2)[0])
        continue
    try:
      if (buf.decode() == "stop"):
        break
    except:
      print("Server: Not getting stopped, keep receiving...")
    print('Server: recvfrom: ' + str(client_addr), counter)    
    outputFile.write(buf)
    print ("Server: Sending ACK", counter)
    s.sendto(packet(counter, "ACK".encode()), client_addr)
    seq, buf = dec_packet(s.recvfrom(1024*2)[0])
    counter += 1
  print("Server: File closed.")
  outputFile.close()

  # Stop listening
  print("Server: Server stopped.")
  s.close()


# In[ ]:


server()
print("Image received by server: ")
renderImage("received.jpg")
get_ipython().system('rm received.jpg')

