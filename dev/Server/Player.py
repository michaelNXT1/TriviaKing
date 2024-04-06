class Player:
    def __init__(self, connection, client_address, user_name):
        self.connection = connection
        self.client_address = client_address
        self.user_name = user_name

    def __deepcopy__(self, memo):
        # Create a new Player object with the same attributes
        return Player(self.connection, self.client_address, self.user_name)
