from AbstractClient import Client

def main():
    print('Client started, listening for offer requests...')
    client = Client()
    client.receive_offer_broadcast()


if __name__ == "__main__":
    main()
