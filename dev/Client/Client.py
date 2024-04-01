import socket
from dev.config import client_consts, general, client_op_codes, server_op_codes, answer_keys
import sys
import tty
import termios


def getch():
    # Save the current terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        # Set the terminal to raw mode
        tty.setraw(fd)
        # Read a single character from the keyboard
        ch = sys.stdin.read(1)
    finally:
        # Restore the terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def send_message(sock, msg, op_code=0x00):
    sock.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))


def receive_offer_broadcast():
    # Create UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', client_consts['server_port']))

    # Receive UDP broadcast
    data, addr = udp_socket.recvfrom(general['buffer_size'])

    # Parse received data
    magic_cookie = int.from_bytes(data[:4])
    message_type = int.from_bytes(data[4:5])
    server_name = data[5:37].decode('utf-8').strip()
    server_port = int.from_bytes(data[37:39], byteorder='big')

    # Check if the received message is an offer
    if magic_cookie == client_consts['magic_cookie'] and message_type == client_consts['message_type']:
        print(f'Received offer from server “{server_name}” at address {addr[0]}, attempting to connect...')
        user_name = input("Please enter your name: ")

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
                data = tcp_socket.recv(1024)
                op_code = int.from_bytes(data[:1])
                content = data[1:].decode()
                if op_code == server_op_codes['server_sends_message']:
                    print(content)
                if op_code == server_op_codes['server_ends_game']:
                    print(content)
                    print("Game over")
                    break
                elif op_code == server_op_codes['server_requests_input']:
                    valid_answer = False
                    while not valid_answer:
                        print('please enter your answer: ', end='')
                        user_input = getch().upper()
                        if user_input in answer_keys.keys():
                            valid_answer = True
                            answer = answer_keys[user_input]
                            send_message(tcp_socket, answer, client_op_codes['client_sends_answer'])
        finally:
            # Close TCP connection
            tcp_socket.close()
    # Close UDP socket
    udp_socket.close()


def main():
    print('Client started, listening for offer requests...')
    receive_offer_broadcast()


if __name__ == "__main__":
    main()
