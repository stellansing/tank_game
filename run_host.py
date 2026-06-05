from modules.LoadGame import MainGame

if __name__ == '__main__':
    game = MainGame()
    game.start_multiplayer_game(mode='host', level='1')
