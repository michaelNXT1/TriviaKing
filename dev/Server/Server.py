import copy
import socket
import threading
import time

from dev import QandA
from dev.Server.Player import Player
from dev.config import server_op_codes, game_welcome_message, server_consts, \
    round_details, game_over_message, game_winner, blue_text, green_text, red_text, yellow_text, cyan_text, check_player_name, get_player_by_clinent_adrres ,intersection_lists

active_connections = []  # List to store active connections
# client_threads = []  # List to store each client's thread
stop_udp_broadcast = False
server_name = "TeamMysticServer"
disqualified_players = []
game_on = False


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


def send_tcp_message(msg, op_code, connection=None):
    if connection is not None:
        connection.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))
        return
    print(cyan_text(msg))
    for p in active_connections:
       try:
            p.connection.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg, 'utf-8'))
       except ConnectionResetError:
            print(f"Error occurred with connection from {p.client_address}")
            remove_player(p, active_connections)
       except ConnectionAbortedError:
           print("Error occurred with connection from {}".format(p.client_address))
           remove_player(p,active_connections)
       except BrokenPipeError:
           print("BrokenPipeError: Connection closed unexpectedly with {p.client_address}")
           # Handle the broken connection, such as removing the player from active connections
           remove_player(p,active_connections)

def handle_tcp_connection(connection, client_address):
    try:
        data = connection.recv(1024)
        content = data[1:].decode()
        if check_player_name(content, active_connections):
            connection.sendall(server_op_codes['server_requests_other_name'].to_bytes(1, byteorder='big'))
        else:
            print(yellow_text(f"Connection accepted from: {client_address}"))
            active_connections.append(Player(connection, client_address, content))
            connection.sendall(b"Your name has been submitted!")


    except Exception as e:
        print(f"Error occurred with connection from {client_address}: {e}")
        player = get_player_by_clinent_adrres(client_address, active_connections)
        remove_player(player,active_connections)
        exit()

    #finally:
    #     # Remove connection from the list of active connections
    #     del active_connections[(connection, client_address)]
    #     # Clean up the connection
    #     connection.close()
    #     print("Connection closed with:", client_address)


def monitor_connections():
    while True:
        # Print the number of active connections
        output = f"Number of active connections: {len(active_connections)}"
        send_tcp_message(output, server_op_codes['server_check_connection'])
        # Sleep for 5 seconds before checking again
        time.sleep(5)
        if game_on:
            return


def get_player_name(player_address):
    for p in active_connections:
        if p.client_address == player_address:
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
    print(yellow_text("Server started, listening on IP address 172.1.0.4"))
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



def send_game_over_message(winner):
    if winner in active_connections:
        active_connections.remove(winner)
    output = game_over_message(winner)
    try:
        send_tcp_message(output, server_op_codes['server_ends_game'])
    except ConnectionResetError:
        remove_player(winner.client_address, active_connections)
        print("Error: Connection reset by peer")
    winner_output = "Congratulations you won!"
    try:
        winner.connection.sendall(server_op_codes['server_ends_game'].to_bytes(1, byteorder='big') +
                              bytes(winner_output, 'utf-8'))
    except ConnectionResetError:
        print("Error: Connection reset by peer")
    except ConnectionAbortedError:
        print("Error: Connection reset by peer")
    global game_on
    game_on = False


def players_in_game():
    active_players = []
    for player in active_connections:
        active_players.append(player)
    return active_players



def remove_player(player, active_players):
    if player in active_players:
        active_players.remove(player)



def run_game():
    global game_on
    game_on = True
    global disqualified_players  # Declare disqualified_players as a global variable
    round_number = 1
    active_players = copy.deepcopy(active_connections)
    try:
        send_tcp_message(game_welcome_message(server_name, QandA.subject), server_op_codes['server_sends_message'])
    except ConnectionResetError:
        print("Error: Connection reset by peer")
    import random
    qa_list = list(QandA.questions_and_answers.keys())
    # random.shuffle(qa_list)
    question = qa_list[0]
    while len(active_players) > 1:
        if len(active_players) == 0:
            exit()
        round_details(round_number, active_players)
        client_threads = []
        answer = QandA.questions_and_answers[question]
        try:
            send_tcp_message(question, server_op_codes['server_requests_input'])
        except ConnectionResetError:
            print("Error: Connection reset by peer")
        for p in active_players:
            client_thread = threading.Thread(target=handle_answers, args=(p, answer))
            client_threads.append(client_thread)

        for client_thread in client_threads:
            client_thread.start()

        for client_thread in client_threads:
            client_thread.join()

        # Check if all players were disqualified
        if len(active_players) == len(disqualified_players):
            disqualified_players = []

        for player in disqualified_players:
            remove_player(player, active_players)
            disqualified_players.remove(player)
        send_tcp_message('', server_op_codes['server_check_connection'])
        intersection_lists(active_players, active_connections)
        round_number += 1
        #TODO check what happend when the questions end
        if round_number-1 > len(qa_list):
            print(blue_text("The players were very smart for the TriviaKing"))
            break
        else:
            question = qa_list[round_number-1]
    if len(active_players)>=1:
        send_game_over_message(active_players[0])



def handle_answers(player, correct_answer):
    client_name = player.user_name
    start_time = time.time()
    answer_flag = False
    output = ''
    while time.time() - start_time <= 10:  # Check if 10 seconds have elapsed
        try:
            player.connection.settimeout(10 - (time.time() - start_time))  # Set timeout for receiving data
            try:
                data = player.connection.recv(1024)
                received_answer = data[1:].decode()
            except ConnectionAbortedError:
                 print("Error: Connection aborted by peer")
                 exit()
            except ConnectionResetError:
                print("Error: Connection aborted by peer")
            answer_flag = True
            break  # Exit loop if data is received
        except socket.timeout:
            continue  # Continue looping if no data is received within timeout

    if answer_flag:
        if received_answer == str(correct_answer):
            output = f"{client_name} is correct!"
            print(green_text(f"{client_name} is correct!"))
        else:
            output = f"{client_name} is incorrect!"
            print(red_text(f"{client_name} is incorrect!"))
            disqualified_players.append(player)

    else:
        output = f"{client_name} time's up!"
        print(red_text(f"{client_name} time's up!"))
        disqualified_players.append(player)

    try:
        if player.connection is None:
            remove_player(player, active_connections)
        else:
            send_tcp_message(output, server_op_codes['server_sends_message'], connection=player.connection)
    except ConnectionResetError:
        print("Error: Connection reset by peer")
        remove_player(player, active_connections)

def main():
    wait_for_clients()
    if len(active_connections) >= 1:
        run_game()
    elif len(active_connections) == 0:
        print(yellow_text("No one connected "))
    else:
        print(yellow_text("Just one connection "))


# TODO need to change after implementing the bot

if __name__ == "__main__":
    main()
