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
