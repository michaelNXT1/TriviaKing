import socket
import threading
from dev.config import client_constants, general, client_op_codes


def send_message(recipient_socket, message, op_code=0x00):
    recipient_socket.sendall(op_code.to_bytes(1, byteorder='big') + bytes(message, 'utf-8'))


def receive_offer_broadcast():
    # Create UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', client_constants['server_port']))

    # Receive UDP broadcast
    data, addr = udp_socket.recvfrom(general['buffer_size'])

    # Parse received data
    magic_cookie = int.from_bytes(data[:4])
    message_type = int.from_bytes(data[4:5])
    server_name = data[5:37].decode('utf-8').strip()
    server_port = int.from_bytes(data[37:39], byteorder='big')

    # Check if the received message is an offer
    if magic_cookie == client_constants['magic_cookie'] and message_type == client_constants['message_type']:
        print(f'Received offer from server “{server_name}” at address {addr[0]}, attempting to connect...')
        user_name = input("Please enter your name: ")

        # Establish TCP connection
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((addr[0], server_port))

        try:
            # Send success message over TCP
            send_message(tcp_socket, user_name, client_op_codes['client_sends_name'])

            # Continuously prompt user for input until "QUIT" is entered
            while True:
                # Receive response from server
                response = tcp_socket.recv(1024)
                print("Server response:", response.decode())
                user_input = input("Enter your input (or 'QUIT' to exit): ")
                send_message(tcp_socket, user_input)
                # tcp_socket.sendall(user_input.encode())

                if user_input.upper() == "QUIT":
                    break

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
