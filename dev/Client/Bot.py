import uuid
import random

from AbstractClient import AbstractClient
from dev import QandA
from dev.config import yellow_text, answer_keys, bot_consts


class Bot(AbstractClient):

    def __init__(self, level=5):
        self.level = level

    def get_name(self):
        new_uuid = uuid.uuid4()
        # Convert UUID to a hexadecimal string
        hex_string = new_uuid.hex
        # Convert hexadecimal string to integer
        uuid_as_number = int(hex_string, 16)
        user_name = f"BOT{uuid_as_number}"
        print(yellow_text(f"Bot name: {user_name}"))
        return user_name

    def get_answer(self, question):
        rand = 'hello'
        print(question)
        answer = QandA.questions_and_answers[question]
        if random.random() > self.level / 10:
            answer = not answer
        print('Bot generated random answer: ' + str(answer_keys[str(answer)[:1]]))
        return answer_keys[str(answer)[:1]]


def main():
    while True:
        print(f'BOT started, answer success rate is {bot_consts["level"] * 10}%, listening for offer requests...')
        bot = Bot(bot_consts['level'])
        bot.receive_offer_broadcast()


if __name__ == "__main__":
    main()
