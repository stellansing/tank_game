import pygame

class Music:
    _initialized = False

    def __init__(self, music_file, volume=0.1):
        if not Music._initialized:
            pygame.mixer.init()
            Music._initialized = True
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(volume)

    def play_music(self):
        pygame.mixer.music.play()

class Sound:
    _initialized = False

    def __init__(self, music_file, volume=0.05):
        if not Sound._initialized:
            pygame.mixer.init()
            Sound._initialized = True
        self.sound = pygame.mixer.Sound(music_file)
        self.sound.set_volume(volume)

    def play_music(self):
        self.sound.play()
