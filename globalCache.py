import pygame
import cfg
'''坦克图片缓存管理器 - 用于预加载和共享图片资源'''

class TankImageCache:
    _cache = {}

    @classmethod
    def initialize(cls, cfg):
        cls._cache.clear()

        for player_key, paths in cfg.PLAYER_TANK_IMAGE_PATHS.items():
            cls._cache[player_key] = []
            for path in paths:
                direction_images = {}

                image = pygame.image.load(path).convert_alpha()
                image_width, image_height = image.get_size()

                frame_width = image_width // 2
                frame_height = image_height // 4

                # 切割上方图片（第1行，y=0）
                direction_images['U1'] = image.subsurface(0, 0, frame_width, frame_height)
                direction_images['U2'] = image.subsurface(frame_width, 0, frame_width, frame_height)

                # 切割下方图片（第2行，y=frame_height）
                direction_images['D1'] = image.subsurface(0, frame_height, frame_width, frame_height)
                direction_images['D2'] = image.subsurface(frame_width, frame_height, frame_width,frame_height)

                # 切割左方图片（第3行，y=2*frame_height）
                direction_images['L1'] = image.subsurface(0, 2 * frame_height, frame_width, frame_height)
                direction_images['L2'] = image.subsurface(frame_width, 2 * frame_height, frame_width,frame_height)

                # 切割右方图片（第4行，y=3*frame_height）
                direction_images['R1'] = image.subsurface(0, 3 * frame_height, frame_width, frame_height)
                direction_images['R2'] = image.subsurface(frame_width, 3 * frame_height, frame_width,frame_height)

                cls._cache[player_key].append(direction_images)


        for enemy_key, paths in cfg.ENEMY_TANK_IMAGE_PATHS.items():
            cls._cache[enemy_key] = []
            for path in paths:
                direction_images = {}

                image = pygame.image.load(path).convert_alpha()
                image_width, image_height = image.get_size()

                frame_width = image_width // 2
                frame_height = image_height // 4

                # 切割上方图片（第1行，y=0）
                direction_images['U1'] = image.subsurface(0, 0, frame_width, frame_height)
                direction_images['U2'] = image.subsurface(frame_width, 0, frame_width, frame_height)

                # 切割下方图片（第2行，y=frame_height）
                direction_images['D1'] = image.subsurface(0, frame_height, frame_width, frame_height)
                direction_images['D2'] = image.subsurface(frame_width, frame_height, frame_width, frame_height)

                # 切割左方图片（第3行，y=2*frame_height）
                direction_images['L1'] = image.subsurface(0, 2 * frame_height, frame_width, frame_height)
                direction_images['L2'] = image.subsurface(frame_width, 2 * frame_height, frame_width, frame_height)

                # 切割右方图片（第4行，y=3*frame_height）
                direction_images['R1'] = image.subsurface(0, 3 * frame_height, frame_width, frame_height)
                direction_images['R2'] = image.subsurface(frame_width, 3 * frame_height, frame_width, frame_height)

                cls._cache[enemy_key].append(direction_images)

    @classmethod
    def get_player_tank_image(cls, player_key, level):
        if player_key in cls._cache and level < len(cls._cache[player_key]):
            return cls._cache[player_key][level]
        return None

    @classmethod
    def get_tank_width(cls):
        if 'player1' in cls._cache:
            return cls._cache['player1'][0]['U1'].get_width()
        return 0

    @classmethod
    def get_enemy_tank_image(cls, tank_type, level):
        if tank_type in cls._cache and level < len(cls._cache[tank_type]):
            return cls._cache[tank_type][level]
        return None

class OtherImageCache:
    _cache = {}
    @classmethod
    def initialize(cls, cfg):
        cls._cache.clear()

        # ========== 爆炸动态图片切割 ==========
        different_stage_images = []
        image = pygame.image.load(cfg.OTHER_IMAGE_PATHS.get('boom_dynamic')).convert_alpha()
        image_width, image_height = image.get_size()
        frame_width = image_width // 6
        frame_height = image_height
        for i in range(6):
            different_stage_images.append(image.subsurface(i * frame_width, 0, frame_width, frame_height))
        cls._cache['boom_dynamic'] = different_stage_images

        # ========== 子弹图片 ==========
        cls._cache['bullets'] = {}
        for direction, path in cfg.BULLET_IMAGE_PATHS.items():
            cls._cache['bullets'][direction] = pygame.image.load(path).convert_alpha()

        # ========== 场景图片 ==========
        cls._cache['scenes'] = {}
        for scene_key, path in cfg.SCENE_IMAGE_PATHS.items():
            cls._cache['scenes'][scene_key] = pygame.image.load(path).convert_alpha()

        # ========== 其他图片 ==========
        cls._cache['others'] = {}
        for other_key, path in cfg.OTHER_IMAGE_PATHS.items():
            cls._cache['others'][other_key] = pygame.image.load(path).convert_alpha()

        # ========== Home图片 ==========
        cls._cache['home'] = {
            'alive': pygame.image.load(cfg.HOME_IMAGE_PATHS[0]).convert_alpha(),
            'destroyed': pygame.image.load(cfg.HOME_IMAGE_PATHS[1]).convert_alpha(),
        }

    @classmethod
    def get_boom_image(cls):
        return cls._cache.get('boom_dynamic')

    @classmethod
    def get_bullet_images(cls):
        return cls._cache.get('bullets', {})

    @classmethod
    def get_scene_image(cls, scene_key):
        return cls._cache.get('scenes', {}).get(scene_key)

    @classmethod
    def get_other_image(cls, image_key):
        return cls._cache.get('others', {}).get(image_key)

    @classmethod
    def get_home_image(cls, state='alive'):
        """获取 home 图片，state 为 'alive' 或 'destroyed'。"""
        return cls._cache.get('home', {}).get(state)
