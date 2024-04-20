general_consts = dict(
    buffer_size=1024,
    server_port=13117
)

server_consts = dict(
    server_port=general_consts['server_port'],
    magic_cookie=0xabcddcba,
    message_type=0x02,
    server_name_max_size=32,
    monitor_connections_sleep_time=5,
    next_connection_wait_time=10,
    answer_wait_time=10,
    next_game_start_time=5,
    address_wait_time=5
)

client_consts = dict(
    server_port=general_consts['server_port'],
    magic_cookie=0xabcddcba,
    message_type=0x02
)

bot_consts = dict(
    level=9
)

client_op_codes = dict(
    client_message=0x00,
    bot_message=0x01
)

server_op_codes = dict(
    server_sends_message=0x00,
    server_requests_input=0x01,
    server_ends_game=0x02,
    server_requests_other_name=0x03,
    server_check_connection=0x04,
    server_accepts_bot=0x05
)

answer_keys = {
    'Y': True,
    'T': True,
    '1': True,
    'N': False,
    'F': False,
    '0': False
}


def welcome_message(server_name, subject):
    return f"Welcome to the {server_name} server, where we are answering trivia questions about {subject}."


def round_details(round_number, active_players):
    if len(active_players) >= 1:
        user_names = ', '.join(player.user_name for player in active_players)
        last_comma_index = user_names.rfind(',')
        if last_comma_index != -1:
            user_names = user_names[:last_comma_index] + ' and' + user_names[last_comma_index + 1:]
        output = f"Round {round_number}, played by {user_names}:"
        print(yellow_text(output))


def game_over_message(winner_name):
    if len(winner_name) == 1:
        return f"Game Over!\nCongratulations to the winner: {winner_name[0].user_name}"
    return f"It's a tie!\nCongratulations to the winners: {','.join([obj.user_name for obj in winner_name])}"


def winner_message(winners):
    if len(winners) == 1:
        return f"Congratulations you won!"
    return f"It's a tie!\nCongratulations to the winners: {','.join([obj.user_name for obj in winners])}"


def game_winner():
    return "Congratulations you won!"


def player_lost(player_name):
    return f"{player_name} Sorry, you didn't win this time. Better luck next round!"


def player_is_correct(player_name):
    return f"{player_name} is correct!"


def player_times_up(player_name):
    return f"{player_name} times up!"


def fastest_player_time(player_name, avg_resp_time):
    print(blue_text(
        f"Fastest Player in TriviaKing: {player_name} with Average Response Time: {avg_resp_time} seconds"))


def avg_response_time(avg_time):
    message = f"Your average response time: {avg_time:.2f} seconds"
    return message


def red_text(text):
    return "\033[1;31m" + text + "\033[0m"


def green_text(text):
    return "\033[1;32m" + text + "\033[0m"


def blue_text(text):
    return "\033[1;34m" + text + "\033[0m"


def yellow_text(text):
    return "\033[1;33m" + text + "\033[0m"


def pink_text(text):
    return "\033[95m" + text + "\033[0m"


def intersection_lists(active_players, active_connections):
    new_active_players = []
    for active_player in active_players:
        for active_connection in active_connections:
            if active_player.user_name == active_connection.user_name:
                new_active_players.append(active_player)
                break  # Exit inner loop after finding a match
    active_players[:] = new_active_players


def print_table(player_responses, round_num):
    num_rounds = round_num - 1
    max_player_name_length = max(len(key) for key in player_responses.keys())
    cell_width = len("Round ") + len(str(num_rounds))

    # Print top border
    print("┌" + "─" * (max_player_name_length + 2) + "┬", end="")
    for _ in range(num_rounds - 1):
        print("─" * (cell_width + 2) + "┬", end="")
    print("─" * (cell_width + 2) + "┐")

    # Print headers
    print("│".ljust(max_player_name_length + 3), end="│")
    for i in range(1, num_rounds + 1):
        print(f" Round {i} ".center(cell_width + 2), end="│")
    print()

    # Print middle border
    print("├" + "─" * (max_player_name_length + 2) + "┼", end="")
    for _ in range(num_rounds - 1):
        print("─" * (cell_width + 2) + "┼", end="")
    print("─" * (cell_width + 2) + "┤")

    # Print player rows
    for user_name, responses in player_responses.items():
        print(f"│ {user_name.ljust(max_player_name_length + 1)}", end="│")
        for i in range(num_rounds):
            if responses[i] is None or responses[i] == '':
                print(f" {'Drop'.center(cell_width)} ", end="│")
            else:
                print(f" {responses[i].center(cell_width + 11)} ", end="│")
        print()

    # Print bottom border
    print("└" + "─" * (max_player_name_length + 2) + "┴", end="")
    for _ in range(num_rounds - 1):
        print("─" * (cell_width + 2) + "┴", end="")
    print("─" * (cell_width + 2) + "┘")
