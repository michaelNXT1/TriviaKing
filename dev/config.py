general = dict(
    buffer_size=1024
)

client_constants = dict(
    server_port=13117,
    magic_cookie=0xabcddcba,
    message_type=0x02
)

client_op_codes = dict(
    client_sends_name=0x00,
    client_sends_answer=0x01
)

server_op_codes = dict(
    server_sends_welcome=0x00,
)