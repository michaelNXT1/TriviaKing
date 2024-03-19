import socket


def get_input_from_keyboard(prompt="Enter input: "):
    """
    Function to get input from the keyboard.

    Args:
    - prompt (str): Optional. Prompt to display to the user. Defaults to "Enter input: ".

    Returns:
    - str: User input from the keyboard.
    """
    user_input = input(prompt)
    return user_input


def receive_offer_broadcast():
    # Create UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('0.0.0.0', 13117))

    # Receive UDP broadcast
    data, addr = udp_socket.recvfrom(1024)

    # Parse received data
    magic_cookie = data[:4]
    message_type = data[4:5]
    server_name = data[5:37].decode('utf-8').strip()
    server_port = int.from_bytes(data[37:39], byteorder='big')

    # Check if the received message is an offer
    if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == b'\x02':
        print(f'Received offer from server “{server_name}” at address {addr[0]}, attempting to connect...')

        # Establish TCP connection
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((addr[0], server_port))

        try:
            # Send success message over TCP
            tcp_socket.sendall(b"success")


            # Continuously prompt user for input until "QUIT" is entered
            while True:
                # Receive response from server
                response = tcp_socket.recv(1024)
                print("Server response:", response.decode())
                user_input = get_input_from_keyboard("Enter your input (or 'QUIT' to exit): ")
                tcp_socket.sendall(user_input.encode())

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
