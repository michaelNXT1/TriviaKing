from abc import ABC, abstractmethod
import socket
from dev.config import client_consts, general, client_op_codes, server_op_codes, answer_keys , red_text, blue_text, yellow_text ,pink_text, green_text
import random
import uuid
class AbstractClient(ABC):
    def send_message(self,sock, msg, op_code=0x00):
        if not isinstance(msg, str):
            msg = str(msg)
            # Encode the string message and send it
        sock.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))

    @abstractmethod
    def getName(self):
        pass

    @abstractmethod
    def getAnswer(self):
        pass

    def receive_offer_broadcast(self):
        # Create UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Set SO_REUSEPORT option
        udp_socket.bind(('0.0.0.0', client_consts['server_port']))

        # Receive UDP broadcast
        data, addr = udp_socket.recvfrom(general['buffer_size'])

        # Parse received data
        magic_cookie = int.from_bytes(data[:4], byteorder='big')
        message_type = int.from_bytes(data[4:5], byteorder='big')
        server_name = data[5:37].decode('utf-8').strip()
        server_port = int.from_bytes(data[37:39], byteorder='big')

        # Check if the received message is an offer
        if magic_cookie == client_consts['magic_cookie'] and message_type == client_consts['message_type']:
            print(blue_text(f'Received offer from server “{server_name}” at address {addr[0]}, attempting to connect...'))

            user_name = self.getName()
            # Establish TCP connection
            try:
                tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tcp_socket.connect((addr[0], server_port))
            except ConnectionRefusedError:
                print(red_text("Connection refused"))
                exit()

            try:
                # Send success message over TCP
                self.send_message(tcp_socket,user_name, client_op_codes['client_sends_name'])
                # Continuously prompt user for input until "QUIT" is entered
                while True:
                    # Receive response from server
                    try:
                        data = tcp_socket.recv(1024)
                    except ConnectionResetError:
                        print(red_text("Connection reset by remote host. Reconnecting..."))
                        break
                    except KeyboardInterrupt:
                        break
                    op_code = int.from_bytes(data[:1], byteorder='big')
                    content = data[1:].decode()
                    if op_code == server_op_codes['server_sends_message'] :
                        print(blue_text('Message from Server: ' + content))
                    elif op_code == server_op_codes['server_ends_game']:
                        print(content)
                        # print("Game over")
                        break
                    elif op_code == server_op_codes['server_requests_input']:
                        print(pink_text('Question from Server: ' + content))
                        answer = self.getAnswer()
                        self.send_message(tcp_socket,answer, client_op_codes['client_sends_answer'])
                    elif op_code == server_op_codes['server_requests_other_name']:
                        print(red_text("Your name is in use by someone else, please try again"))
                        user_name = self.getName()
                        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tcp_socket.connect((addr[0], server_port))
                        self.send_message(tcp_socket, user_name, client_op_codes['client_sends_name'])
                    elif op_code == server_op_codes['server_check_connection']:
                        continue
                    else:
                        print(green_text('successfully connected'))
            finally:
                # Close TCP connection
                tcp_socket.close()
                # check this
                print(red_text("Server disconnected, listening for offer requests..."))

        # Close UDP socket
        udp_socket.close()


class Bot(AbstractClient):
    def getName(self):
        new_uuid = uuid.uuid4()
        # Convert UUID to a hexadecimal string
        hex_string = new_uuid.hex
        # Convert hexadecimal string to integer
        uuid_as_number = int(hex_string, 16)
        user_name = f"BOT{uuid_as_number}"
        print(yellow_text(f"Bot name: {user_name}"))
        return user_name

    def getAnswer(self):
        options = ['0', '1']
        random_answer = random.choice(options)
        print('Bot generated random answer: ' + str(answer_keys[random_answer]))
        return answer_keys[random_answer]

class Client(AbstractClient):
    def getName(self):
        try:
            user_name = input(yellow_text("Please enter your name: "))
            return user_name
        except KeyboardInterrupt:
            print(red_text("program stop when wait to name"))
            exit()

    def getAnswer(self):
        try:
            valid_answer = False
            while not valid_answer:
                print('please enter your answer: ', end='')
                user_input = input().upper()
                if user_input in answer_keys.keys():
                    valid_answer = True
                    answer = answer_keys[user_input]
                    return answer
        except KeyboardInterrupt:
            print(red_text("program stop when wait to answer"))
            exit()
