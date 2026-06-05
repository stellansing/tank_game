from modules.ClientLoadGame import ClientMainGame

if __name__ == '__main__':
    game = ClientMainGame()
    game.start_multiplayer_game(mode='join')
