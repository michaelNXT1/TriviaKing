import socket
from dev.config import client_consts, general, client_op_codes, server_op_codes, answer_keys
import random

global number_of_bots
number_of_bots = 1

def send_message(sock, msg, op_code=0x00):
    if not isinstance(msg, str):
        msg = str(msg)
        # Encode the string message and send it
    sock.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))

def receive_offer_broadcast():
    # Create UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Set SO_REUSEPORT option
    udp_socket.bind(('0.0.0.0', client_consts['server_port']))

    # Receive UDP broadcast
    data, addr = udp_socket.recvfrom(general['buffer_size'])

    # Parse received data
    magic_cookie = int.from_bytes(data[:4],  byteorder='big')
    message_type = int.from_bytes(data[4:5],  byteorder='big')
    server_name = data[5:37].decode('utf-8').strip()
    server_port = int.from_bytes(data[37:39], byteorder='big')

    # Check if the received message is an offer   
    if magic_cookie == client_consts['magic_cookie'] and message_type == client_consts['message_type']:
        print(f'Received offer from server “{server_name}” at address {addr[0]}, attempting to connect...')
        global number_of_bots
        random_number = random.randint(1, 100)
        user_name = f"BOT{random_number}"
        number_of_bots = number_of_bots + 1
        print(f"Bot name: {user_name}")

    # Establish TCP connection
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((addr[0], server_port))

        try:
            # Send success message over TCP
            send_message(tcp_socket, user_name, client_op_codes['client_sends_name'])
            print('successfully connected')
            # Continuously prompt user for input until "QUIT" is entered
            while True:
                # Receive response from server
                try:
                    data = tcp_socket.recv(1024)
                except ConnectionResetError:
                    #change the ptint
                    print("Connection reset by remote host. Reconnecting...")
                    break
                op_code = int.from_bytes(data[:1],  byteorder='big')
                content = data[1:].decode()
                if op_code == server_op_codes['server_sends_message']:
                    print('Message from Server: ' + content)
                elif op_code == server_op_codes['server_ends_game']:
                    print(content)
                    print("Game over")
                    break
                elif op_code == server_op_codes['server_requests_input']:
                    print('Question from Server: ' + content)
                    options = ['0', '1']
                    random_answer = random.choice(options)
                    print('Bot generated random answer: ' + str(answer_keys[random_answer]))
                    answer = answer_keys[random_answer]
                    send_message(tcp_socket, answer, client_op_codes['client_sends_answer'])
        finally:
            # Close TCP connection
            tcp_socket.close()
            #check this
            print("Server disconnected, listening for offer requests...")

    # Close UDP socket
    udp_socket.close()


def main():
    print('BOT started, listening for offer requests...')
    receive_offer_broadcast()


if __name__ == "__main__":
    main()
