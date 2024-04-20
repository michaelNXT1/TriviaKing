import uuid
import random

from AbstractClient import AbstractClient
from dev import QandA
from dev.config import yellow_text, answer_keys, bot_consts


class Bot(AbstractClient):

    def __init__(self, level=5):
        self.level = level

    def is_bot(self):
        return True

    def accept_bot_name(self, content):
        print(yellow_text(f"Bot name: {content}"))

    def get_name(self):
        return ''

    def get_answer(self, question):
        rand = 'hello'
        print(question)
        answer = QandA.questions_and_answers[question]
        if random.random() > self.level / 10:
            answer = not answer
        print('Bot generated random answer: ' + str(answer_keys[str(answer)[:1]]))
        return answer_keys[str(answer)[:1]]


def main():
    try:
        while True:
            print(f'BOT started, answer success rate is {bot_consts["level"] * 10}%, listening for offer requests...')
            bot = Bot(bot_consts['level'])
            bot.receive_offer_broadcast()
    except KeyboardInterrupt:
        print(red_text("Process interrupted by user, exiting.."))


if __name__ == "__main__":
    main()
