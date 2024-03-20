import socket
import threading
import time

active_connections = {}  # List to store active connections
stop_udp_broadcast = False


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
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while not stop_udp_broadcast:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.sendto(packet, ('<broadcast>', 13117))
        time.sleep(1)
    print('Terminating UDP broadcast.')
    udp_socket.close()


def handle_tcp_connection(connection, client_address):
    try:
        print("Connection accepted from:", client_address)
        active_connections[(connection, client_address)] = ''  # Add connection to the list of active connections

        while True:
            # Receive data from client
            data = connection.recv(1024)
            if not data:
                break  # Break if no more data is received
            op_code = int.from_bytes(data[:1])
            content = data[1:].decode()

            if op_code == 0x00:
                active_connections[(connection, client_address)] = content
                connection.sendall(b"Your name has been submitted!")
            else:
                print(f"Received from {client_address}: {content}")
                connection.sendall(b"Thank you for the message!")

            # Check if client wants to quit
            if content.strip().upper() == "QUIT":
                break

    except Exception as e:
        print(f"Error occurred with connection from {client_address}: {e}")

    finally:
        # Remove connection from the list of active connections
        del active_connections[(connection, client_address)]
        # Clean up the connection
        connection.close()
        print("Connection closed with:", client_address)


def monitor_connections():
    while True:
        # Print the number of active connections
        print(f"Number of active connections: {len(active_connections)}")
        # Sleep for 5 seconds before checking again
        time.sleep(5)


def start_thread(target, is_daemon):
    thread = threading.Thread(target=target)
    thread.daemon = is_daemon
    thread.start()
    return thread


def wait_for_clients():
    start_thread(send_offer_broadcast, True)  # Start UDP broadcast thread
    start_thread(monitor_connections, True)  # Start a thread to monitor active connections
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
    # Bind the socket to the address and port
    server_address = ('', 12345)  # Example port, replace with your desired port
    tcp_socket.bind(server_address)
    tcp_socket.listen(5)  # Listen for incoming connections
    print("Server started, listening on IP address 172.1.0.4")
    last_join_time = time.time()
    while time.time() - last_join_time < 10:
        tcp_socket.settimeout(10)
        try:
            connection, client_address = tcp_socket.accept()  # Accept incoming connection
            print("Connection accepted from:", client_address)
            active_connections[(connection, client_address)] = ''  # Add connection to the list of active connections
            data = connection.recv(1024)
            content = data[1:].decode()
            active_connections[(connection, client_address)] = content
            connection.sendall(b"Your name has been submitted!")
            last_join_time = time.time()
        except socket.timeout:
            break
    global stop_udp_broadcast
    stop_udp_broadcast = True


def main():
    wait_for_clients()


if __name__ == "__main__":
    main()
