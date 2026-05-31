class Music:
    pygame.mixer.init()
    def __init__(self,music_file, volume=0.1):

        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(volume)
    def play_music(self):
        pygame.mixer.music.play()

class Sound:
    pygame.mixer.init()

    def __init__(self, music_file, volume=0.05):
        self.sound= pygame.mixer.Sound(music_file)
        self.sound.set_volume(volume)

    def play_music(self):
        self.sound.play()