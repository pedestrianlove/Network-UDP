import asyncio
import socket

from Packet import Packet


class RDTUtility:
    # General variables
    timeout = None
    server_addr = None
    server_socket = None
    client_addr = None
    sequence_number = None
    client_socket = None

    # GBN variables
    window_size = None
    base_ptr = None
    failed = None

    @classmethod
    def __init__(cls, server_addr, client_addr):
        cls.server_addr = server_addr
        cls.client_addr = client_addr
        cls.server_socket = cls.create_socket()
        cls.client_socket = cls.create_socket()
        cls.sequence_number = 0
        cls.timeout = 5  # Set timeout value in seconds
        cls.window_size = 100

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

    async def receive_ack(self):
        checked_ptr = self.base_ptr
        while checked_ptr < self.base_ptr + self.window_size:
            try:
                self.client_socket.settimeout(self.timeout)
                ack_packet = Packet.receive(self.client_socket)
                if self.is_expected_seq(ack_packet.seq) and ack_packet.binary_data.decode() == "ACK":
                    print("RDT: Correct ACK SEQ received, shifting the window...")
                    self.sequence_number += 1
                    checked_ptr += 1
                else:
                    print("RDT: Incorrect ACK SEQ received,", ack_packet.seq, ", sending another one...")
                    print("RDT: ", ack_packet)

                # Set flags to resend the window
                self.failed = True
            except TimeoutError:
                self.failed = True
                continue
        return True

    # Userspace methods
    def rdt_send(self, packets_list):
        list_length = len(packets_list)
        self.base_ptr = 0
        self.failed = True

        # Start listening for ACK packets
        event_loop = asyncio.get_event_loop()
        ack_result = event_loop.create_task(self.receive_ack())

        while self.base_ptr < list_length:
            # Send packets on request
            if self.failed:
                self.failed = False
                # Get current window
                local_base_ptr = self.base_ptr
                print("RDT: Sending the packets with SEQ=", local_base_ptr, ", to ", local_base_ptr + self.window_size, "...")
                for i in range(local_base_ptr, local_base_ptr + self.window_size):
                    if i >= list_length:
                        break
                    packets_list[i].send(self.client_socket, self.client_addr)

        # Pickup the result of the ACK packets listening
        event_loop.run_until_complete(ack_result)

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

    def start_client(self):
        print("Client: Client starting at...", str(self.client_addr))
        self.client_socket.bind(self.client_addr)
        print("Client: Sending the following image: test.jpg")

        # Read the binary data from file and buffer into packets list
        packets_list = []
        counter = 0
        testFile = open('test.jpg', 'rb')
        buf = testFile.read(1024)
        while buf:
            print("Client: Buffering packet with SEQ...", counter)
            packets_list.append(Packet(counter, buf))
            counter += 1
            buf = testFile.read(1024)

        # Send the buffered packets
        self.rdt_send(packets_list)

        print("Client: File sent.")
        print("Client: Sending stop signal...")
        self.rdt_send("stop".encode())

        testFile.close()
        print("Client stopped.")
