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
