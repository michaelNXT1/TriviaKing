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
)

answer_keys = {
    'Y': True,
    'T': True,
    '1': True,
    'N': False,
    'F': False,
    '2': False
}


def game_welcome_message(server_name, subject):
    return f"Welcome to the {server_name} server, where we are answering trivia questions about {subject}."


def round_details(round_number, active_players):
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


def red_text(text):
    return "\033[1;31m" + text + "\033[0m"


def green_text(text):
    return "\033[1;32m" + text + "\033[0m"


def blue_text(text):
    return "\033[1;34m" + text + "\033[0m"


def yellow_text(text):
    return "\033[1;33m" + text + "\033[0m"


def cyan_text(text):
    return "\033[1;36;40m" + text + "\033[0m"
