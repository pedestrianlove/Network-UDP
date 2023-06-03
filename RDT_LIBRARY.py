import socket
import pickle


class Packet:
    seq = None
    binary_data = None

    def __init__(self, seq_input, data_input):
        self.seq = seq_input
        self.binary_data = data_input

    def __str__(self):
        return "Packet: SEQ=" + str(self.seq) + ", DATA=" + str(self.binary_data)

    # Utility Methods
    def encode(self):
        packet = (self.seq, self.binary_data)
        packet_bytes = pickle.dumps(packet)
        return packet_bytes

    @staticmethod
    def decode(binary_packet):
        packet = pickle.loads(binary_packet)
        seq, binary_data = packet
        return Packet(seq, binary_data)

    # Userspace methods
    def send(self, assigned_socket, addr):
        packet = self.encode()
        assigned_socket.sendto(packet, addr)

    @staticmethod
    def receive(assigned_socket):
        binary_packet = assigned_socket.recvfrom(1024 * 2)[0]
        return Packet.decode(binary_packet)


class RDTUtility:
    timeout = None
    server_addr = None
    server_socket = None
    client_addr = None
    sequence_number = None
    client_socket = None

    @classmethod
    def __init__(cls, server_addr, client_addr):
        cls.server_addr = server_addr
        cls.client_addr = client_addr
        cls.server_socket = cls.create_socket()
        cls.client_socket = cls.create_socket()
        cls.sequence_number = 0
        cls.timeout = 5  # Set timeout value in seconds

    @staticmethod
    def create_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock

    @classmethod
    def send_ack(cls, addr, seq):
        ack_packet = Packet(seq, "ACK".encode())
        ack_packet.send(cls.server_socket, addr)

    @classmethod
    def is_expected_seq(cls, seq):
        return seq == cls.sequence_number

    # Userspace methods
    @classmethod
    def rdt_send(cls, data):
        packet = Packet(cls.sequence_number, data)
        while True:
            print("RDT: Sending the packet with SEQ=", packet.seq, "...")
            packet.send(cls.client_socket, cls.server_addr)
            try:
                cls.client_socket.settimeout(cls.timeout)
                ack_packet = Packet.receive(cls.client_socket)
                if cls.is_expected_seq(ack_packet.seq) and ack_packet.binary_data.decode() == "ACK":
                    print("RDT: Correct ACK SEQ received, goes on sending another one...")
                    cls.sequence_number += 1
                    break
                else:
                    print("RDT: Incorrect ACK SEQ received,", ack_packet.seq, ", sending another one...")
                    print("RDT: ", ack_packet)
                    continue
            except TimeoutError:
                print("RDT: Timeout occurred, resending the packet...")
                continue

    @classmethod
    def rdt_receive(cls):
        while True:
            print("RDT: Receiving the packet with SEQ=", cls.sequence_number, "...")
            try:
                cls.server_socket.settimeout(cls.timeout)
                packet = Packet.receive(cls.server_socket)
                if cls.is_expected_seq(packet.seq):
                    print("RDT: Correct SEQ received,", packet.seq, ", saving...")
                    cls.sequence_number += 1
                    print("RDT: Sending ACK with SEQ=", packet.seq, ", to the client...")
                    print("RDT: ", packet)
                    cls.send_ack(cls.client_addr, cls.sequence_number - 1)
                    return packet.binary_data
                else:
                    print("RDT: Incorrect SEQ received,", packet.seq, ", resending the last ack...")
                    cls.send_ack(cls.client_addr, cls.sequence_number - 1)
                    break
            except TimeoutError:
                print("RDT: Timeout occurred, waiting for the packet...")
                continue

    @classmethod
    def start_server(cls):
        print("Server: Server starting...")
        cls.server_socket.bind(cls.server_addr)
        print("Server: Listening at: ", str(cls.server_addr))
        print("Server: Waiting for data...")

        outputFile = open('received.jpg', 'wb')
        while True:
            data = cls.rdt_receive()
            try:
                if data.decode() == "stop":
                    break
                outputFile.write(data)
            except UnicodeDecodeError:
                outputFile.write(data)
        print("Server: File closed.")
        outputFile.close()

        print("Server: Server stopped.")
        cls.server_socket.close()

    @classmethod
    def start_client(cls):
        print("Client: Client starting at...", str(cls.client_addr))
        cls.client_socket.bind(cls.client_addr)
        print("Client: Sending the following image: test.jpg")

        testFile = open('test.jpg', 'rb')
        buf = testFile.read(1024)
        while buf:
            print("Client: Sending packet with SEQ...", cls.sequence_number)
            cls.rdt_send(buf)
            buf = testFile.read(1024)

        print("Client: File sent.")
        print("Client: Sending stop signal...")
        cls.rdt_send("stop".encode())

        testFile.close()
        print("Client stopped.")
