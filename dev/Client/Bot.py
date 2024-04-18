from AbstractClient import Bot


def main():
    while True:
        print('BOT started, listening for offer requests...')
        bot = Bot()
        bot.receive_offer_broadcast()


if __name__ == "__main__":
    main()
