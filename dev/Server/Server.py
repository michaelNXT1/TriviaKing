import socket
import threading
import time

from dev import QandA
from dev.Server.Player import Player
from dev.config import server_op_codes, game_welcome_message, server_consts, \
    player_lost, next_round

active_connections = []  # List to store active connections
client_threads = []  # List to store each client's thread
stop_udp_broadcast = False
server_name = "TeamMysticServer"
disqualified_players = []


def send_offer_broadcast():
    # Define server name and port
    server_port = 12345  # Example port, replace with your desired port

    # Ensure server name is 32 characters long
    server_name_32 = server_name.ljust(32)

    # Construct packet
    magic_cookie = server_consts['magic_cookie'].to_bytes(4, byteorder='big')
    message_type = server_consts['message_type'].to_bytes(1, byteorder='big')
    server_name_bytes = server_name_32.encode('utf-8')
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


def send_tcp_message(msg, op_code):
    print(msg)
    for p in active_connections:
        p.connection.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))


def handle_tcp_connection(connection, client_address):
    try:
        print("Connection accepted from:", client_address)
        data = connection.recv(1024)
        content = data[1:].decode()
        active_connections.append(Player(connection, client_address, content))
        connection.sendall(b"Your name has been submitted!")

    except Exception as e:
        print(f"Error occurred with connection from {client_address}: {e}")

    # finally:
    #     # Remove connection from the list of active connections
    #     del active_connections[(connection, client_address)]
    #     # Clean up the connection
    #     connection.close()
    #     print("Connection closed with:", client_address)


def monitor_connections():
    while True:
        # Print the number of active connections
        print(f"Number of active connections: {len(active_connections)}")
        # Sleep for 5 seconds before checking again
        time.sleep(5)


def get_player_name(player):
    for p in active_connections:
        if p.client_address == player.client_address:
            return p.user_name
        return None


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
            handle_tcp_connection(connection, client_address)
            last_join_time = time.time()
        except socket.timeout:
            break
    global stop_udp_broadcast
    stop_udp_broadcast = True


def run_game():
    round_number = 0
    send_tcp_message(game_welcome_message(server_name, QandA.subject), server_op_codes['server_sends_message'])
    import random
    qa_list = list(QandA.questions_and_answers.keys())
    random.shuffle(qa_list)
    while len(active_connections) > 1:
        for question in qa_list:
            answer = QandA.questions_and_answers[question]
            send_tcp_message(question, server_op_codes['server_requests_input'])
            for p in active_connections:
                client_thread = threading.Thread(target=handle_answers, args=(p.connection, p.client_address, answer))
                client_threads.append(client_thread)

            for client_thread in client_threads:
                start_thread(client_thread)

            for thread in client_threads:
                thread.join()

            # Check if all players were disqualified
            if len(active_connections) == len(disqualified_players):
                disqualified_players = []

            for player in disqualified_players:
                send_tcp_message(player_lost(get_player_name(player.connection)),
                                 server_op_codes['server_sends_message'])
                disqualified_players.remove(player)
                active_connections.remove(player)

            print(next_round(round_number, active_connections))
            round_number += 1

    print(f"And the winner is {get_player_name(active_connections[0])}")


def handle_answers(connection, client_address, correct_answer):
    client_name = get_player_name(client_address)
    # active_connections.
    start_time = time.time()  # Get the current time
    answer_flag = False
    # Each player has 10 seconds to answer
    while (time.time() - start_time <= 10) or (not answer_flag):
        try:
            data = connection.recv(1024);
            received_answer = data[1:].decode()
            answer_flag = True
        except Exception as e:
            continue

    if answer_flag:
        if received_answer == correct_answer:
            # send_tcp_message(player_is_correct(client_name), server_op_codes['server_sends_message'])
            print(f"{client_name} is correct!")
        else:
            # send_tcp_message(player_is_incorrect(client_name), server_op_codes['server_sends_message'])
            print(f"{client_name} is incorrect!")
            disqualified_players.append(client_address)

    else:
        # send_tcp_message(player_times_up(get_player_name(client_address)), server_op_codes['server_sends_message'])
        # TODO need to print somthing?
        disqualified_players.append(client_address)


def main():
    wait_for_clients()
    if len(active_connections) >= 1:
        run_game()
    else:
        print("Just on connection ")
#         TODO need to change after implementing the bot

if __name__ == "__main__":
    main()
