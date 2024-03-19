import socket
import time
import threading


def send_offer_broadcast():
    # Define server name and port
    server_name = "TeamMysticServer"
    server_port = 12345  # Example port, replace with your desired port

    # Ensure server name is 32 characters long
    server_name = server_name.ljust(32)

    # Construct packet
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name_bytes = server_name.encode('utf-8')
    server_port_bytes = server_port.to_bytes(2, byteorder='big')

    packet = magic_cookie + message_type + server_name_bytes + server_port_bytes

    # Broadcast packet via UDP
    while True:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.sendto(packet, ('<broadcast>', 13117))
        udp_socket.close()
        time.sleep(1)


def handle_tcp_connections():
    # Create a TCP/IP socket
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_address = ('', 12345)  # Example port, replace with your desired port
    tcp_socket.bind(server_address)

    # Listen for incoming connections
    tcp_socket.listen(1)

    print("Server started, listening on IP address 172.1.0.4")

    try:
        while True:
            # Accept incoming connection
            connection, client_address = tcp_socket.accept()

            try:
                print("Connection accepted from:", client_address)

                while True:
                    print('here')
                    # Receive data from client
                    data = connection.recv(1024)
                    if not data:
                        break  # Break if no more data is received

                    message = data.decode()
                    print("Received:", message)

                    # Send response to client
                    connection.sendall(b"Thank you for the message!")

                    # Check if client wants to quit
                    if message.strip().upper() == "QUIT":
                        break

            finally:
                # Clean up the connection
                connection.close()
    finally:
        # Clean up the socket
        tcp_socket.close()


def main():
    # Start UDP broadcast thread
    udp_thread = threading.Thread(target=send_offer_broadcast)
    udp_thread.daemon = True
    udp_thread.start()

    # Start TCP server
    handle_tcp_connections()


if __name__ == "__main__":
    main()
