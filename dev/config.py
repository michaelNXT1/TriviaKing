general = dict(
    buffer_size=1024
)

server_consts = dict(
    server_port=13117,
    magic_cookie=0xabcddcba,
    message_type=0x02
)

client_consts = dict(
    server_port=13117,
    magic_cookie=0xabcddcba,
    message_type=0x02
)

client_op_codes = dict(
    client_sends_name=0x00,
    client_sends_answer=0x01
)

server_op_codes = dict(
    server_sends_message=0x00,
    server_requests_input=0x01,
    server_ends_game=0x02,
    server_requests_other_name=0x03,
    server_check_connection=0x04
)

answer_keys = {
    'Y': True,
    'T': True,
    '1': True,
    'N': False,
    'F': False,
    '0': False
}


def game_welcome_message(server_name, subject):
    return f"Welcome to the {server_name} server, where we are answering trivia questions about {subject}."


def round_details(round_number, active_players):
    if len(active_players) >= 1:
        output = f"Round {round_number}, played by {active_players[0].user_name}"
        for active_player in active_players[1:]:
            output += f" and {active_player.user_name}"
        print(yellow_text(output))


def game_over_message(winner_name):
    return f"Game Over!\nCongratulations to the winner: {winner_name.user_name} \n"


def game_winner():
    return "Congratulations you won!"


def player_lost(player_name):
    return f"{player_name} Sorry, you didn't win this time. Better luck next round!"


def player_is_correct(player_name):
    return f"{player_name} is correct!"


def player_times_up(player_name):
    return f"{player_name} times up!"


def fastest_player_time(player_name, avg_response_time):
    print(blue_text(
        f"Fastest Player in TriviaKing: {player_name} with Average Response Time: {avg_response_time} seconds"))


def avg_response_time(avg_time):
    message = f"Your average response time: {avg_time:.2f} seconds"
    return message


def red_text(text):
    return "\033[1;31m" + text + "\033[0m"


def green_text(text):
    return "\033[1;32m" + text + "\033[0m"


def cyan_text(text):
    return "\033[1;36;40m" + text + "\033[0m"


def blue_text(text):
    return "\033[1;34m" + text + "\033[0m"


def yellow_text(text):
    return "\033[1;33m" + text + "\033[0m"


def pink_text(text):
    return "\033[95m" + text + "\033[0m"


def check_player_name(player_name, active_players):
    for active_player in active_players:
        if active_player.user_name == player_name:
            return True
    return False


def get_player_by_connection(connection, active_connection):
    for active_player in active_connection:
        if active_player.connection == connection:
            return active_player


def intersection_lists(active_players, active_connections):
    new_active_players = []
    for active_player in active_players:
        for active_connection in active_connections:
            if active_player.user_name == active_connection.user_name:
                new_active_players.append(active_player)
                break  # Exit inner loop after finding a match
    active_players[:] = new_active_players


def print_table(player_responses, round_num):
    num_rounds = round_num
    num_players = len(player_responses)

    # Calculate the width of each cell
    cell_width = 20  # Adjust this value based on your content width

    # Print top border
    print("┌", end="")
    for _ in range(num_rounds):
        print("─" * (cell_width + 2) + "┬", end="")
    print("─" * (cell_width + 2) + "┐")

    # Print headers
    print("│".rjust(cell_width), end="")
    for i in range(1, num_rounds + 1):
        print(f" Round {i} ".center(cell_width), end="│")
    print()

    # Print middle border
    print("├", end="")
    for _ in range(num_rounds):
        print("─" * (cell_width + 2) + "┼", end="")
    print("─" * (cell_width + 2) + "┤")

    # Print player rows
    for user_name, responses in player_responses.items():
        print(f"│ {user_name.ljust(cell_width)}", end="")
        for response in responses:
            print(f" {response.center(cell_width)} ", end="")
        # Fill remaining empty cells
        for _ in range(num_rounds - len(responses)):
            print(" " * (cell_width + 2), end="")
        print("│")

    # Print bottom border
    print("└", end="")
    for _ in range(num_rounds):
        print("─" * (cell_width + 2) + "┴", end="")
    print("─" * (cell_width + 2) + "┘")


