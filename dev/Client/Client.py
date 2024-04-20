from AbstractClient import AbstractClient
from inputimeout import inputimeout, TimeoutOccurred

from dev.config import answer_keys, yellow_text, red_text


class Client(AbstractClient):
    def is_bot(self):
        return False

    def accept_bot_name(self, content):
        pass

    def get_name(self):
        try:
            user_name = input(yellow_text("Please enter your name: "))
            return user_name
        except KeyboardInterrupt:
            print(red_text("\nProgram stop when wait to name"))
            exit()

    def get_answer(self, question):
        try:
            valid_answer = False
            while not valid_answer:
                user_input = inputimeout(prompt='please enter your answer: ', timeout=10).upper()  # TODO: use constant
                if user_input in answer_keys.keys():
                    answer = answer_keys[user_input]
                    return answer
        except KeyboardInterrupt:
            print("program stop when wait to answer")
            exit()
        except TimeoutOccurred:
            return None
        except Exception:
            return None


def main():
    while True:
        print('Client started, listening for offer requests...')
        client = Client()
        client.receive_offer_broadcast()


if __name__ == "__main__":
    main()
