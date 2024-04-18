import copy
import socket
import threading
import time

from dev import QandA
from dev.config import server_op_codes, general_consts, welcome_message, server_consts, round_details, \
    game_over_message, blue_text, green_text, red_text, yellow_text, fastest_player_time, avg_response_time, \
    print_table, intersection_lists
from dev.Server.Player import Player


def remove_player(connection, active_players):
    active_players[:] = [p for p in active_players if p.connection != connection]


def calculate_average_response_time(player):
    num_questions_answered = len(player.response_times)
    return sum(player.response_times) / num_questions_answered if num_questions_answered > 0 else 0


class Server(object):
    def __init__(self):
        self.active_connections = []  # List to store active connections
        self.disqualified_players = []
        self.stop_udp_broadcast = False
        self.server_name = "TeamMysticServer"  # Define server name
        self.game_on = False
        self.server_port = 12345  # Define server port
        self.stop_udp_broadcast = False

    def send_offer_broadcast(self):

        # Ensure server name is 32 characters long
        server_name_32 = self.server_name.ljust(server_consts['server_name_max_size'])

        # Construct packet
        magic_cookie = server_consts['magic_cookie'].to_bytes(4)
        message_type = server_consts['message_type'].to_bytes(1)
        server_name_bytes = server_name_32.encode('utf-8')
        server_port_bytes = self.server_port.to_bytes(2)

        packet = magic_cookie + message_type + server_name_bytes + server_port_bytes

        # Broadcast packet via UDP
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while not self.stop_udp_broadcast:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.sendto(packet, ('<broadcast>', 13117))
            time.sleep(1)
        print('Terminating UDP broadcast.')
        udp_socket.close()

    def send_tcp_message(self, msg, op_code, connection=None):
        if connection is not None:
            try:
                connection.sendall(op_code.to_bytes(1) + bytes(msg.ljust(general_consts['buffer_size'] - 1), 'utf-8'))
                return
            except BrokenPipeError:
                print(f"BrokenPipeError: Connection closed unexpectedly with {connection}")
                remove_player(connection, self.active_connections)
                return
        print(blue_text(msg))
        for p in self.active_connections:
            try:
                p.connection.sendall(op_code.to_bytes(1) + bytes(msg.ljust(general_consts['buffer_size'] - 1), 'utf-8'))
            except (ConnectionResetError, ConnectionAbortedError):
                print(f"Error occurred with connection from {p.client_address}")
                remove_player(p.connection, self.active_connections)
            except BrokenPipeError:
                print(f"BrokenPipeError: Connection closed unexpectedly with {p.client_address}")
                remove_player(p.connection, self.active_connections)

    def monitor_connections(self):
        while True:
            # Print the number of active connections
            output = f"Number of active connections: {len(self.active_connections)}"
            # Check that active connections are stable
            self.send_tcp_message(output, server_op_codes['server_check_connection'])
            time.sleep(server_consts['monitor_connections_sleep_time'])  # Sleep for 5 seconds before checking again
            if self.game_on:
                return

    def handle_tcp_connection(self, connection, client_address):
        try:
            data = connection.recv(general_consts['buffer_size'])
            given_username = data[1:].decode()
            if any(p.user_name == given_username for p in self.active_connections):
                self.send_tcp_message('', server_op_codes['server_requests_other_name'], connection)
                return False
            else:
                print(yellow_text(f"Connection accepted from: {client_address}, named {given_username}"))
                self.active_connections.append(Player(connection, client_address, given_username))
                self.send_tcp_message('Successfully connected!', server_op_codes['server_sends_message'], connection)
                return True

        except Exception as e:
            print(f"Error occurred with connection from {client_address}: {e}")
            remove_player(connection, self.active_connections)
            exit()  # TODO: seems like a dangerous command, doesn't it exit the server entirely?

    def wait_for_clients(self):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
        server_address = ('', self.server_port)  # Example port, replace with your desired port
        while True:
            try:
                tcp_socket.bind(server_address)  # Bind the socket to the address and port
                break
            except OSError:
                print(red_text(f'Address still in use, sleeping for {server_consts["address_wait_time"]} seconds..'))
                time.sleep(server_consts["address_wait_time"])
        tcp_socket.listen(5)  # Listen for incoming connections
        threading.Thread(target=self.send_offer_broadcast, daemon=True).start()  # Start UDP broadcast thread
        threading.Thread(target=self.monitor_connections, daemon=True).start()  # A thread to monitor active connections
        print(yellow_text("Server started, listening on IP address " + socket.gethostbyname(socket.gethostname())))
        last_join_time = time.time()
        while time.time() - last_join_time < server_consts['next_connection_wait_time']:
            tcp_socket.settimeout(server_consts['next_connection_wait_time'])
            try:
                connection, client_address = tcp_socket.accept()  # Accept incoming connection
                if self.handle_tcp_connection(connection, client_address):
                    last_join_time = time.time()
            except socket.timeout:
                break
            except KeyboardInterrupt:
                print(red_text("Connection interrupted by user, stopping server..."))
                exit()
        self.stop_udp_broadcast = True
        self.game_on = True

    def add_response_time(self, player, response_time):
        for p in self.active_connections:
            if p.user_name == player.user_name:
                p.response_times.append(response_time)

    def handle_answers(self, player, correct_answer):
        client_name = player.user_name
        start_time = time.time()
        end_time = None
        answered = False
        received_answer = None
        while time.time() - start_time <= server_consts['answer_wait_time']:  # Check if 10 seconds have elapsed
            try:
                # Set timeout for receiving data
                player.connection.settimeout(server_consts['answer_wait_time'] - (time.time() - start_time))
                try:
                    data = player.connection.recv(general_consts['buffer_size'])
                    received_answer = data[1:].decode()
                    if len(data) == 0:
                        print(red_text(f"The player {client_name} disconnected unexpectedly from the server"))
                        remove_player(player.connection, self.active_connections)
                        exit()
                except (ConnectionAbortedError, ConnectionResetError):
                    print("Error: Connection aborted by peer.")
                    remove_player(player.connection, self.active_connections)
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
                self.disqualified_players.append(player)
        else:
            output = f"{client_name}'s time is up!"
            print(red_text(output))
            self.disqualified_players.append(player)
            end_time = start_time + 10

        self.add_response_time(player, end_time - start_time)

        try:
            if player.connection is None:
                remove_player(player.connection, self.active_connections)
            else:
                self.send_tcp_message(output, server_op_codes['server_sends_message'], connection=player.connection)
        except ConnectionResetError:
            print("Error: Connection reset by peer")
            remove_player(player.connection, self.active_connections)

    def print_fastest_player(self):
        if len(self.active_connections) > 0:
            fastest_player = min(self.active_connections, key=lambda p: calculate_average_response_time(p))
            if fastest_player:
                fastest_player_time(fastest_player.user_name, calculate_average_response_time(fastest_player))
        else:
            print("All the players are disconnected")

    def calculate_statistics(self):
        print(yellow_text("Calculating statistics..."))
        for player in self.active_connections:
            avg_time_msg = avg_response_time(calculate_average_response_time(player))
            try:
                self.send_tcp_message(avg_time_msg, server_op_codes['server_sends_message'], player.connection)
            except ConnectionResetError:
                print("Error: Connection reset by peer")

        self.print_fastest_player()

    def send_game_over_message(self, winner):
        self.calculate_statistics()
        if winner in self.active_connections:
            self.active_connections.remove(winner)
        output = game_over_message(winner)
        try:
            self.send_tcp_message(output, server_op_codes['server_ends_game'])
        except ConnectionResetError:
            remove_player(winner.connection, self.active_connections)
            print("Error: Connection reset by peer")
        winner_output = "Congratulations you won!"
        try:
            self.send_tcp_message(winner_output, server_op_codes['server_ends_game'], winner.connection)
        except ConnectionResetError:
            print("Error: Connection reset by peer")
        except ConnectionAbortedError:
            print("Error: Connection reset by peer")
        except BrokenPipeError:
            print("BrokenPipeError: Connection closed unexpectedly with {p.client_address}")
            # TODO: Handle the broken connection, such as removing the player from active connections

        for player in self.active_connections:
            player.connection.close()

        self.active_connections = []
        self.game_on = False

    def run_game(self):
        self.game_on = True
        round_number = 1
        active_players = copy.deepcopy(self.active_connections)
        try:
            self.send_tcp_message(welcome_message(self.server_name, QandA.subject),
                                  server_op_codes['server_sends_message'])
        except ConnectionResetError:
            print("Error: Connection reset by peer")
        import random
        qa_list = list(QandA.questions_and_answers.keys())
        random.shuffle(qa_list)
        question = qa_list[0]
        player_responses = {p.user_name: ['' for _ in range(len(qa_list))] for p in active_players}

        while len(active_players) > 1:
            self.send_tcp_message('', server_op_codes['server_check_connection'])
            intersection_lists(active_players, self.active_connections)

            if len(active_players) == 0:
                print(red_text("All the players are disconnected"))
                exit()
            round_details(round_number, active_players)
            try:
                for player in active_players:
                    self.send_tcp_message(question, server_op_codes['server_requests_input'], player.connection)
            except ConnectionResetError:
                print("Error: Connection reset by peer")
            answer = QandA.questions_and_answers[question]
            client_threads = [threading.Thread(target=self.handle_answers, args=(p, answer)) for p in active_players]
            [thread.start() for thread in client_threads]
            [thread.join() for thread in client_threads]

            # Check if all players were disqualified
            if len(active_players) == len(self.disqualified_players):
                self.disqualified_players = []

            # Update player_responses based on active_players
            for player in active_players:
                if player and player not in self.disqualified_players:
                    player_responses[player.user_name][round_number - 1] = green_text('✔')
                else:
                    player_responses[player.user_name][round_number - 1] = red_text('✘')

            active_players = [p for p in active_players if p not in self.disqualified_players]
            self.disqualified_players = []
            round_number += 1
            # TODO check what happened when the questions end (end game)
            if round_number > len(qa_list):
                print(blue_text("The players were very smart for the TriviaKing"))
                break
            else:
                question = qa_list[round_number - 1]

        if len(active_players) >= 1:
            self.send_game_over_message(active_players[0])
        print_table(player_responses, round_number)

    def run_server(self):
        while True:
            self.stop_udp_broadcast = False
            self.wait_for_clients()
            if len(self.active_connections) > 1:
                self.run_game()
            elif len(self.active_connections) == 0:
                print(yellow_text("No one connected"))
            else:
                print(yellow_text("Just one connection"))
                self.send_tcp_message('Sorry, no additional players found.', server_op_codes['server_ends_game'], self.active_connections[0].connection)
                self.active_connections = []
            print(green_text(f"Next game will start in {server_consts['next_game_start_time']} seconds.."))
            time.sleep(server_consts['next_game_start_time'])


def main():
    Server().run_server()


if __name__ == "__main__":
    main()
