import socket
import pickle


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

    @staticmethod
    def packet(seq, binary_data):
        packet = (seq, binary_data)
        packet_bytes = pickle.dumps(packet)
        return packet_bytes

    @staticmethod
    def dec_packet(binary_packet):
        packet = pickle.loads(binary_packet)
        seq, binary_data = packet
        return seq, binary_data

    @staticmethod
    def send_packet(addr, packet):
        socket.sendto(packet, addr)

    @staticmethod
    def receive_packet(socket):
        return socket.recvfrom(1024 * 2)[0]

    @classmethod
    def send_ack(cls, addr, seq):
        ack_packet = cls.packet(seq, "ACK".encode())
        cls.client_socket.sendto(ack_packet, addr)

    @classmethod
    def is_expected_seq(cls, seq):
        return seq == cls.sequence_number

    # Userspace methods
    @classmethod
    def rdt_send(cls, data):
        packet = cls.packet(cls.sequence_number, data)
        while True:
            print("RDT: Sending the packet with SEQ=", cls.sequence_number, "...")
            cls.client_socket.sendto(packet, cls.server_addr)
            try:
                cls.client_socket.settimeout(cls.timeout)
                ack_packet = cls.receive_packet(cls.client_socket)
                seq, data = cls.dec_packet(ack_packet)
                if cls.is_expected_seq(seq) and data.decode() == "ACK":
                    print("RDT: Correct ACK SEQ received, goes on sending another one...")
                    cls.sequence_number += 1
                    break
                else:
                    print("RDT: Incorrect ACK SEQ received,", seq, ", sending another one...")
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
                packet = cls.receive_packet(cls.server_socket)
                seq, data = cls.dec_packet(packet)
                if cls.is_expected_seq(seq):
                    print("RDT: Correct SEQ received,", seq, ", saving...")
                    cls.sequence_number += 1
                    print("RDT: Sending ACK with SEQ=", seq, ", to the client...")
                    cls.send_ack(cls.client_addr, cls.sequence_number - 1)
                    return data
                else:
                    print("RDT: Incorrect SEQ received,", seq, ", resending the last ack...")
                    cls.send_ack(cls.client_addr, cls.sequence_number - 1)
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
