import pygame


class Music:
    """背景音乐播放器"""
    _initialized = False
    _init_error = False

    def __init__(self, music_file, volume=0.1):
        if not Music._initialized:
            try:
                pygame.mixer.init()
                Music._initialized = True
            except pygame.error as e:
                print(f"[警告] 初始化音频混合器失败: {e}")
                Music._init_error = True
        self._valid = False
        if not Music._init_error:
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(volume)
                self._valid = True
            except pygame.error as e:
                print(f"[警告] 加载音频文件失败: {music_file} - {e}")

    def play_music(self):
        """播放背景音乐"""
        if self._valid:
            try:
                pygame.mixer.music.play()
            except pygame.error:
                pass


class Sound:
    """音效播放器（短音频）"""
    _initialized = False
    _init_error = False

    def __init__(self, music_file, volume=0.05):
        if not Sound._initialized:
            try:
                pygame.mixer.init()
                Sound._initialized = True
            except pygame.error as e:
                print(f"[警告] 初始化音频混合器失败: {e}")
                Sound._init_error = True
        self._valid = False
        if not Sound._init_error:
            try:
                self.sound = pygame.mixer.Sound(music_file)
                self.sound.set_volume(volume)
                self._valid = True
            except (pygame.error, FileNotFoundError) as e:
                print(f"[警告] 加载音效文件失败: {music_file} - {e}")

    def play_music(self):
        """播放音效"""
        if self._valid:
            try:
                self.sound.play()
            except pygame.error:
                pass
