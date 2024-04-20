import threading
from abc import ABC, abstractmethod
import socket
from dev.config import client_consts, general_consts, client_op_codes, server_op_codes, red_text, \
    blue_text, pink_text, green_text


class AbstractClient(ABC):
    def send_message(self, sock, msg, op_code=0x00):
        if not isinstance(msg, str):
            msg = str(msg)
            # Encode the string message and send it
        sock.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_answer(self, question):
        pass

    def receive_offer_broadcast(self):
        # Create UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Set SO_REUSEPORT option
        udp_socket.bind(('0.0.0.0', client_consts['server_port']))

        # Receive UDP broadcast
        try:
            data, addr = udp_socket.recvfrom(general_consts['buffer_size'])

        except KeyboardInterrupt:
            print(red_text("program stop when wait for UDP connection"))
            exit()

        # Parse received data
        magic_cookie = int.from_bytes(data[:4], byteorder='big')
        message_type = int.from_bytes(data[4:5], byteorder='big')
        server_name = data[5:37].decode('utf-8').strip()
        server_port = int.from_bytes(data[37:39], byteorder='big')

        # Check if the received message is an offer
        if magic_cookie == client_consts['magic_cookie'] and message_type == client_consts['message_type']:
            print(
                blue_text(f'Received offer from server “{server_name}” at address {addr[0]}, attempting to connect...'))

            user_name = self.get_name()
            # Establish TCP connection
            try:
                tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_socket.connect((addr[0], server_port))
            except ConnectionRefusedError:
                print(red_text("Connection refused"))
                exit()

            try:
                # Send success message over TCP
                self.send_message(tcp_socket, user_name, client_op_codes['client_sends_name'])
                # Continuously prompt user for input until "QUIT" is entered
                while True:
                    # Receive response from server
                    try:
                        data = tcp_socket.recv(general_consts['buffer_size'])
                    except ConnectionResetError:
                        print(red_text("Connection reset by remote host. Reconnecting..."))
                        break
                    except KeyboardInterrupt:
                        break
                    op_code = int.from_bytes(data[:1], byteorder='big')
                    content = data[1:].decode().rstrip()
                    if len(data) == 0:
                        print(red_text("Connection closed by remote host"))
                        break
                    # print(data) #TODO: delete, for debugging only
                    if op_code == server_op_codes['server_sends_message']:
                        print(blue_text('Message from Server: ' + content))
                    elif op_code == server_op_codes['server_ends_game']:
                        print(content)
                        break
                    elif op_code == server_op_codes['server_requests_input']:
                        threading.Thread(target=self.return_answer, args=(content, tcp_socket)).start()
                    elif op_code == server_op_codes['server_requests_other_name']:
                        print(red_text("Your name is in use by someone else, please try again"))
                        user_name = self.get_name()
                        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tcp_socket.connect((addr[0], server_port))
                        self.send_message(tcp_socket, user_name, client_op_codes['client_sends_name'])
                    elif op_code == server_op_codes['server_check_connection']:
                        continue
                    # elif op_code == server_op_codes['']:
                    #     continue
                    else:
                        print(green_text('successfully connected'))

            except ConnectionRefusedError:
                print(red_text("Connection refused"))
                exit()
            finally:
                # Close TCP connection
                tcp_socket.close()
                print(red_text("Server disconnected, listening for offer requests..."))

        # Close UDP socket
        udp_socket.close()

    def return_answer(self, content, tcp_socket):
        print(pink_text('Question from Server: ' + content))
        answer = self.get_answer(content)
        if answer is not None:
            self.send_message(tcp_socket, answer, client_op_codes['client_sends_answer'])

