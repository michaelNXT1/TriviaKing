import copy
import socket
import threading
import time

from dev import QandA
from dev.Server.Player import Player
from dev.config import server_op_codes, general_consts, game_welcome_message, server_consts, round_details, \
    game_over_message, blue_text, green_text, red_text, yellow_text, fastest_player_time, avg_response_time, \
    print_table, intersection_lists

active_connections = []  # List to store active connections
stop_udp_broadcast = False
server_name = "TeamMysticServer"
disqualified_players = []
game_on = False


def send_offer_broadcast():
    # Define server name and port
    server_port = 12345  # Example port, replace with your desired port
    server_name_32 = server_name.ljust(32)  # Ensure server name is 32 characters long

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
        try:
            connection.sendall(op_code.to_bytes(1) + bytes(msg.ljust(general_consts['buffer_size'] - 1), 'utf-8'))
            return
        except BrokenPipeError:
            print(f"BrokenPipeError: Connection closed unexpectedly with {connection}")
            remove_player_by_connection(connection, active_connections)
            return
    print(blue_text(msg))
    for p in active_connections:
        try:
            p.connection.sendall(op_code.to_bytes(1, byteorder='big') + bytes(msg.ljust(1023), 'utf-8'))
        except (ConnectionResetError, ConnectionAbortedError):
            print(f"Error occurred with connection from {p.client_address}")
            remove_player(p, active_connections)
        except BrokenPipeError:
            print(f"BrokenPipeError: Connection closed unexpectedly with {p.client_address}")
            remove_player(p, active_connections)


def handle_tcp_connection(connection, client_address):
    try:
        data = connection.recv(general_consts['buffer_size'])
        given_username = data[1:].decode()
        if any(p.user_name == given_username for p in active_connections):
            send_tcp_message('', server_op_codes['server_requests_other_name'], connection)
            return False
        else:
            print(yellow_text(f"Connection accepted from: {client_address}, named {given_username}"))
            active_connections.append(Player(connection, client_address, given_username))
            send_tcp_message('Successfully connected!', server_op_codes['server_sends_message'], connection)
            return True

    except Exception as e:
        print(f"Error occurred with connection from {client_address}: {e}")
        remove_player_by_connection(connection, active_connections)
        exit()  # TODO: seems like a dangerous command, doesn't it exit the server entirely?


def monitor_connections():
    while True:
        output = f"Number of active connections: {len(active_connections)}"  # Print the number of active connections
        send_tcp_message(output, server_op_codes['server_check_connection'])  # Check that active connections are stable
        time.sleep(1)  # Sleep for 5 seconds before checking again
        if game_on:
            return


def wait_for_clients():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
    server_address = ('', 12345)  # Example port, replace with your desired port
    while True:
        try:
            tcp_socket.bind(server_address)  # Bind the socket to the address and port
            break
        except OSError:
            print(red_text('Address still in use, sleeping for 5 seconds..'))
            time.sleep(5)
    tcp_socket.listen(5)  # Listen for incoming connections
    threading.Thread(target=send_offer_broadcast, daemon=True).start()  # Start UDP broadcast thread
    threading.Thread(target=monitor_connections, daemon=True).start()  # Start a thread to monitor active connections
    print(yellow_text("Server started, listening on IP address 172.1.0.4"))
    last_join_time = time.time()
    while time.time() - last_join_time < 10:
        tcp_socket.settimeout(10)
        try:
            connection, client_address = tcp_socket.accept()  # Accept incoming connection
            if handle_tcp_connection(connection, client_address):
                last_join_time = time.time()
        except socket.timeout:
            break
        except KeyboardInterrupt:
            print(red_text("Connection interrupted by user, stopping server..."))
            exit()
    global stop_udp_broadcast
    stop_udp_broadcast = True


def calculate_statistics():
    print(yellow_text("Calculating statistics..."))
    for player in active_connections:
        avg_time_msg = avg_response_time(calculate_average_response_time(player))
        try:
            send_tcp_message(avg_time_msg, server_op_codes['server_sends_message'], player.connection)
        except ConnectionResetError:
            print("Error: Connection reset by peer")

    print_fastest_player()


def send_game_over_message(winner):
    global active_connections
    calculate_statistics()
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
        send_tcp_message(winner_output, server_op_codes['server_ends_game'], winner.connection)
    except ConnectionResetError:
        print("Error: Connection reset by peer")
    except ConnectionAbortedError:
        print("Error: Connection reset by peer")
    except BrokenPipeError:
        print("BrokenPipeError: Connection closed unexpectedly with {p.client_address}")
        # TODO: Handle the broken connection, such as removing the player from active connections

    for player in active_connections:
        player.connection.close()

    active_connections = []
    global game_on
    game_on = False


def add_response_time(player, response_time):
    for p in active_connections:
        if p.user_name == player.user_name:
            p.response_times.append(response_time)


def remove_player(player, active_players):
    new_active_players = []
    for p in active_players:
        if player.user_name != p.user_name:
            new_active_players.append(p)
    active_players[:] = new_active_players


def remove_player_by_connection(connection, active_players):
    active_players[:] = [player for player in active_players if player.connection != connection]


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
    # random.shuffle(qa_list) #TODO: disable comment when done
    question = qa_list[0]

    num_rounds = len(qa_list)
    player_responses = {p.user_name: ['' for _ in range(num_rounds)] for p in active_players}

    while len(active_players) > 1:
        send_tcp_message('', server_op_codes['server_check_connection'])
        intersection_lists(active_players, active_connections)

        if len(active_players) == 0:
            print(red_text("All the players are disconnected"))
            exit()
        round_details(round_number, active_players)
        try:
            for player in active_players:
                send_tcp_message(question, server_op_codes['server_requests_input'], player.connection)
        except ConnectionResetError:
            print("Error: Connection reset by peer")
        answer = QandA.questions_and_answers[question]
        client_threads = [threading.Thread(target=handle_answers, args=(p, answer)) for p in active_players]
        [thread.start() for thread in client_threads]
        [thread.join() for thread in client_threads]

        # Check if all players were disqualified
        if len(active_players) == len(disqualified_players):
            disqualified_players = []

        # Update player_responses based on active_players
        for player in active_players:
            if player and player not in disqualified_players:
                player_responses[player.user_name][round_number - 1] = green_text('✔')
            else:
                player_responses[player.user_name][round_number - 1] = red_text('✘')

        active_players = [p for p in active_players if p not in disqualified_players]
        disqualified_players = []
        round_number += 1
        # TODO check what happened when the questions end
        if round_number > len(qa_list):
            print(blue_text("The players were very smart for the TriviaKing"))
            break
        else:
            question = qa_list[round_number - 1]

    if len(active_players) >= 1:
        send_game_over_message(active_players[0])
    print_table(player_responses, round_number)


def handle_answers(player, correct_answer):
    client_name = player.user_name
    start_time = time.time()
    end_time = None
    answered = False
    received_answer = None
    while time.time() - start_time <= 10:  # Check if 10 seconds have elapsed  # TODO: make constant
        try:
            player.connection.settimeout(10 - (time.time() - start_time))  # Set timeout for receiving data TODO: make constant
            try:
                data = player.connection.recv(general_consts['buffer_size'])
                received_answer = data[1:].decode()
                if len(data) == 0:
                    print(red_text(f"The player {client_name} disconnected unexpectedly from the server"))
                    remove_player(player, active_connections)
                    exit()
            except (ConnectionAbortedError, ConnectionResetError):
                print("Error: Connection aborted by peer.")
                remove_player(player, active_connections)
                exit()
            answered = True
            end_time = time.time()
            break  # Exit loop if data is received
        except socket.timeout:
            continue  # Continue looping if no data is received within timeout

    if answered:
        if received_answer == str(correct_answer):
            output = f"{client_name} is correct!"
            print(green_text(output))
        else:
            output = f"{client_name} is incorrect!"
            print(red_text(output))
            disqualified_players.append(player)
    else:
        output = f"{client_name}'s time is up!"
        print(red_text(output))
        disqualified_players.append(player)
        end_time = start_time + 10

    add_response_time(player, end_time - start_time)

    try:
        if player.connection is None:
            remove_player(player, active_connections)
        else:
            send_tcp_message(output, server_op_codes['server_sends_message'], connection=player.connection)
    except ConnectionResetError:
        print("Error: Connection reset by peer")
        remove_player(player, active_connections)


def calculate_average_response_time(player):
    total_response_time = sum(player.response_times)
    num_questions_answered = len(player.response_times)
    if num_questions_answered > 0:
        average_response_time = total_response_time / num_questions_answered
        return average_response_time
    else:
        return 0


def print_fastest_player():
    if len(active_connections) > 0:
        fastest_player = min(active_connections, key=lambda p: calculate_average_response_time(p))
        if fastest_player:
            fastest_player_time(fastest_player.user_name, calculate_average_response_time(fastest_player))
    else:
        print("All the players are disconnected")


def main():
    while True:
        global stop_udp_broadcast
        stop_udp_broadcast = False
        wait_for_clients()
        if len(active_connections) > 1:
            run_game()
        elif len(active_connections) == 0:
            print(yellow_text("No one connected "))
        else:
            print(yellow_text("Just one connection "))
        print(green_text("Next game will start in 5 seconds.."))
        time.sleep(5)

# TODO need to change after implementing the bot

if __name__ == "__main__":
    main()
