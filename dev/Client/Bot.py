from AbstractClient import Bot


def main():
    print('BOT started, listening for offer requests...')
    bot = Bot()
    bot.receive_offer_broadcast()


if __name__ == "__main__":
    main()
