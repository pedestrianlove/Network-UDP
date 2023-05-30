import socket
import pickle
import cv2
import matplotlib.pyplot as plt

class RDTUtility:
    def __init__(self, server_addr, client_addr):
        self.server_addr = server_addr
        self.client_addr = client_addr
        self.server_socket = self.create_socket()
        self.client_socket = self.create_socket()
        self.sequence_number = 0

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

    def packet(self, seq, binary_data):
        packet = (seq, binary_data)
        packet_bytes = pickle.dumps(packet)
        return packet_bytes

    def dec_packet(self, binary_packet):
        packet = pickle.loads(binary_packet)
        seq, binary_data = packet
        return seq, binary_data

    def send_packet(self, socket, packet):
        socket.sendto(packet, self.server_addr)

    def receive_packet(self, socket):
        return socket.recvfrom(1024 * 2)[0]

    def send_ack(self, socket, seq):
        ack_packet = self.packet(seq, "ACK".encode())
        self.send_packet(socket, ack_packet)

    def is_expected_seq(self, seq):
        return seq == self.sequence_number

    def rdt_send(self, socket, data):
        packet = self.packet(self.sequence_number, data)
        while True:
            print ("Sending the packet with SEQ=", self.sequence_number, "...")
            self.send_packet(socket, packet)
            ack_packet = self.receive_packet(socket)
            seq, _ = self.dec_packet(ack_packet)
            if self.is_expected_seq(seq):
                print ("Correct SEQ received, goes on sending another one...")
                self.sequence_number += 1
                break
            else:
                print ("Incorrect SEQ received, sending another one...")
                continue

    def rdt_receive(self, socket):
        while True:
            print ("Receiving the packet with SEQ=", self.sequence_number, "...")
            packet = self.receive_packet(socket)
            seq, data = self.dec_packet(packet)
            if self.is_expected_seq(seq):
                print ("Correct SEQ received, saving...")
                self.send_ack(socket, seq)
                self.sequence_number += 1
                return data
            else: # resend ack
                print ("Incorrect SEQ received, continuing...")
                self.send_ack(socket, self.sequence_number)
                continue

    def start_server(self):
        print("Server: Server starting...")
        self.server_socket.bind(self.server_addr)
        print("Server: Listening at: ", str(self.server_addr))
        print("Server: Waiting for data...")

        outputFile = open('received.jpg', 'wb')
        while True:
            data = self.rdt_receive(self.server_socket)
            if data.decode() == "stop":
                break
            outputFile.write(data)
        print("Server: File closed.")
        outputFile.close()

        print("Server: Server stopped.")
        self.server_socket.close()

    def start_client(self):
        print("Client: Client starting at...", str(self.client_addr))

        print("Client: Sending the following image:")
        self.renderImage("test.jpg")

        counter = 0
        testFile = open('test.jpg', 'rb')
        buf = testFile.read(1024)
        while buf:
            print("Client: Sending packet with SEQ...", counter)
            self.rdt_send(self.client_socket, buf)
            counter += 1
            buf = testFile.read(1024)

        print("Client: Sending stop signal...")
        self.rdt_send(self.client_socket, "stop".encode())

        testFile.close()
        print("Client stopped.")

    def renderImage(self, imagePath):
        imageObject = cv2.imread(imagePath, -1)
        plt.imshow(imageObject)
        plt.axis("off")
        plt.show()
