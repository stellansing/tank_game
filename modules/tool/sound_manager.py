import cfg
from modules.tool.music import Sound


class SoundManager:
    """音效管理器，负责统一管理游戏音效的加载和播放"""
    _blast = None
    _bang = None
    _start = None

    @classmethod
    def play_blast(cls):
        """播放爆炸音效"""
        if cls._blast is None:
            cls._blast = Sound(cfg.AUDIO_PATHS['blast'], volume=0.1)
        cls._blast.play_music()

    @classmethod
    def play_hit(cls):
        """播放命中音效"""
        if cls._bang is None:
            cls._bang = Sound(cfg.AUDIO_PATHS['hit'], volume=0.07)
        cls._bang.play_music()

    @classmethod
    def play_start(cls):
        """播放游戏开始音效"""
        if cls._start is None:
            cls._start = Sound(cfg.AUDIO_PATHS['start'], volume=0.1)
        cls._start.play_music()
