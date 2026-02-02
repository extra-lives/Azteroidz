import json
import math
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import pygame


def get_process_ram_mb():
    try:
        import psutil

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            import ctypes.wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.wintypes.DWORD),
                    ("PageFaultCount", ctypes.wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            GetCurrentProcess = kernel32.GetCurrentProcess
            GetCurrentProcess.restype = ctypes.wintypes.HANDLE

            GetProcessMemoryInfo = psapi.GetProcessMemoryInfo
            GetProcessMemoryInfo.argtypes = [
                ctypes.wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                ctypes.wintypes.DWORD,
            ]
            GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            if GetProcessMemoryInfo(GetCurrentProcess(), ctypes.byref(counters), counters.cb):
                return counters.WorkingSetSize / (1024 * 1024)
        except Exception:
            return None
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return rss / (1024 * 1024)
        return rss / 1024
    except Exception:
        return None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIDTH = 1024
HEIGHT = 768
WORLD_WIDTH = 80000
WORLD_HEIGHT = 60000
FPS = 60
CAMERA_ZOOM = 0.5
STAR_PARALLAX = 0.18

SAVE_PATH = "save.json"
SHOOT_SOUND_PATH = os.path.join(BASE_DIR, "assets", "audio", "shoot-default.wav")
EXPLODE_SOUND_PATH = os.path.join(BASE_DIR, "assets", "audio", "explode-default.wav")
ASTEROID_EXPLODE_SOUND_PATH = os.path.join(BASE_DIR, "assets", "audio", "explode-asteroid.wav")
SHIELD_SOUND_PATH = os.path.join(BASE_DIR, "assets", "audio", "shield-default.wav")

SHIP_RADIUS = 12
SHIP_THRUST = 260
SHIP_REVERSE_THRUST = 120
SHIP_BRAKE = 360
SHIP_STOP_DAMP = 6.0
SHIP_TURN_SPEED = 200  # degrees/sec
SHIP_STICK_TURN_SPEED = 320  # degrees/sec (stick aiming)
SHIP_MAX_SPEED = 380

BULLET_SPEED = 520
BULLET_TTL = 3.3
FIRE_COOLDOWN = 0.18
BULLET_HIT_SLOP = 2

ASTEROID_SIZES = {
    4: 110,
    3: 60,
    2: 32,
    1: 10,
}
ASTEROID_SPEED = {
    4: (20, 45),
    3: (30, 70),
    2: (50, 110),
    1: (80, 150),
}
ASTEROID_SHAPE_CACHE = {}

ASTEROID_NEARBY_TARGET = 28
ASTEROID_NEARBY_RADIUS = 1800
ASTEROID_SPAWN_RADIUS = 2000
ASTEROID_SPAWN_BUFFER = 220
ASTEROID_SPAWN_INTERVAL = 1.2
ASTEROID_OFFSCREEN_MARGIN = 220

ENEMY_RADIUS = 12
ENEMY_SCOUT_SPEED = 120
ENEMY_PURSUE_SPEED = 140
ENEMY_TURN_SPEED = 110
ENEMY_PURSUE_RADIUS = 600
ENEMY_FIRE_RANGE = 400
ENEMY_HOLD_RADIUS = 100
ENEMY_HOLD_PLAYER_SPEED = 40
ENEMY_FIRE_COOLDOWN = 1.4
ENEMY_BULLET_SPEED = 400
ENEMY_BULLET_TTL = 2.0
ENEMY_SHIELD_HITS = 1
ELITE_ENEMY_SHIELD_HITS = 2
ELITE_ENEMY_SCORE_BONUS = 100
ELITE_ENEMY_SPEED_MULT = 1.2
ELITE_ENEMY_FIRE_RATE_MULT = 1.2
ELITE_ENEMY_BULLET_SPEED_MULT = 1.2
ELITE_ENEMY_SIZE_MULT = 1.5
ELITE_ENEMY_SPAWN_CHANCE = 0.2
ELITE_ENEMY_OUTER_CHANCE = 0.6
ELITE_ENEMY_OUTER_BAND_FRAC = 0.2
ENEMY_NEARBY_TARGET = 12
ENEMY_NEARBY_RADIUS = 3600
ENEMY_SPAWN_RADIUS = 4000
ENEMY_SPAWN_BUFFER = 1800
ENEMY_OFFSCREEN_MARGIN = 240
ENEMY_DESPAWN_RADIUS = 5200
ENEMY_SPAWN_INTERVAL = 3.2

BOSS_SCALE = 6.0
BOSS_RADIUS = int(SHIP_RADIUS * BOSS_SCALE)
BOSS_PATROL_SPEED = 120
BOSS_TURN_SPEED = 80
BOSS_FIRE_COOLDOWN = 1.6
BOSS_BULLET_SPEED = 380
BOSS_MAX_HP = 1000
BOSS_HIT_DAMAGE = 10
BOSS_FORMATION_BREAK_RADIUS = 750
BOSS_PATROL_NODE_RADIUS = 220
BOSS_SCORE_BONUS = 900

PICKUP_TTL = 15.0
PICKUP_GRID_SPACING = 0.7
PICKUP_RADIUS = 24
CANISTER_RADIUS = 26
CANISTER_HITS = 4
BOOST_MULTIPLIER = 1.5
BOOST_TIME = 6.0
SPREAD_TIME = 7.0
SPREAD_ANGLE = 12
MINE_DROP_COOLDOWN = 0.5
MINE_RADIUS = 32
MINE_BLAST_RADIUS = MINE_RADIUS * 3
MINE_TTL = 60.0
SOUND_NEAR_RADIUS = 600
SOUND_FAR_RADIUS = 2400
STAR_COUNT = 500
FREIGHTER_COUNT = 10
FREIGHTER_SPEED = (70, 110)
FREIGHTER_RADIUS = SHIP_RADIUS * 5
# DualShock 4 mapping (pygame)
JOY_AXIS_LX = 0
JOY_AXIS_LY = 1
JOY_AXIS_RX = 2
JOY_AXIS_RY = 3
JOY_AXIS_LT = 4
JOY_AXIS_RT = 5
JOY_AXIS_DEADZONE = 0.5
D_PAD_UP = 11
D_PAD_DOWN = 12
D_PAD_LEFT = 13
D_PAD_RIGHT = 14
BTN_X = 0
BTN_O = 1
BTN_S = 2
BTN_T = 3
BTN_L3 = 7
BTN_R3 = 8
BTN_L1 = 9
BTN_R1 = 10
BTN_MAP = 15
DAMAGE_POPUP_TTL = 0.75
DAMAGE_POPUP_SPEED = 85
DAMAGE_POPUP_MAX = 35
STOP_THRUSTER_TTL = 0.22
ENEMY_SHARD_TTL = 1.2
ENEMY_SHARD_SPEED = 90
ENEMY_SHARD_MAX = 90
BEACON_OFFSET_MIN = 120
BEACON_OFFSET_MAX = 260
UI_PICKUP_RADIUS = 16
UI_PICKUP_SPACING = 90
UI_PICKUP_TOP_Y = 38


COLORS = {
    "bg": (5, 7, 10),
    "ship": (230, 230, 230),
    "bullet": (255, 240, 120),
    "asteroid": (245, 245, 245),
    "planet": (120, 220, 140),
    "moon": (120, 170, 255),
    "pickup_shield": (120, 200, 255),
    "pickup_rapid": (255, 190, 120),
    "pickup_boost": (255, 170, 90),
    "pickup_spread": (140, 220, 140),
    "pickup_canister": (170, 90, 220),
    "pickup_boost": (170, 90, 220),
    "pickup_mine": (220, 70, 70),
    "mine_core": (255, 170, 80),
    "enemy": (235, 90, 90),
    "enemy_shield": (255, 170, 80),
    "elite_enemy_shield": (220, 160, 255),
    "elite_enemy": (200, 80, 255),
    "boss": (245, 200, 90),
    "boss_shield": (220, 60, 60),
    "freighter": (150, 110, 80),
    "freighter_shield": (120, 160, 200),
    "god_shield": (255, 215, 80),
    "ui": (200, 200, 200),
    "warning": (255, 140, 140),
}


@dataclass(slots=True)
class Asteroid:
    pos: pygame.Vector2
    vel: pygame.Vector2
    size: int
    radius: int
    spin: float
    angle: float
    shape: list


@dataclass(slots=True)
class Pickup:
    kind: str
    pos: pygame.Vector2
    ttl: float
    shell_hp: int = 0


@dataclass(slots=True)
class Enemy:
    pos: pygame.Vector2
    vel: pygame.Vector2
    angle: float
    shield: int
    fire_timer: float
    wander_timer: float
    wander_angle: float
    pursuing: bool = False
    elite: bool = False
    escort: bool = False
    escort_offset: pygame.Vector2 = field(default_factory=pygame.Vector2)


@dataclass(slots=True)
class Boss:
    pos: pygame.Vector2
    vel: pygame.Vector2
    angle: float
    hp: int
    fire_timer: float
    patrol_index: int
    patrol_points: list


@dataclass(slots=True)
class Landmark:
    id: int
    kind: str
    pos: pygame.Vector2
    radius: int
    color: tuple
    parent_id: Optional[int] = None


def wrap_position(pos):
    return pygame.Vector2(pos.x % WORLD_WIDTH, pos.y % WORLD_HEIGHT)


def clamp_position(pos, radius=0):
    return pygame.Vector2(
        max(radius, min(WORLD_WIDTH - radius, pos.x)),
        max(radius, min(WORLD_HEIGHT - radius, pos.y)),
    )


def world_to_screen(world_pos, camera_pos):
    delta = world_pos - camera_pos
    return pygame.Vector2(WIDTH / 2, HEIGHT / 2) + delta * CAMERA_ZOOM


def world_to_screen_parallax(world_pos, camera_pos, parallax):
    delta = world_pos - camera_pos
    return pygame.Vector2(WIDTH / 2, HEIGHT / 2) + delta * parallax


def toroidal_delta_world(a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    if abs(dx) > WORLD_WIDTH / 2:
        dx -= math.copysign(WORLD_WIDTH, dx)
    if abs(dy) > WORLD_HEIGHT / 2:
        dy -= math.copysign(WORLD_HEIGHT, dy)
    return pygame.Vector2(dx, dy)


def prev_pos(pos, vel, dt):
    return pos - vel * dt


def angle_to_vector(angle_deg):
    radians = math.radians(angle_deg)
    return pygame.Vector2(math.cos(radians), math.sin(radians))


def vector_to_angle(vec):
    return math.degrees(math.atan2(vec.y, vec.x))


def turn_towards(current, target, max_turn):
    diff = (target - current + 180) % 360 - 180
    if diff > max_turn:
        return current + max_turn
    if diff < -max_turn:
        return current - max_turn
    return target


def spawn_damage_popup(popups, pool, font, text, world_pos, color):
    if len(popups) >= DAMAGE_POPUP_MAX:
        return
    surface = font.render(text, True, color)
    drift = pygame.Vector2(random.uniform(-20, 20), -DAMAGE_POPUP_SPEED)
    if pool:
        popup = pool.pop()
        popup["pos"].update(world_pos)
        popup["vel"].update(drift)
        popup["ttl"] = DAMAGE_POPUP_TTL
        popup["surface"] = surface
    else:
        popup = {
            "pos": pygame.Vector2(world_pos),
            "vel": drift,
            "ttl": DAMAGE_POPUP_TTL,
            "surface": surface,
        }
    popups.append(popup)


def remove_enemy(enemies, enemy, boss_escorts):
    if enemy in enemies:
        enemies.remove(enemy)
    if boss_escorts is not None and enemy in boss_escorts:
        boss_escorts.remove(enemy)


def make_beacon_id(rng):
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    digits = "23456789"
    part_a = "".join(rng.choice(letters) for _ in range(2))
    part_b = "".join(rng.choice(digits) for _ in range(2))
    return f"{part_a}-{part_b}"


def scale_color(color, alpha):
    return (
        max(0, min(255, int(color[0] * alpha))),
        max(0, min(255, int(color[1] * alpha))),
        max(0, min(255, int(color[2] * alpha))),
    )


def draw_beacon(surface, pos, color):
    size = 12
    ring = []
    for i in range(6):
        angle = math.radians(60 * i + 30)
        ring.append((pos.x + math.cos(angle) * size, pos.y + math.sin(angle) * size))
    pygame.draw.polygon(surface, color, ring, 2)
    pygame.draw.circle(surface, color, (int(pos.x), int(pos.y)), 4, 1)
    pygame.draw.line(surface, color, (pos.x, pos.y - size - 6), (pos.x, pos.y + size + 6), 1)


def spawn_enemy_shards(shards, pool, pos, angle, color=COLORS["enemy"]):
    if len(shards) >= ENEMY_SHARD_MAX:
        return
    base = [
        pygame.Vector2(10, 0).rotate(angle),
        pygame.Vector2(-8, -6).rotate(angle),
        pygame.Vector2(-8, 6).rotate(angle),
    ]
    for i in range(3):
        start = pos + base[i]
        end = pos + base[(i + 1) % 3]
        direction = (end - start).normalize()
        drift = direction.rotate(random.uniform(-30, 30)) * random.uniform(ENEMY_SHARD_SPEED * 0.6, ENEMY_SHARD_SPEED)
        if pool:
            shard = pool.pop()
            shard["start"].update(start)
            shard["end"].update(end)
            shard["vel"].update(drift)
            shard["ttl"] = ENEMY_SHARD_TTL
        else:
            shard = {
                "start": pygame.Vector2(start),
                "end": pygame.Vector2(end),
                "vel": drift,
                "ttl": ENEMY_SHARD_TTL,
            }
        shard["color"] = color
        shards.append(shard)


def seed_from_time():
    return int(time.time()) & 0xFFFFFFFF


def make_asteroid_shape(rng, radius):
    points = []
    count = rng.randint(8, 13)
    for i in range(count):
        angle = (math.tau / count) * i
        jitter = rng.uniform(0.65, 1.2)
        r = radius * jitter
        points.append((math.cos(angle) * r, math.sin(angle) * r))
    return points


def get_asteroid_shape(rng, radius):
    cached = ASTEROID_SHAPE_CACHE.get(radius)
    if cached is None:
        cached = make_asteroid_shape(rng, radius)
        ASTEROID_SHAPE_CACHE[radius] = cached
    return cached


def spawn_asteroid(rng, size, avoid_center=True):
    radius = int(ASTEROID_SIZES[size] * rng.uniform(0.75, 1.35))
    if avoid_center:
        while True:
            pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
            if pos.distance_to((WORLD_WIDTH / 2, WORLD_HEIGHT / 2)) > 240:
                break
    else:
        pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))

    speed_min, speed_max = ASTEROID_SPEED[size]
    velocity = angle_to_vector(rng.uniform(0, 360)) * rng.uniform(speed_min, speed_max)
    spin = rng.uniform(-40, 40)
    shape = get_asteroid_shape(rng, radius)
    return Asteroid(
        pos=pos,
        vel=velocity,
        size=size,
        radius=radius,
        spin=spin,
        angle=rng.uniform(0, 360),
        shape=shape,
    )


def spawn_asteroid_near(rng, size, center):
    radius = ASTEROID_SIZES[size]
    view_half_w = WIDTH / (2 * CAMERA_ZOOM) + ASTEROID_OFFSCREEN_MARGIN
    view_half_h = HEIGHT / (2 * CAMERA_ZOOM) + ASTEROID_OFFSCREEN_MARGIN
    for _ in range(60):
        offset = pygame.Vector2(rng.uniform(ASTEROID_SPAWN_BUFFER, ASTEROID_SPAWN_RADIUS), 0).rotate(
            rng.uniform(0, 360)
        )
        pos = center + offset
        if not (0 <= pos.x <= WORLD_WIDTH and 0 <= pos.y <= WORLD_HEIGHT):
            continue
        if abs(pos.x - center.x) < view_half_w and abs(pos.y - center.y) < view_half_h:
            continue
        asteroid = spawn_asteroid(rng, size, avoid_center=False)
        asteroid.pos = pos
        return asteroid
    asteroid = spawn_asteroid(rng, size, avoid_center=False)
    asteroid.pos = center + pygame.Vector2(ASTEROID_SPAWN_RADIUS, 0)
    return asteroid


def spawn_pickup(rng):
    kind = rng.choice(["shield", "spread", "mine", "boost_canister"])
    pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
    shell_hp = CANISTER_HITS if kind == "boost_canister" else 0
    return Pickup(kind=kind, pos=pos, ttl=PICKUP_TTL, shell_hp=shell_hp)


def spawn_enemy(rng, elite=False):
    pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
    angle = rng.uniform(0, 360)
    fire_rate_mult = ELITE_ENEMY_FIRE_RATE_MULT if elite else 1.0
    return Enemy(
        pos=pos,
        vel=pygame.Vector2(0, 0),
        angle=angle,
        shield=ELITE_ENEMY_SHIELD_HITS if elite else ENEMY_SHIELD_HITS,
        fire_timer=rng.uniform(0, ENEMY_FIRE_COOLDOWN / fire_rate_mult),
        wander_timer=rng.uniform(0.5, 1.5),
        wander_angle=angle,
        elite=elite,
    )


def enemy_spawn_clear(pos, landmarks, radius=ENEMY_RADIUS):
    for landmark in landmarks:
        if landmark.kind not in ("planet", "moon"):
            continue
        if (pos - landmark.pos).length() < landmark.radius + radius:
            return False
    return True


def elite_spawn_chance(center_x):
    band = WORLD_WIDTH * ELITE_ENEMY_OUTER_BAND_FRAC
    if center_x <= band or center_x >= WORLD_WIDTH - band:
        return ELITE_ENEMY_OUTER_CHANCE
    return 0.0


def spawn_enemy_near(rng, center, landmarks, elite=False):
    view_half_w = WIDTH / (2 * CAMERA_ZOOM) + ENEMY_OFFSCREEN_MARGIN
    view_half_h = HEIGHT / (2 * CAMERA_ZOOM) + ENEMY_OFFSCREEN_MARGIN
    band = WORLD_WIDTH * ELITE_ENEMY_OUTER_BAND_FRAC
    for _ in range(60):
        offset = pygame.Vector2(rng.uniform(ENEMY_SPAWN_BUFFER, ENEMY_SPAWN_RADIUS), 0).rotate(
            rng.uniform(0, 360)
        )
        pos = center + offset
        if not (0 <= pos.x <= WORLD_WIDTH and 0 <= pos.y <= WORLD_HEIGHT):
            continue
        if abs(pos.x - center.x) < view_half_w and abs(pos.y - center.y) < view_half_h:
            continue
        if elite and not (pos.x <= band or pos.x >= WORLD_WIDTH - band):
            continue
        radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if elite else 1.0)
        if not enemy_spawn_clear(pos, landmarks, radius):
            continue
        enemy = spawn_enemy(rng, elite=elite)
        enemy.pos = pos
        return enemy
    enemy = spawn_enemy(rng, elite=elite)
    for _ in range(60):
        pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
        radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if elite else 1.0)
        if elite and not (pos.x <= band or pos.x >= WORLD_WIDTH - band):
            continue
        if enemy_spawn_clear(pos, landmarks, radius):
            enemy.pos = pos
            return enemy
    final_radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if elite else 1.0)
    enemy.pos = clamp_position(center + pygame.Vector2(ENEMY_SPAWN_RADIUS, 0), radius=final_radius)
    return enemy


def boss_patrol_points(margin):
    return [
        pygame.Vector2(margin, margin),
        pygame.Vector2(WORLD_WIDTH * 0.5, margin),
        pygame.Vector2(WORLD_WIDTH - margin, margin),
        pygame.Vector2(WORLD_WIDTH - margin, WORLD_HEIGHT * 0.5),
        pygame.Vector2(WORLD_WIDTH - margin, WORLD_HEIGHT - margin),
        pygame.Vector2(WORLD_WIDTH * 0.5, WORLD_HEIGHT - margin),
        pygame.Vector2(margin, WORLD_HEIGHT - margin),
        pygame.Vector2(margin, WORLD_HEIGHT * 0.5),
    ]


def spawn_boss_with_escorts(seed):
    rng = random.Random(seed ^ 0xB055B055)
    margin = max(BOSS_RADIUS * 2.0, 900)
    patrol_points = boss_patrol_points(margin)
    start_index = rng.randrange(len(patrol_points))
    start_pos = pygame.Vector2(patrol_points[start_index])
    next_index = (start_index + 1) % len(patrol_points)
    to_next = patrol_points[next_index] - start_pos
    angle = vector_to_angle(to_next) if to_next.length_squared() > 0 else 0.0
    boss = Boss(
        pos=start_pos,
        vel=pygame.Vector2(0, 0),
        angle=angle,
        hp=BOSS_MAX_HP,
        fire_timer=rng.uniform(0, BOSS_FIRE_COOLDOWN),
        patrol_index=next_index,
        patrol_points=patrol_points,
    )

    elite_offsets = [
        pygame.Vector2(BOSS_RADIUS * 1.8, -BOSS_RADIUS * 0.8),
        pygame.Vector2(BOSS_RADIUS * 1.8, BOSS_RADIUS * 0.8),
        pygame.Vector2(-BOSS_RADIUS * 1.1, -BOSS_RADIUS * 1.4),
        pygame.Vector2(-BOSS_RADIUS * 1.1, BOSS_RADIUS * 1.4),
    ]
    regular_offsets = [
        pygame.Vector2(BOSS_RADIUS * 2.6, 0.0),
        pygame.Vector2(BOSS_RADIUS * 0.4, -BOSS_RADIUS * 2.2),
        pygame.Vector2(BOSS_RADIUS * 0.4, BOSS_RADIUS * 2.2),
        pygame.Vector2(-BOSS_RADIUS * 2.0, 0.0),
        pygame.Vector2(-BOSS_RADIUS * 0.6, -BOSS_RADIUS * 2.4),
        pygame.Vector2(-BOSS_RADIUS * 0.6, BOSS_RADIUS * 2.4),
    ]

    escorts = []
    for offset in elite_offsets:
        enemy = spawn_enemy(rng, elite=True)
        enemy.escort = True
        enemy.escort_offset = pygame.Vector2(offset)
        enemy.pos = boss.pos + offset.rotate(boss.angle)
        enemy.angle = boss.angle
        escorts.append(enemy)
    for offset in regular_offsets:
        enemy = spawn_enemy(rng, elite=False)
        enemy.escort = True
        enemy.escort_offset = pygame.Vector2(offset)
        enemy.pos = boss.pos + offset.rotate(boss.angle)
        enemy.angle = boss.angle
        escorts.append(enemy)

    return boss, escorts


def segment_hits_circle(rel_prev, rel_curr, radius):
    radius_sq = radius * radius
    if rel_prev.length_squared() <= radius_sq or rel_curr.length_squared() <= radius_sq:
        return True
    seg = rel_curr - rel_prev
    seg_len_sq = seg.length_squared()
    if seg_len_sq == 0:
        return False
    t = max(0.0, min(1.0, -rel_prev.dot(seg) / seg_len_sq))
    closest = rel_prev + seg * t
    return closest.length_squared() <= radius_sq


def moving_circle_hit(prev_a, curr_a, prev_b, curr_b, radius):
    rel_prev = prev_a - prev_b
    rel_curr = curr_a - curr_b
    return segment_hits_circle(rel_prev, rel_curr, radius)


def generate_landmarks(seed):
    rng = random.Random(seed)
    landmarks = []
    planet_count = 12
    planets = []
    planet_id = 0
    for _ in range(planet_count):
        radius = rng.randint(1760, 2880)
        placed = False
        for _ in range(60):
            pos = pygame.Vector2(
                rng.uniform(radius, WORLD_WIDTH - radius),
                rng.uniform(radius, WORLD_HEIGHT - radius),
            )
            if all((pos - p.pos).length() >= p.radius + radius + 1000 for p in planets):
                planets.append(
                    Landmark(
                        id=planet_id,
                        kind="planet",
                        pos=pos,
                        radius=radius,
                        color=COLORS["planet"],
                    )
                )
                planet_id += 1
                placed = True
                break
        if not placed:
            continue
    landmarks.extend(planets)
    moon_id = 0
    moons = []
    for parent in planets:
        size = rng.randint(int(parent.radius * 0.16), int(parent.radius * 0.4))
        min_orbit = parent.radius + size + 120
        max_orbit = parent.radius + size + 520
        placed = False
        for _ in range(50):
            offset = pygame.Vector2(rng.uniform(min_orbit, max_orbit), 0).rotate(rng.uniform(0, 360))
            moon_pos = parent.pos + offset
            if not (size <= moon_pos.x <= WORLD_WIDTH - size and size <= moon_pos.y <= WORLD_HEIGHT - size):
                continue
            if any((moon_pos - p.pos).length() < p.radius + size + 140 for p in planets):
                continue
            if any((moon_pos - m.pos).length() < m.radius + size + 80 for m in moons):
                continue
            landmark = Landmark(
                id=moon_id,
                kind="moon",
                pos=moon_pos,
                radius=size,
                color=COLORS["moon"],
                parent_id=parent.id,
            )
            moons.append(landmark)
            landmarks.append(landmark)
            moon_id += 1
            placed = True
            break
        if not placed:
            continue
    return landmarks


def generate_pickups(seed):
    rng = random.Random(seed ^ 0x5F3759DF)
    pickups = []
    screen_w = WIDTH / CAMERA_ZOOM
    screen_h = HEIGHT / CAMERA_ZOOM
    cell_w = screen_w * PICKUP_GRID_SPACING
    cell_h = screen_h * PICKUP_GRID_SPACING
    x = 0.0
    while x < WORLD_WIDTH:
        y = 0.0
        while y < WORLD_HEIGHT:
            pos = pygame.Vector2(
                min(WORLD_WIDTH - 1, x + rng.uniform(0, cell_w)),
                min(WORLD_HEIGHT - 1, y + rng.uniform(0, cell_h)),
            )
            pickups.append(spawn_pickup(rng))
            pickups[-1].pos = pos
            y += cell_h
        x += cell_w
    return pickups


def generate_enemies(seed, center, landmarks):
    rng = random.Random(seed ^ 0x1EADBEEF)
    enemies = []
    for _ in range(ENEMY_NEARBY_TARGET):
        chance = elite_spawn_chance(center.x)
        enemies.append(spawn_enemy_near(rng, center, landmarks, elite=rng.random() < chance))
    return enemies


def generate_starfield(seed):
    rng = random.Random(seed ^ 0xA5A5A5A5)
    surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for _ in range(STAR_COUNT):
        brightness = rng.randint(35, 95)
        size = 1 if rng.random() < 0.9 else 2
        x = rng.randrange(0, WIDTH)
        y = rng.randrange(0, HEIGHT)
        color = (brightness, brightness, brightness)
        pygame.draw.circle(surface, color, (x, y), size)
    return {"surface": surface, "width": WIDTH, "height": HEIGHT}


def pick_nearest_moon(planet, moons):
    best = None
    best_dist_sq = None
    for moon in moons:
        dist_sq = (moon.pos - planet.pos).length_squared()
        if best_dist_sq is None or dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best = moon
    return best


def generate_freighters(seed, landmarks):
    rng = random.Random(seed ^ 0x7F4A7C15)
    planets = [l for l in landmarks if l.kind == "planet"]
    moons = [l for l in landmarks if l.kind == "moon"]
    if len(planets) < 2 or len(moons) < 2:
        return []
    freighters = []
    used_pairs = set()
    attempts = 0
    max_attempts = FREIGHTER_COUNT * 12
    while len(freighters) < FREIGHTER_COUNT and attempts < max_attempts:
        attempts += 1
        origin, dest = rng.sample(planets, 2)
        origin_moon = pick_nearest_moon(origin, moons)
        dest_moon = pick_nearest_moon(dest, moons)
        if not origin_moon or not dest_moon:
            continue
        pair = tuple(sorted((origin_moon.id, dest_moon.id)))
        if pair in used_pairs:
            continue
        used_pairs.add(pair)
        pos = pygame.Vector2(origin_moon.pos)
        speed = rng.uniform(*FREIGHTER_SPEED)
        freighters.append(
            {
                "pos": pos,
                "vel": pygame.Vector2(0, 0),
                "angle": rng.uniform(0, 360),
                "from": pygame.Vector2(origin_moon.pos),
                "to": pygame.Vector2(dest_moon.pos),
                "target": pygame.Vector2(dest_moon.pos),
                "speed": speed,
            }
        )
    return freighters


def new_world(seed):
    rng = random.Random(seed)
    asteroids = []
    for _ in range(120):
        size = 4 if rng.random() < 0.12 else 3
        asteroids.append(spawn_asteroid(rng, size))
    pickups = generate_pickups(seed)
    center = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
    landmarks = generate_landmarks(seed)
    enemies = generate_enemies(seed, center, landmarks)
    boss, boss_escorts = spawn_boss_with_escorts(seed)
    enemies.extend(boss_escorts)
    stars = generate_starfield(seed)
    freighters = generate_freighters(seed, landmarks)
    return asteroids, pickups, enemies, landmarks, stars, freighters, boss, boss_escorts


def load_state():
    if not os.path.exists(SAVE_PATH):
        return None
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def serialize_vec(vec):
    return [vec.x, vec.y]


def deserialize_vec(value):
    return pygame.Vector2(value[0], value[1])


def serialize_asteroid(asteroid):
    return {
        "pos": serialize_vec(asteroid.pos),
        "vel": serialize_vec(asteroid.vel),
        "size": asteroid.size,
        "radius": asteroid.radius,
        "spin": asteroid.spin,
        "angle": asteroid.angle,
        "shape": asteroid.shape,
    }


def deserialize_asteroid(data):
    radius = data["radius"]
    cached = ASTEROID_SHAPE_CACHE.get(radius)
    if cached is None:
        rng = random.Random(radius * 9176)
        cached = make_asteroid_shape(rng, radius)
        ASTEROID_SHAPE_CACHE[radius] = cached
    return Asteroid(
        pos=deserialize_vec(data["pos"]),
        vel=deserialize_vec(data["vel"]),
        size=data["size"],
        radius=radius,
        spin=data["spin"],
        angle=data["angle"],
        shape=cached,
    )


def serialize_pickup(pickup):
    return {
        "kind": pickup.kind,
        "pos": serialize_vec(pickup.pos),
        "ttl": pickup.ttl,
        "shell_hp": pickup.shell_hp,
    }


def deserialize_pickup(data):
    kind = data["kind"]
    shell_hp = data.get("shell_hp", CANISTER_HITS if kind == "boost_canister" else 0)
    return Pickup(kind=kind, pos=deserialize_vec(data["pos"]), ttl=data["ttl"], shell_hp=shell_hp)


def draw_vector_shape(surface, pos, angle, points, color, width=2):
    rotated = []
    for x, y in points:
        vec = pygame.Vector2(x, y).rotate(angle) * CAMERA_ZOOM
        rotated.append((pos.x + vec.x, pos.y + vec.y))
    pygame.draw.lines(surface, color, True, rotated, width)


def draw_ship(surface, pos, angle, color, scale=1.0):
    render_radius = SHIP_RADIUS * CAMERA_ZOOM * scale
    nose = pygame.Vector2(render_radius * 1.2, 0).rotate(angle)
    left = pygame.Vector2(-render_radius, -render_radius * 0.7).rotate(angle)
    right = pygame.Vector2(-render_radius, render_radius * 0.7).rotate(angle)
    points = [
        (pos.x + nose.x, pos.y + nose.y),
        (pos.x + left.x, pos.y + left.y),
        (pos.x + right.x, pos.y + right.y),
    ]
    pygame.draw.lines(surface, color, True, points, 2)


def draw_boss(surface, pos, angle, color, scale=1.0):
    render_radius = SHIP_RADIUS * CAMERA_ZOOM * scale
    front = render_radius * 1.4
    rear = render_radius * 1.05
    wing = render_radius * 0.85
    peak_offset = render_radius * 0.28
    peak_depth = render_radius * 0.22
    points = [
        (front, -peak_offset),
        (front - peak_depth, 0),
        (front, peak_offset),
        (-rear, wing),
        (-rear * 0.7, 0),
        (-rear, -wing),
    ]
    draw_vector_shape(surface, pos, angle, points, color, 3)


def draw_freighter(surface, pos, angle, color):
    length = FREIGHTER_RADIUS * CAMERA_ZOOM * 2.2
    half_w = FREIGHTER_RADIUS * CAMERA_ZOOM * 0.8
    nose = FREIGHTER_RADIUS * CAMERA_ZOOM * 0.5
    tail = FREIGHTER_RADIUS * CAMERA_ZOOM * 1.1
    points = [
        (length * 0.5, 0),
        (nose, half_w),
        (-tail, half_w * 0.8),
        (-length * 0.5, 0),
        (-tail, -half_w * 0.8),
        (nose, -half_w),
    ]
    draw_vector_shape(surface, pos, angle, points, color, 4)
    cargo_radius = max(2, int(FREIGHTER_RADIUS * CAMERA_ZOOM * 0.18))
    cargo_x = [-tail * 0.3, 0.0]
    cargo_y = [-half_w * 0.25, half_w * 0.25]
    cargo_color = (190, 150, 100)
    for x in cargo_x:
        for y in cargo_y:
            cargo_pos = pos + pygame.Vector2(x, y).rotate(angle)
            pygame.draw.circle(surface, cargo_color, (int(cargo_pos.x), int(cargo_pos.y)), cargo_radius, 1)


def draw_edge_arrow(surface, direction, color):
    if direction.length_squared() == 0:
        return
    dir_norm = direction.normalize()
    margin = 18
    half_w = WIDTH / 2 - margin
    half_h = HEIGHT / 2 - margin
    tx = float("inf") if dir_norm.x == 0 else half_w / abs(dir_norm.x)
    ty = float("inf") if dir_norm.y == 0 else half_h / abs(dir_norm.y)
    t = min(tx, ty)
    tip = pygame.Vector2(WIDTH / 2, HEIGHT / 2) + dir_norm * t
    size = 14
    left = tip - dir_norm * size + dir_norm.rotate(90) * (size * 0.6)
    right = tip - dir_norm * size + dir_norm.rotate(-90) * (size * 0.6)
    pygame.draw.polygon(surface, color, [(tip.x, tip.y), (left.x, left.y), (right.x, right.y)], 2)


def draw_thruster(surface, pos, angle, color, scale=1.0, back_mult=1.7):
    render_radius = SHIP_RADIUS * CAMERA_ZOOM
    back = pygame.Vector2(-render_radius * back_mult, 0).rotate(angle)
    perp = pygame.Vector2(0, render_radius * 0.35).rotate(angle)
    base = pos + back
    lengths = [render_radius * 1.8 * scale, render_radius * 1.3 * scale, render_radius * 0.9 * scale]
    offsets = [0.0, render_radius * 0.22, -render_radius * 0.22]
    for length, offset in zip(lengths, offsets):
        start = base + perp * offset
        end = start + pygame.Vector2(-length, 0).rotate(angle)
        pygame.draw.line(surface, color, start, end, 2)


def draw_stop_thruster(surface, pos, angle, color, side="both"):
    render_radius = SHIP_RADIUS * CAMERA_ZOOM
    side_vec = pygame.Vector2(0, render_radius * 1.35).rotate(angle)
    forward = pygame.Vector2(render_radius * 1.1, 0).rotate(angle)
    lengths = [render_radius * 0.75, render_radius * 0.5]
    offsets = [0.0, render_radius * 0.2]
    for length, offset in zip(lengths, offsets):
        left_start = pos - side_vec + forward * offset
        right_start = pos + side_vec + forward * offset
        left_end = left_start - side_vec.normalize() * length
        right_end = right_start + side_vec.normalize() * length
        if side in ("left", "both"):
            pygame.draw.line(surface, color, left_start, left_end, 2)
        if side in ("right", "both"):
            pygame.draw.line(surface, color, right_start, right_end, 2)


def draw_mine(surface, pos, radius, color, core_color):
    points = []
    for i in range(5):
        angle = math.radians(72 * i - 90)
        points.append((pos.x + math.cos(angle) * radius, pos.y + math.sin(angle) * radius))
    pygame.draw.polygon(surface, color, points, 2)
    pygame.draw.circle(surface, core_color, (int(pos.x), int(pos.y)), max(2, int(radius * 0.35)), 0)


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.joystick.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = screen.get_size()
    pygame.display.set_caption("Seeded Asteroids - Prototype")
    pygame.event.clear()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 18)
    debug_font = pygame.font.SysFont("Consolas", 16)
    popup_font = pygame.font.SysFont("Consolas", 16, bold=True)
    game_over_font_big = pygame.font.SysFont("Consolas", 64, bold=True)
    game_over_font_med = pygame.font.SysFont("Consolas", 32)
    game_over_font_small = pygame.font.SysFont("Consolas", 20)
    shoot_sound = None
    explode_sound = None
    explode_channel = None
    asteroid_explode_sound = None
    asteroid_explode_channel = None
    shield_sound = None
    if pygame.mixer.get_init() is None:
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
    if pygame.mixer.get_init():
        pygame.mixer.set_num_channels(16)
    if pygame.mixer.get_init() and os.path.exists(SHOOT_SOUND_PATH):
        try:
            shoot_sound = pygame.mixer.Sound(SHOOT_SOUND_PATH)
            shoot_sound.set_volume(0.6)
        except pygame.error:
            shoot_sound = None
    if pygame.mixer.get_init() and os.path.exists(EXPLODE_SOUND_PATH):
        try:
            explode_sound = pygame.mixer.Sound(EXPLODE_SOUND_PATH)
            explode_sound.set_volume(1.0)
            explode_channel = pygame.mixer.Channel(1)
        except pygame.error:
            explode_sound = None
            explode_channel = None
    if pygame.mixer.get_init() and os.path.exists(SHIELD_SOUND_PATH):
        try:
            shield_sound = pygame.mixer.Sound(SHIELD_SOUND_PATH)
            shield_sound.set_volume(0.8)
        except pygame.error:
            shield_sound = None
    if pygame.mixer.get_init() and os.path.exists(ASTEROID_EXPLODE_SOUND_PATH):
        try:
            asteroid_explode_sound = pygame.mixer.Sound(ASTEROID_EXPLODE_SOUND_PATH)
            asteroid_explode_sound.set_volume(0.9)
            asteroid_explode_channel = pygame.mixer.Channel(2)
        except pygame.error:
            asteroid_explode_sound = None
            asteroid_explode_channel = None

    def attenuate_volume(world_pos, base_volume=1.0):
        if world_pos is None:
            return base_volume
        dist = (world_pos - ship_pos).length()
        if dist <= SOUND_NEAR_RADIUS:
            return base_volume
        if dist >= SOUND_FAR_RADIUS:
            return 0.0
        t = (SOUND_FAR_RADIUS - dist) / (SOUND_FAR_RADIUS - SOUND_NEAR_RADIUS)
        return base_volume * t

    def play_explode_sound(world_pos=None):
        if explode_sound:
            volume = attenuate_volume(world_pos, 1.0)
            if volume <= 0.0:
                return
            if explode_channel:
                explode_channel.set_volume(volume)
                explode_channel.play(explode_sound)
            else:
                channel = explode_sound.play()
                if channel:
                    channel.set_volume(volume)

    def play_asteroid_explode_sound():
        return
    def play_shield_sound():
        if shield_sound:
            shield_sound.play()
    joystick = None
    joy_name = "none"
    joy_axes = 0
    joy_buttons = 0
    joy_hats = 0
    show_gamepad_debug = False
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        joy_name = joystick.get_name()
        joy_axes = joystick.get_numaxes()
        joy_buttons = joystick.get_numbuttons()
        joy_hats = joystick.get_numhats()

    seed = seed_from_time()
    asteroids, pickups, enemies, landmarks, stars, freighters, boss, boss_escorts = new_world(seed)

    ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
    ship_vel = pygame.Vector2(0, 0)
    ship_angle = -90

    bullets = []
    enemy_bullets = []
    bullet_pool = []
    enemy_bullet_pool = []
    damage_popups = []
    damage_popup_pool = []
    beacons = {}
    enemy_shards = []
    enemy_shard_pool = []
    mines = []
    fire_timer = 0.0
    score = 0
    lives = 3
    game_over = False
    last_death_cause = None

    shield_time = 10.0
    shield_size_mult = 3.0
    shield_stock = 0
    rapid_time = 0.0
    rapid_stock = 0
    spread_time = 0.0
    spread_stock = 0
    mine_stock = 0
    boost_time = 0.0
    boost_stock = 0
    mine_cooldown = 0.0
    asteroid_spawn_timer = 0.0
    enemy_spawn_timer = 0.0
    thrusting_render = False
    stopping_render = False
    stop_thruster_timer = 0.0
    stop_thruster_held = False
    stop_thruster_side = "both"
    show_map = False
    discovered_planets = set()
    god_mode = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        ship_prev = pygame.Vector2(ship_pos)
        shield_prev = shield_time

        for event in pygame.event.get([pygame.QUIT, pygame.KEYDOWN, pygame.JOYBUTTONDOWN]):
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    show_gamepad_debug = not show_gamepad_debug
                elif event.key == pygame.K_F3:
                    play_explode_sound(ship_pos)
                elif event.key == pygame.K_m:
                    show_map = not show_map
                elif event.key == pygame.K_F2:
                    god_mode = not god_mode
                    if god_mode:
                        shield_stock += 4
                        rapid_stock += 4
                        spread_stock += 4
                        mine_stock += 4
                        boost_stock += 4
                elif event.key == pygame.K_1 and not game_over:
                    if shield_stock > 0 and shield_time <= 0:
                        shield_stock -= 1
                        shield_time = 8.0
                        shield_size_mult = 1.0
                        play_shield_sound()
                elif event.key == pygame.K_3 and not game_over:
                    if spread_stock > 0 and spread_time <= 0:
                        spread_stock -= 1
                        spread_time = SPREAD_TIME
                elif event.key == pygame.K_4 and not game_over:
                    if mine_stock > 0 and mine_cooldown <= 0:
                        mines.append({"pos": pygame.Vector2(ship_pos), "ttl": MINE_TTL})
                        mine_stock -= 1
                        mine_cooldown = MINE_DROP_COOLDOWN
                elif event.key == pygame.K_5 and not game_over:
                    if rapid_stock > 0 and rapid_time <= 0:
                        rapid_stock -= 1
                        rapid_time = 7.0
                elif event.key == pygame.K_2 and not game_over:
                    if boost_stock > 0 and boost_time <= 0:
                        boost_stock -= 1
                        boost_time = BOOST_TIME
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == BTN_MAP:
                    show_map = not show_map
                elif event.button == BTN_S and not game_over:
                    if shield_stock > 0 and shield_time <= 0:
                        shield_stock -= 1
                        shield_time = 8.0
                        shield_size_mult = 1.0
                        play_shield_sound()
                elif event.button == BTN_T and not game_over:
                    if boost_stock > 0 and boost_time <= 0:
                        boost_stock -= 1
                        boost_time = BOOST_TIME
                elif event.button == BTN_O and not game_over:
                    if spread_stock > 0 and spread_time <= 0:
                        spread_stock -= 1
                        spread_time = SPREAD_TIME
                elif event.button == BTN_L3 and not game_over:
                    if mine_stock > 0 and mine_cooldown <= 0:
                        mines.append({"pos": pygame.Vector2(ship_pos), "ttl": MINE_TTL})
                        mine_stock -= 1
                        mine_cooldown = MINE_DROP_COOLDOWN

        keys = pygame.key.get_pressed()
        if joystick:
            pygame.event.pump()
        if keys[pygame.K_ESCAPE]:
            running = False

        if show_map:
            screen.fill(COLORS["bg"])
            margin = 80
            map_w = WIDTH - margin * 2
            map_h = HEIGHT - margin * 2
            map_rect = pygame.Rect(margin, margin, map_w, map_h)
            pygame.draw.rect(screen, COLORS["ui"], map_rect, 2)
            map_scale_x = map_rect.width / WORLD_WIDTH
            map_scale_y = map_rect.height / WORLD_HEIGHT
            map_scale = min(map_scale_x, map_scale_y)
            for landmark in landmarks:
                kind = landmark.kind
                if kind == "planet":
                    color = COLORS["planet"]
                elif kind == "moon":
                    if landmark.parent_id not in discovered_planets:
                        continue
                    color = COLORS["moon"]
                else:
                    continue
                map_x = map_rect.x + (landmark.pos.x / WORLD_WIDTH) * map_rect.width
                map_y = map_rect.y + (landmark.pos.y / WORLD_HEIGHT) * map_rect.height
                map_radius = max(1, int(landmark.radius * map_scale))
                pygame.draw.circle(screen, color, (int(map_x), int(map_y)), map_radius, 1)
                if kind == "planet" and landmark.id in beacons:
                    beacon = beacons[landmark.id]
                    label = font.render(beacon["code"], True, COLORS["ui"])
                    screen.blit(label, (map_x + 6, map_y - 6))
            for freighter in freighters:
                map_x = map_rect.x + (freighter["pos"].x / WORLD_WIDTH) * map_rect.width
                map_y = map_rect.y + (freighter["pos"].y / WORLD_HEIGHT) * map_rect.height
                pygame.draw.circle(screen, COLORS["freighter"], (int(map_x), int(map_y)), 3, 0)
            if boss:
                map_x = map_rect.x + (boss.pos.x / WORLD_WIDTH) * map_rect.width
                map_y = map_rect.y + (boss.pos.y / WORLD_HEIGHT) * map_rect.height
                pygame.draw.circle(screen, COLORS["boss"], (int(map_x), int(map_y)), 6, 0)
                pygame.draw.circle(screen, COLORS["boss_shield"], (int(map_x), int(map_y)), 9, 1)
            map_x = map_rect.x + (ship_pos.x / WORLD_WIDTH) * map_rect.width
            map_y = map_rect.y + (ship_pos.y / WORLD_HEIGHT) * map_rect.height
            pygame.draw.circle(screen, COLORS["pickup_shield"], (int(map_x), int(map_y)), 5, 0)
            title = font.render("Map - press M to close", True, COLORS["ui"])
            screen.blit(title, (WIDTH / 2 - title.get_width() / 2, 24))
            pygame.display.flip()
            continue

        if keys[pygame.K_n]:
            seed = seed_from_time()
            asteroids, pickups, enemies, landmarks, stars, freighters, boss, boss_escorts = new_world(seed)
            bullets = []
            enemy_bullets = []
            bullet_pool = []
            enemy_bullet_pool = []
            damage_popups = []
            damage_popup_pool = []
            beacons = {}
            enemy_shards = []
            enemy_shard_pool = []
            mines = []
            ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
            ship_vel = pygame.Vector2(0, 0)
            ship_angle = -90
            score = 0
            lives = 3
            shield_time = 10.0
            shield_size_mult = 3.0
            shield_stock = 0
            rapid_time = 0.0
            rapid_stock = 0
            spread_time = 0.0
            spread_stock = 0
            mine_stock = 0
            boost_time = 0.0
            boost_stock = 0
            mine_cooldown = 0.0
            game_over = False
            last_death_cause = None
            discovered_planets = set()

        if keys[pygame.K_F5]:
            state = {
                "seed": seed,
                "player": {
                    "pos": serialize_vec(ship_pos),
                    "vel": serialize_vec(ship_vel),
                    "angle": ship_angle,
                    "score": score,
                    "lives": lives,
                    "shield_time": shield_time,
                    "shield_stock": shield_stock,
                    "rapid_time": rapid_time,
                    "rapid_stock": rapid_stock,
                    "spread_time": spread_time,
                    "spread_stock": spread_stock,
                    "mine_stock": mine_stock,
                    "boost_time": boost_time,
                    "boost_stock": boost_stock,
                },
                "asteroids": [serialize_asteroid(a) for a in asteroids],
                "pickups": [serialize_pickup(p) for p in pickups],
                "discovered_planets": sorted(discovered_planets),
            }
            save_state(state)

        if keys[pygame.K_F6]:
            data = load_state()
            if data:
                seed = data["seed"]
                asteroids = [deserialize_asteroid(a) for a in data["asteroids"]]
                pickups = [deserialize_pickup(p) for p in data["pickups"]]
                bullet_pool = []
                enemy_bullet_pool = []
                damage_popups = []
                damage_popup_pool = []
                beacons = {}
                enemy_shards = []
                enemy_shard_pool = []
                mines = []
                landmarks = generate_landmarks(seed)
                enemies = generate_enemies(seed, pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2), landmarks)
                boss, boss_escorts = spawn_boss_with_escorts(seed)
                enemies.extend(boss_escorts)
                stars = generate_starfield(seed)
                freighters = generate_freighters(seed, landmarks)
                player = data["player"]
                ship_pos = deserialize_vec(player["pos"])
                ship_vel = deserialize_vec(player["vel"])
                ship_angle = player["angle"]
                score = player["score"]
                lives = player["lives"]
                shield_time = player["shield_time"]
                shield_stock = player.get("shield_stock", 0)
                rapid_time = player["rapid_time"]
                rapid_stock = player.get("rapid_stock", 0)
                spread_time = player.get("spread_time", 0.0)
                spread_stock = player.get("spread_stock", 0)
                mine_stock = player.get("mine_stock", 0)
                boost_time = player.get("boost_time", 0.0)
                boost_stock = player.get("boost_stock", 0)
                mine_cooldown = 0.0
                shield_size_mult = 1.0
                game_over = False
                last_death_cause = None
                discovered_planets = set(data.get("discovered_planets", []))

        strafe_left = False
        strafe_right = False
        if not game_over:
            turn = 0
            thrusting = False
            reversing = False
            stopping = False
            hat_x = 0
            hat_y = 0
            fire_button = False
            stop_button = False
            thrust_button = False
            axis_x = 0.0
            axis_y = 0.0
            axis_lt = -1.0
            axis_rt = -1.0
            axis_values = []
            if joystick:
                button_count = joystick.get_numbuttons()
                if button_count > D_PAD_RIGHT:
                    dpad_left = joystick.get_button(D_PAD_LEFT)
                    dpad_right = joystick.get_button(D_PAD_RIGHT)
                    dpad_up = joystick.get_button(D_PAD_UP)
                    dpad_down = joystick.get_button(D_PAD_DOWN)
                    hat_x = -1 if dpad_left else (1 if dpad_right else 0)
                    hat_y = 1 if dpad_up else (-1 if dpad_down else 0)
                elif joystick.get_numhats() > 0:
                    hat = joystick.get_hat(0)
                    hat_x, hat_y = hat[0], hat[1]
                if joystick.get_numaxes() > 0:
                    axis_values = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
                    if len(axis_values) > JOY_AXIS_LX:
                        axis_x = axis_values[JOY_AXIS_LX]
                    if len(axis_values) > JOY_AXIS_LY:
                        axis_y = axis_values[JOY_AXIS_LY]
                    if len(axis_values) > JOY_AXIS_LT:
                        axis_lt = axis_values[JOY_AXIS_LT]
                    if len(axis_values) > JOY_AXIS_RT:
                        axis_rt = axis_values[JOY_AXIS_RT]
                fire_button = joystick.get_button(BTN_X) if button_count > BTN_X else False
                stop_button = joystick.get_button(BTN_L1) if button_count > BTN_L1 else False
                thrust_button = joystick.get_button(BTN_R1) if button_count > BTN_R1 else False
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                turn -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                turn += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                thrusting = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                reversing = True
            if keys[pygame.K_q]:
                strafe_left = True
            if keys[pygame.K_e]:
                strafe_right = True
            if keys[pygame.K_LSHIFT]:
                stopping = True
            if joystick and thrust_button:
                thrusting = True
            if hat_x < 0:
                turn -= 1
            if hat_x > 0:
                turn += 1
            if hat_y > 0:
                thrusting = True
            if hat_y < 0:
                reversing = True
            if hat_x == 0 and hat_y == 0:
                if axis_x < -JOY_AXIS_DEADZONE:
                    turn -= 1
                if axis_x > JOY_AXIS_DEADZONE:
                    turn += 1
                if axis_y > JOY_AXIS_DEADZONE:
                    reversing = True
            if axis_lt > JOY_AXIS_DEADZONE:
                strafe_left = True
            if axis_rt > JOY_AXIS_DEADZONE:
                strafe_right = True
            if stop_button:
                stopping = True
            thrusting_render = thrusting
            stopping_render = stopping
            if stopping_render and not stop_thruster_held:
                stop_thruster_timer = STOP_THRUSTER_TTL
            stop_thruster_held = stopping_render

            boost_multiplier = BOOST_MULTIPLIER if boost_time > 0 else 1.0
            ship_angle += turn * SHIP_TURN_SPEED * dt
            if thrusting:
                ship_vel += angle_to_vector(ship_angle) * (SHIP_THRUST * boost_multiplier) * dt
            if reversing:
                forward = angle_to_vector(ship_angle)
                forward_speed = ship_vel.dot(forward)
                if forward_speed > 10:
                    ship_vel -= ship_vel.normalize() * SHIP_BRAKE * dt
                else:
                    ship_vel -= forward * SHIP_REVERSE_THRUST * dt
            if strafe_left:
                ship_vel += angle_to_vector(ship_angle - 90) * (SHIP_THRUST * boost_multiplier) * dt
            if strafe_right:
                ship_vel += angle_to_vector(ship_angle + 90) * (SHIP_THRUST * boost_multiplier) * dt
            if stopping:
                ship_vel *= max(0.0, 1.0 - SHIP_STOP_DAMP * dt)

            max_speed = SHIP_MAX_SPEED * boost_multiplier
            if ship_vel.length() > max_speed:
                ship_vel.scale_to_length(max_speed)

            new_pos = ship_pos + ship_vel * dt
            ship_pos = clamp_position(new_pos, SHIP_RADIUS)
            ship_prev = pygame.Vector2(ship_pos)

            fire_timer = max(0.0, fire_timer - dt)
            rapid_multiplier = 0.55 if rapid_time > 0 else 1.0
            cooldown = FIRE_COOLDOWN * rapid_multiplier
            if (keys[pygame.K_SPACE] or fire_button) and fire_timer <= 0.0:
                angles = [ship_angle]
                if spread_time > 0:
                    angles = [ship_angle - SPREAD_ANGLE, ship_angle, ship_angle + SPREAD_ANGLE]
                for angle in angles:
                    bullet_vel = angle_to_vector(angle) * BULLET_SPEED + ship_vel * 0.35
                    if bullet_pool:
                        bullet = bullet_pool.pop()
                        bullet["pos"].update(ship_pos)
                        bullet["vel"].update(bullet_vel)
                        bullet["ttl"] = BULLET_TTL
                    else:
                        bullet = {"pos": pygame.Vector2(ship_pos), "vel": bullet_vel, "ttl": BULLET_TTL}
                    bullets.append(bullet)
                if shoot_sound:
                    shoot_sound.play()
                fire_timer = cooldown

        if god_mode:
            shield_time = 10.0
            shield_size_mult = 3.0
        else:
            shield_time = max(0.0, shield_time - dt)
            if shield_time <= 0 and shield_size_mult != 1.0:
                shield_size_mult = 1.0
        rapid_time = max(0.0, rapid_time - dt)
        spread_time = max(0.0, spread_time - dt)
        boost_time = max(0.0, boost_time - dt)
        mine_cooldown = max(0.0, mine_cooldown - dt)
        stop_thruster_timer = max(0.0, stop_thruster_timer - dt)

        for i in range(len(bullets) - 1, -1, -1):
            bullet = bullets[i]
            bullet["pos"] += bullet["vel"] * dt
            bullet["ttl"] -= dt
            if bullet["ttl"] <= 0:
                bullets.pop(i)
                bullet_pool.append(bullet)

        for i in range(len(enemy_bullets) - 1, -1, -1):
            bullet = enemy_bullets[i]
            bullet["pos"] += bullet["vel"] * dt
            bullet["ttl"] -= dt
            if bullet["ttl"] <= 0:
                enemy_bullets.pop(i)
                enemy_bullet_pool.append(bullet)

        for i in range(len(enemy_shards) - 1, -1, -1):
            shard = enemy_shards[i]
            shard["start"] += shard["vel"] * dt
            shard["end"] += shard["vel"] * dt
            shard["ttl"] -= dt
            if shard["ttl"] <= 0:
                enemy_shards.pop(i)
                enemy_shard_pool.append(shard)

        for asteroid in asteroids:
            asteroid.pos += asteroid.vel * dt
            asteroid.angle += asteroid.spin * dt
            if asteroid.pos.x < asteroid.radius:
                asteroid.pos.x = asteroid.radius
                asteroid.vel.x = abs(asteroid.vel.x)
            elif asteroid.pos.x > WORLD_WIDTH - asteroid.radius:
                asteroid.pos.x = WORLD_WIDTH - asteroid.radius
                asteroid.vel.x = -abs(asteroid.vel.x)
            if asteroid.pos.y < asteroid.radius:
                asteroid.pos.y = asteroid.radius
                asteroid.vel.y = abs(asteroid.vel.y)
            elif asteroid.pos.y > WORLD_HEIGHT - asteroid.radius:
                asteroid.pos.y = WORLD_HEIGHT - asteroid.radius
                asteroid.vel.y = -abs(asteroid.vel.y)

        for i in range(len(damage_popups) - 1, -1, -1):
            popup = damage_popups[i]
            popup["pos"] += popup["vel"] * dt
            popup["ttl"] -= dt
            if popup["ttl"] <= 0:
                damage_popups.pop(i)
                damage_popup_pool.append(popup)

        enemy_spawn_timer -= dt
        if enemy_spawn_timer <= 0:
            enemy_spawn_timer = ENEMY_SPAWN_INTERVAL
            radius_sq = ENEMY_NEARBY_RADIUS * ENEMY_NEARBY_RADIUS
            nearby = 0
            for enemy in enemies:
                if (enemy.pos - ship_pos).length_squared() <= radius_sq:
                    nearby += 1
            if nearby < ENEMY_NEARBY_TARGET:
                rng = random.Random(seed + score + int(time.time()))
                to_spawn = min(6, ENEMY_NEARBY_TARGET - nearby)
                for _ in range(to_spawn):
                    chance = elite_spawn_chance(ship_pos.x)
                    enemies.append(spawn_enemy_near(rng, ship_pos, landmarks, elite=rng.random() < chance))
        despawn_sq = ENEMY_DESPAWN_RADIUS * ENEMY_DESPAWN_RADIUS
        for enemy in enemies[:]:
            if enemy.escort:
                continue
            if (enemy.pos - ship_pos).length_squared() > despawn_sq:
                remove_enemy(enemies, enemy, boss_escorts)

        asteroid_spawn_timer -= dt
        if asteroid_spawn_timer <= 0:
            asteroid_spawn_timer = ASTEROID_SPAWN_INTERVAL
            nearby = 0
            radius_sq = ASTEROID_NEARBY_RADIUS * ASTEROID_NEARBY_RADIUS
            for asteroid in asteroids:
                if (asteroid.pos - ship_pos).length_squared() <= radius_sq:
                    nearby += 1
            if nearby < ASTEROID_NEARBY_TARGET:
                rng = random.Random(seed + score + int(time.time()))
                to_spawn = min(6, ASTEROID_NEARBY_TARGET - nearby)
                for _ in range(to_spawn):
                    size = 4 if rng.random() < 0.12 else 3
                    asteroids.append(spawn_asteroid_near(rng, size, ship_pos))

        boss_escorts = [enemy for enemy in enemies if enemy.escort]
        escorts_alive = len(boss_escorts) > 0
        formation_active = False
        escorts_pursuing = False
        if boss and escorts_alive:
            for escort in boss_escorts:
                if (ship_pos - escort.pos).length_squared() <= ENEMY_PURSUE_RADIUS * ENEMY_PURSUE_RADIUS:
                    escorts_pursuing = True
                    break
        if boss:
            to_player = ship_pos - boss.pos
            formation_active = (
                escorts_alive
                and not escorts_pursuing
                and to_player.length_squared() > BOSS_FORMATION_BREAK_RADIUS * BOSS_FORMATION_BREAK_RADIUS
            )
            if escorts_alive and escorts_pursuing:
                boss.vel = pygame.Vector2(0, 0)
                if to_player.length_squared() > 0:
                    boss.angle = turn_towards(boss.angle, vector_to_angle(to_player), BOSS_TURN_SPEED * dt)
            elif escorts_alive:
                target = boss.patrol_points[boss.patrol_index]
                to_target = target - boss.pos
                if to_target.length_squared() <= BOSS_PATROL_NODE_RADIUS * BOSS_PATROL_NODE_RADIUS:
                    boss.patrol_index = (boss.patrol_index + 1) % len(boss.patrol_points)
                    target = boss.patrol_points[boss.patrol_index]
                    to_target = target - boss.pos
                if to_target.length_squared() > 0:
                    target_angle = vector_to_angle(to_target)
                    boss.angle = turn_towards(boss.angle, target_angle, BOSS_TURN_SPEED * dt)
                    boss.vel = angle_to_vector(boss.angle) * BOSS_PATROL_SPEED
                else:
                    boss.vel = pygame.Vector2(0, 0)
                boss.pos += boss.vel * dt
            else:
                if to_player.length_squared() > 0:
                    target_angle = vector_to_angle(to_player)
                    boss.angle = turn_towards(boss.angle, target_angle, BOSS_TURN_SPEED * dt)
                boss.vel = angle_to_vector(boss.angle) * (SHIP_MAX_SPEED * 0.5)
                boss.pos += boss.vel * dt
                boss.fire_timer = max(0.0, boss.fire_timer - dt)
                if boss.fire_timer <= 0.0:
                    bullet_vel = angle_to_vector(boss.angle) * BOSS_BULLET_SPEED + boss.vel * 0.2
                    if enemy_bullet_pool:
                        bullet = enemy_bullet_pool.pop()
                        bullet["pos"].update(boss.pos)
                        bullet["vel"].update(bullet_vel)
                        bullet["ttl"] = ENEMY_BULLET_TTL
                    else:
                        bullet = {"pos": pygame.Vector2(boss.pos), "vel": bullet_vel, "ttl": ENEMY_BULLET_TTL}
                    enemy_bullets.append(bullet)
                    boss.fire_timer = BOSS_FIRE_COOLDOWN
            boss.pos = clamp_position(boss.pos, BOSS_RADIUS)

        for enemy in enemies[:]:
            if boss and formation_active and enemy.escort:
                desired_pos = boss.pos + enemy.escort_offset.rotate(boss.angle)
                to_desired = desired_pos - enemy.pos
                dist = to_desired.length()
                if dist > 1:
                    return_speed = ENEMY_PURSUE_SPEED * 2.0
                    max_step = return_speed * dt
                    if dist <= max_step:
                        enemy.pos = pygame.Vector2(desired_pos)
                        enemy.vel = pygame.Vector2(0, 0)
                        enemy.angle = boss.angle
                    else:
                        target_angle = vector_to_angle(to_desired)
                        enemy.angle = turn_towards(enemy.angle, target_angle, ENEMY_TURN_SPEED * dt * 1.5)
                        enemy.vel = angle_to_vector(enemy.angle) * return_speed
                        enemy.pos = enemy.pos + enemy.vel * dt
                else:
                    enemy.pos = pygame.Vector2(desired_pos)
                    enemy.vel = pygame.Vector2(0, 0)
                    enemy.angle = boss.angle
                enemy.pursuing = False
                continue
            enemy_radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0)
            to_player = ship_pos - enemy.pos
            dist_sq = to_player.length_squared()
            pursuing = dist_sq <= ENEMY_PURSUE_RADIUS * ENEMY_PURSUE_RADIUS
            enemy.pursuing = pursuing
            speed_mult = ELITE_ENEMY_SPEED_MULT if enemy.elite else 1.0
            if pursuing and dist_sq > 0:
                target_angle = vector_to_angle(to_player)
                enemy.angle = turn_towards(enemy.angle, target_angle, ENEMY_TURN_SPEED * dt)
                if dist_sq <= ENEMY_HOLD_RADIUS * ENEMY_HOLD_RADIUS and ship_vel.length() <= ENEMY_HOLD_PLAYER_SPEED:
                    speed = 0.0
                else:
                    speed = ENEMY_PURSUE_SPEED * speed_mult
            else:
                enemy.wander_timer -= dt
                if enemy.wander_timer <= 0:
                    enemy.wander_timer = random.uniform(0.8, 2.2)
                    enemy.wander_angle = (enemy.angle + random.uniform(-120, 120)) % 360
                enemy.angle = turn_towards(enemy.angle, enemy.wander_angle, ENEMY_TURN_SPEED * dt * 0.6)
                speed = ENEMY_SCOUT_SPEED * speed_mult

            enemy.vel = angle_to_vector(enemy.angle) * speed
            enemy.pos = enemy.pos + enemy.vel * dt
            if (
                enemy.pos.x < -enemy_radius
                or enemy.pos.x > WORLD_WIDTH + enemy_radius
                or enemy.pos.y < -enemy_radius
                or enemy.pos.y > WORLD_HEIGHT + enemy_radius
            ):
                remove_enemy(enemies, enemy, boss_escorts)
                continue
            fire_rate_mult = ELITE_ENEMY_FIRE_RATE_MULT if enemy.elite else 1.0
            bullet_speed_mult = ELITE_ENEMY_BULLET_SPEED_MULT if enemy.elite else 1.0
            enemy.fire_timer = max(0.0, enemy.fire_timer - dt)
            if (
                pursuing
                and dist_sq <= ENEMY_FIRE_RANGE * ENEMY_FIRE_RANGE
                and enemy.fire_timer <= 0.0
            ):
                bullet_vel = angle_to_vector(enemy.angle) * (ENEMY_BULLET_SPEED * bullet_speed_mult) + enemy.vel * 0.2
                if enemy_bullet_pool:
                    bullet = enemy_bullet_pool.pop()
                    bullet["pos"].update(enemy.pos)
                    bullet["vel"].update(bullet_vel)
                    bullet["ttl"] = ENEMY_BULLET_TTL
                else:
                    bullet = {"pos": pygame.Vector2(enemy.pos), "vel": bullet_vel, "ttl": ENEMY_BULLET_TTL}
                enemy_bullets.append(bullet)
                enemy.fire_timer = ENEMY_FIRE_COOLDOWN / fire_rate_mult

        for freighter in freighters:
            to_target = freighter["target"] - freighter["pos"]
            dist_sq = to_target.length_squared()
            if dist_sq <= 160 * 160:
                if freighter["target"] == freighter["to"]:
                    freighter["target"] = pygame.Vector2(freighter["from"])
                else:
                    freighter["target"] = pygame.Vector2(freighter["to"])
                to_target = freighter["target"] - freighter["pos"]
            if to_target.length_squared() > 0:
                freighter["angle"] = vector_to_angle(to_target)
                freighter["vel"] = to_target.normalize() * freighter["speed"]
            else:
                freighter["vel"] = pygame.Vector2(0, 0)
            freighter["pos"] = freighter["pos"] + freighter["vel"] * dt

        # Pickups persist until collected.

        if not game_over:
            if shield_prev > 0 and shield_time <= 0:
                for asteroid in asteroids:
                    hit_radius = asteroid.radius + SHIP_RADIUS
                    if moving_circle_hit(ship_pos, ship_pos, asteroid.pos, asteroid.pos, hit_radius):
                        play_explode_sound(ship_pos)
                        lives -= 1
                        last_death_cause = "asteroid"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        shield_time = 10.0
                        shield_size_mult = 3.0
                        rapid_time = 0.0
                        spread_time = 0.0
                        boost_time = 0.0
                        if lives <= 0:
                            game_over = True
                        break
                if not game_over:
                    for landmark in landmarks:
                        hit_radius = landmark.radius + SHIP_RADIUS
                        if moving_circle_hit(ship_pos, ship_pos, landmark.pos, landmark.pos, hit_radius):
                            play_explode_sound(ship_pos)
                            lives -= 1
                            if landmark.kind == "moon":
                                last_death_cause = "moon"
                            else:
                                last_death_cause = "planet"
                            ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                            ship_vel = pygame.Vector2(0, 0)
                            shield_time = 10.0
                            shield_size_mult = 3.0
                            rapid_time = 0.0
                            spread_time = 0.0
                            boost_time = 0.0
                            if lives <= 0:
                                game_over = True
                                break

            for pickup in pickups:
                pickup_hit_radius = SHIP_RADIUS + PICKUP_RADIUS * 0.8
                if moving_circle_hit(ship_prev, ship_pos, pickup.pos, pickup.pos, pickup_hit_radius):
                    if pickup.kind == "boost_canister":
                        continue
                    if pickup.kind == "shield":
                        shield_stock += 1
                    elif pickup.kind == "spread":
                        spread_stock += 1
                    elif pickup.kind == "mine":
                        mine_stock += 3
                    elif pickup.kind == "boost":
                        boost_stock += 1
                    else:
                        rapid_stock += 1
                    pickups.remove(pickup)
                    break

            for bullet in enemy_bullets[:]:
                bullet_prev = prev_pos(bullet["pos"], bullet["vel"], dt)
                if moving_circle_hit(bullet_prev, bullet["pos"], ship_prev, ship_pos, SHIP_RADIUS + 4):
                    enemy_bullets.remove(bullet)
                    enemy_bullet_pool.append(bullet)
                    if shield_time <= 0:
                        play_explode_sound(ship_pos)
                        lives -= 1
                        last_death_cause = "enemy bullet"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        shield_time = 10.0
                        shield_size_mult = 3.0
                        rapid_time = 0.0
                        spread_time = 0.0
                        boost_time = 0.0
                        if lives <= 0:
                            game_over = True
                    break

            for bullet in enemy_bullets[:]:
                bullet_prev = prev_pos(bullet["pos"], bullet["vel"], dt)
                hit = None
                for asteroid in asteroids:
                    asteroid_prev = prev_pos(asteroid.pos, asteroid.vel, dt)
                    radius = asteroid.radius + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], asteroid_prev, asteroid.pos, radius):
                        hit = asteroid
                        break
                if hit:
                    enemy_bullets.remove(bullet)
                    enemy_bullet_pool.append(bullet)
                    asteroids.remove(hit)
                    if hit.size > 1:
                        play_asteroid_explode_sound()
                        rng = random.Random(seed + int(hit.pos.x) + int(hit.pos.y))
                        for _ in range(2):
                            child = spawn_asteroid(rng, hit.size - 1, avoid_center=False)
                            child.pos = pygame.Vector2(hit.pos)
                            child.vel = hit.vel.rotate(rng.uniform(-50, 50)) * 1.2
                            asteroids.append(child)

            for enemy in enemies:
                enemy_radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0)
                enemy_prev = prev_pos(enemy.pos, enemy.vel, dt)
                hit_radius = enemy_radius + SHIP_RADIUS
                if moving_circle_hit(enemy_prev, enemy.pos, ship_prev, ship_pos, hit_radius):
                    if shield_time <= 0:
                        play_explode_sound(ship_pos)
                        lives -= 1
                        last_death_cause = "enemy ship"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        shield_time = 10.0
                        shield_size_mult = 3.0
                        rapid_time = 0.0
                        spread_time = 0.0
                        boost_time = 0.0
                        if lives <= 0:
                            game_over = True
                    break

            if boss:
                boss_prev = prev_pos(boss.pos, boss.vel, dt)
                hit_radius = BOSS_RADIUS + SHIP_RADIUS
                if moving_circle_hit(boss_prev, boss.pos, ship_prev, ship_pos, hit_radius):
                    if shield_time <= 0:
                        play_explode_sound(ship_pos)
                        lives -= 1
                        last_death_cause = "boss ship"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        shield_time = 10.0
                        shield_size_mult = 3.0
                        rapid_time = 0.0
                        spread_time = 0.0
                        boost_time = 0.0
                        if lives <= 0:
                            game_over = True

            for asteroid in asteroids[:]:
                asteroid_prev = prev_pos(asteroid.pos, asteroid.vel, dt)
                hit_radius = asteroid.radius + SHIP_RADIUS
                if moving_circle_hit(ship_prev, ship_pos, asteroid_prev, asteroid.pos, hit_radius):
                    if shield_time <= 0:
                        play_explode_sound(ship_pos)
                        lives -= 1
                        last_death_cause = "asteroid"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        shield_time = 10.0
                        shield_size_mult = 3.0
                        rapid_time = 0.0
                        spread_time = 0.0
                        boost_time = 0.0
                        if lives <= 0:
                            game_over = True
                    break

            for bullet in bullets[:]:
                if boss:
                    bullet_prev = prev_pos(bullet["pos"], bullet["vel"], dt)
                    boss_prev = prev_pos(boss.pos, boss.vel, dt)
                    radius = BOSS_RADIUS + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], boss_prev, boss.pos, radius):
                        bullets.remove(bullet)
                        bullet_pool.append(bullet)
                        if not escorts_alive:
                            boss.hp = max(0, boss.hp - BOSS_HIT_DAMAGE)
                            score += BOSS_HIT_DAMAGE
                            spawn_damage_popup(
                                damage_popups,
                                damage_popup_pool,
                                popup_font,
                                str(BOSS_HIT_DAMAGE),
                                boss.pos,
                                COLORS["boss"],
                            )
                            if boss.hp <= 0:
                                play_explode_sound(boss.pos)
                                score += BOSS_SCORE_BONUS
                                for _ in range(6):
                                    spawn_enemy_shards(
                                        enemy_shards, enemy_shard_pool, boss.pos, boss.angle, COLORS["boss"]
                                    )
                                boss = None
                        continue
                hit_enemy = None
                for enemy in enemies:
                    enemy_radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0)
                    enemy_prev = prev_pos(enemy.pos, enemy.vel, dt)
                    bullet_prev = prev_pos(bullet["pos"], bullet["vel"], dt)
                    radius = enemy_radius + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], enemy_prev, enemy.pos, radius):
                        hit_enemy = enemy
                        break
                if hit_enemy:
                    bullets.remove(bullet)
                    bullet_pool.append(bullet)
                    if hit_enemy.shield > 0:
                        hit_enemy.shield -= 1
                        score += 20
                        if hit_enemy.escort:
                            hit_color = COLORS["boss_shield"]
                        else:
                            hit_color = COLORS["elite_enemy"] if hit_enemy.elite else COLORS["enemy_shield"]
                        spawn_damage_popup(
                            damage_popups,
                            damage_popup_pool,
                            popup_font,
                            "20",
                            hit_enemy.pos,
                            hit_color,
                        )
                    else:
                        remove_enemy(enemies, hit_enemy, boss_escorts)
                        play_explode_sound(hit_enemy.pos)
                        score += 80 + (ELITE_ENEMY_SCORE_BONUS if hit_enemy.elite else 0)
                        shard_color = COLORS["elite_enemy"] if hit_enemy.elite else COLORS["enemy"]
                        spawn_enemy_shards(enemy_shards, enemy_shard_pool, hit_enemy.pos, hit_enemy.angle, shard_color)
                        spawn_damage_popup(
                            damage_popups,
                            damage_popup_pool,
                            popup_font,
                            "80",
                            hit_enemy.pos,
                            COLORS["elite_enemy"] if hit_enemy.elite else COLORS["enemy"],
                        )
                    continue

                hit_canister = None
                for pickup in pickups:
                    if pickup.kind != "boost_canister":
                        continue
                    bullet_prev = prev_pos(bullet["pos"], bullet["vel"], dt)
                    radius = CANISTER_RADIUS + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], pickup.pos, pickup.pos, radius):
                        hit_canister = pickup
                        break
                if hit_canister:
                    bullets.remove(bullet)
                    bullet_pool.append(bullet)
                    hit_canister.shell_hp = max(0, hit_canister.shell_hp - 1)
                    if hit_canister.shell_hp <= 0:
                        hit_canister.kind = "boost"
                        hit_canister.shell_hp = 0
                        spawn_damage_popup(
                            damage_popups,
                            damage_popup_pool,
                            popup_font,
                            "BOOST",
                            hit_canister.pos,
                            COLORS["pickup_boost"],
                        )
                    else:
                        spawn_damage_popup(
                            damage_popups,
                            damage_popup_pool,
                            popup_font,
                            "1",
                            hit_canister.pos,
                            COLORS["pickup_canister"],
                        )
                    continue

                hit = None
                for asteroid in asteroids:
                    asteroid_prev = prev_pos(asteroid.pos, asteroid.vel, dt)
                    bullet_prev = prev_pos(bullet["pos"], bullet["vel"], dt)
                    radius = asteroid.radius + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], asteroid_prev, asteroid.pos, radius):
                        hit = asteroid
                        break
                if hit:
                    bullets.remove(bullet)
                    bullet_pool.append(bullet)
                    asteroids.remove(hit)
                    score += 10 * (5 - hit.size)
                    spawn_damage_popup(
                        damage_popups,
                        damage_popup_pool,
                        popup_font,
                        str(10 * (5 - hit.size)),
                        hit.pos,
                        COLORS["bullet"],
                    )
                    if hit.size > 1:
                        play_asteroid_explode_sound()
                        rng = random.Random(seed + score + int(hit.pos.x))
                        for _ in range(2):
                            child = spawn_asteroid(rng, hit.size - 1, avoid_center=False)
                            child.pos = pygame.Vector2(hit.pos)
                            child.vel = hit.vel.rotate(rng.uniform(-50, 50)) * 1.2
                            asteroids.append(child)
                    break

            for mine in mines[:]:
                mine["ttl"] -= dt
                if mine["ttl"] <= 0:
                    mines.remove(mine)
                    continue
                trigger_enemy = None
                for enemy in enemies:
                    enemy_radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0)
                    if (enemy.pos - mine["pos"]).length() <= enemy_radius + MINE_RADIUS:
                        trigger_enemy = enemy
                        break
                trigger_boss = False
                if not trigger_enemy and boss and not escorts_alive:
                    if (boss.pos - mine["pos"]).length() <= BOSS_RADIUS + MINE_RADIUS:
                        trigger_boss = True
                if not trigger_enemy and not trigger_boss:
                    continue

                mines.remove(mine)
                to_kill = [trigger_enemy] if trigger_enemy else []
                for enemy in enemies:
                    if enemy is trigger_enemy:
                        continue
                    if (enemy.pos - mine["pos"]).length() <= MINE_BLAST_RADIUS:
                        to_kill.append(enemy)
                for enemy in to_kill:
                    if enemy in enemies:
                        remove_enemy(enemies, enemy, boss_escorts)
                        play_explode_sound(enemy.pos)
                        score += 80 + (ELITE_ENEMY_SCORE_BONUS if enemy.elite else 0)
                        shard_color = COLORS["elite_enemy"] if enemy.elite else COLORS["enemy"]
                        spawn_enemy_shards(enemy_shards, enemy_shard_pool, enemy.pos, enemy.angle, shard_color)
                        spawn_damage_popup(
                            damage_popups,
                            damage_popup_pool,
                            popup_font,
                            "80",
                            enemy.pos,
                            COLORS["elite_enemy"] if enemy.elite else COLORS["enemy"],
                        )
                if boss and not escorts_alive and boss is not None:
                    if (boss.pos - mine["pos"]).length() <= MINE_BLAST_RADIUS + BOSS_RADIUS:
                        boss.hp = max(0, boss.hp - BOSS_HIT_DAMAGE)
                        score += BOSS_HIT_DAMAGE
                        spawn_damage_popup(
                            damage_popups,
                            damage_popup_pool,
                            popup_font,
                            str(BOSS_HIT_DAMAGE),
                            boss.pos,
                            COLORS["boss"],
                        )
                        if boss.hp <= 0:
                            play_explode_sound(boss.pos)
                            score += BOSS_SCORE_BONUS
                            for _ in range(6):
                                spawn_enemy_shards(
                                    enemy_shards, enemy_shard_pool, boss.pos, boss.angle, COLORS["boss"]
                                )
                            boss = None

            for enemy in enemies[:]:
                if enemy.shield > 0:
                    continue
                enemy_radius = ENEMY_RADIUS * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0)
                enemy_prev = prev_pos(enemy.pos, enemy.vel, dt)
                for asteroid in asteroids:
                    asteroid_prev = prev_pos(asteroid.pos, asteroid.vel, dt)
                    hit_radius = asteroid.radius + enemy_radius
                    if moving_circle_hit(enemy_prev, enemy.pos, asteroid_prev, asteroid.pos, hit_radius):
                        remove_enemy(enemies, enemy, boss_escorts)
                        play_explode_sound(enemy.pos)
                        score += 100
                        break

            for landmark in landmarks:
                hit_radius = landmark.radius + SHIP_RADIUS
                if moving_circle_hit(ship_prev, ship_pos, landmark.pos, landmark.pos, hit_radius):
                    if shield_time <= 0:
                        play_explode_sound(ship_pos)
                        lives -= 1
                        if landmark.kind == "moon":
                            last_death_cause = "moon"
                        else:
                            last_death_cause = "planet"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        shield_time = 10.0
                        shield_size_mult = 3.0
                        rapid_time = 0.0
                        spread_time = 0.0
                        boost_time = 0.0
                        if lives <= 0:
                            game_over = True
                    break

        if not asteroids:
            rng = random.Random(seed + score)
            for _ in range(120):
                size = 4 if rng.random() < 0.12 else 3
                asteroids.append(spawn_asteroid(rng, size))

        for asteroid in asteroids[:]:
            for landmark in landmarks:
                asteroid_prev = prev_pos(asteroid.pos, asteroid.vel, dt)
                hit_radius = asteroid.radius + landmark.radius
                if moving_circle_hit(asteroid_prev, asteroid.pos, landmark.pos, landmark.pos, hit_radius):
                    asteroids.remove(asteroid)
                    if asteroid.size > 1:
                        rng = random.Random(seed + int(asteroid.pos.x) + int(asteroid.pos.y))
                        for _ in range(2):
                            child = spawn_asteroid(rng, asteroid.size - 1, avoid_center=False)
                            child.pos = pygame.Vector2(asteroid.pos)
                            child.vel = asteroid.vel.rotate(rng.uniform(-60, 60)) * 1.2
                            asteroids.append(child)
                    break

        screen.fill(COLORS["bg"])

        # Debug: universe bounds
        top_left = world_to_screen(pygame.Vector2(0, 0), ship_pos)
        bottom_right = world_to_screen(pygame.Vector2(WORLD_WIDTH, WORLD_HEIGHT), ship_pos)
        rect_left = min(top_left.x, bottom_right.x)
        rect_top = min(top_left.y, bottom_right.y)
        rect_w = abs(bottom_right.x - top_left.x)
        rect_h = abs(bottom_right.y - top_left.y)
        pygame.draw.rect(
            screen,
            COLORS["warning"],
            pygame.Rect(rect_left, rect_top, rect_w, rect_h),
            4,
        )

        star_surface = stars["surface"]
        tile_w = stars["width"]
        tile_h = stars["height"]
        offset_x = int((-ship_pos.x * STAR_PARALLAX) % tile_w)
        offset_y = int((-ship_pos.y * STAR_PARALLAX) % tile_h)
        for draw_x in (offset_x - tile_w, offset_x):
            for draw_y in (offset_y - tile_h, offset_y):
                screen.blit(star_surface, (draw_x, draw_y))

        for landmark in landmarks:
            screen_pos = world_to_screen(landmark.pos, ship_pos)
            draw_radius = landmark.radius * CAMERA_ZOOM
            pygame.draw.circle(
                screen,
                landmark.color,
                (int(screen_pos.x), int(screen_pos.y)),
                max(1, int(draw_radius)),
                2,
            )
            if landmark.kind == "planet":
                on_screen = (
                    -draw_radius <= screen_pos.x <= WIDTH + draw_radius
                    and -draw_radius <= screen_pos.y <= HEIGHT + draw_radius
                )
                if on_screen:
                    if landmark.id not in beacons:
                        rng = random.Random(seed + landmark.id * 7919)
                        offset = pygame.Vector2(
                            rng.uniform(landmark.radius + BEACON_OFFSET_MIN, landmark.radius + BEACON_OFFSET_MAX), 0
                        ).rotate(rng.uniform(0, 360))
                        beacon_pos = clamp_position(landmark.pos + offset)
                        beacons[landmark.id] = {
                            "pos": beacon_pos,
                            "code": make_beacon_id(rng),
                        }
                    discovered_planets.add(landmark.id)

        for planet_id, beacon in beacons.items():
            screen_pos = world_to_screen(beacon["pos"], ship_pos)
            draw_beacon(screen, screen_pos, COLORS["pickup_shield"])
            label = font.render(beacon["code"], True, COLORS["ui"])
            screen.blit(label, (screen_pos.x + 18, screen_pos.y - 10))

        for asteroid in asteroids:
            screen_pos = world_to_screen(asteroid.pos, ship_pos)
            draw_radius = asteroid.radius * CAMERA_ZOOM
            draw_vector_shape(screen, screen_pos, asteroid.angle, asteroid.shape, COLORS["asteroid"], 2)

        for bullet in bullets:
            screen_pos = world_to_screen(bullet["pos"], ship_pos)
            bullet_radius = max(1, int(2 * CAMERA_ZOOM))
            pygame.draw.circle(
                screen,
                COLORS["bullet"],
                (int(screen_pos.x), int(screen_pos.y)),
                bullet_radius,
                1,
            )

        for bullet in enemy_bullets:
            screen_pos = world_to_screen(bullet["pos"], ship_pos)
            bullet_radius = max(1, int(2 * CAMERA_ZOOM))
            pygame.draw.circle(
                screen,
                COLORS["enemy"],
                (int(screen_pos.x), int(screen_pos.y)),
                bullet_radius,
                1,
            )

        for mine in mines:
            screen_pos = world_to_screen(mine["pos"], ship_pos)
            draw_mine(
                screen,
                screen_pos,
                max(2, int(MINE_RADIUS * CAMERA_ZOOM)),
                COLORS["pickup_mine"],
                COLORS["mine_core"],
            )

        if boss:
            screen_pos = world_to_screen(boss.pos, ship_pos)
            if escorts_alive:
                shield_radius = (BOSS_RADIUS + 16) * CAMERA_ZOOM
                pygame.draw.circle(
                    screen,
                    COLORS["boss_shield"],
                    (int(screen_pos.x), int(screen_pos.y)),
                    max(1, int(shield_radius)),
                    2,
                )
            if boss.vel.length_squared() > 0:
                draw_thruster(
                    screen,
                    screen_pos,
                    boss.angle,
                    COLORS["pickup_rapid"],
                    2.2,
                    3.0,
                )
            draw_boss(screen, screen_pos, boss.angle, COLORS["boss"], BOSS_SCALE)

        for enemy in enemies:
            screen_pos = world_to_screen(enemy.pos, ship_pos)
            if enemy.shield > 0:
                shield_mult = ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0
                if not enemy.elite and not enemy.escort:
                    shield_radius = (SHIP_RADIUS + 10) * CAMERA_ZOOM
                else:
                    shield_radius = (ENEMY_RADIUS + 8) * CAMERA_ZOOM * shield_mult
                pygame.draw.circle(
                    screen,
                    COLORS["boss_shield"] if enemy.escort else (COLORS["elite_enemy_shield"] if enemy.elite else COLORS["enemy_shield"]),
                    (int(screen_pos.x), int(screen_pos.y)),
                    max(1, int(shield_radius)),
                    2 if enemy.elite or enemy.escort else 1,
                )
            if enemy.pursuing:
                back_mult = 2.0 * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0)
                draw_thruster(
                    screen,
                    screen_pos,
                    enemy.angle,
                    COLORS["elite_enemy"] if enemy.elite else COLORS["enemy"],
                    0.7 * (ELITE_ENEMY_SIZE_MULT if enemy.elite else 1.0),
                    back_mult,
                )
            if enemy.elite:
                draw_ship(screen, screen_pos, enemy.angle, COLORS["elite_enemy"], ELITE_ENEMY_SIZE_MULT)
            else:
                draw_ship(screen, screen_pos, enemy.angle, COLORS["enemy"])

        for freighter in freighters:
            screen_pos = world_to_screen(freighter["pos"], ship_pos)
            shield_radius = (FREIGHTER_RADIUS + 14) * CAMERA_ZOOM
            pygame.draw.circle(
                screen,
                COLORS["freighter_shield"],
                (int(screen_pos.x), int(screen_pos.y)),
                max(1, int(shield_radius)),
                1,
            )
            draw_thruster(screen, screen_pos, freighter["angle"], COLORS["pickup_rapid"], 0.9, 2.8)
            draw_freighter(screen, screen_pos, freighter["angle"], COLORS["freighter"])

        for pickup in pickups:
            screen_pos = world_to_screen(pickup.pos, ship_pos)
            if pickup.kind == "boost_canister":
                shell_radius = max(2, int(CANISTER_RADIUS * CAMERA_ZOOM))
                core_radius = max(1, int((PICKUP_RADIUS * 0.45) * CAMERA_ZOOM))
                shell_rect = pygame.Rect(0, 0, shell_radius * 2, shell_radius * 2)
                shell_rect.center = (int(screen_pos.x), int(screen_pos.y))
                core_rect = pygame.Rect(0, 0, core_radius * 2, core_radius * 2)
                core_rect.center = (int(screen_pos.x), int(screen_pos.y))
                pygame.draw.rect(screen, COLORS["pickup_canister"], shell_rect, 2)
                pygame.draw.rect(screen, COLORS["pickup_canister"], core_rect, 1)
                continue

            if pickup.kind == "shield":
                color = COLORS["pickup_shield"]
            elif pickup.kind == "spread":
                color = COLORS["pickup_spread"]
            elif pickup.kind == "mine":
                color = COLORS["pickup_mine"]
            elif pickup.kind == "boost":
                color = COLORS["pickup_boost"]
            else:
                color = COLORS["pickup_rapid"]
            pickup_radius = max(2, int(PICKUP_RADIUS * CAMERA_ZOOM))
            core_radius = max(1, int((PICKUP_RADIUS * 0.25) * CAMERA_ZOOM))
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), pickup_radius, 2)
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), core_radius, 0)

        if shield_time > 0 and not game_over:
            shield_screen_pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
            shield_radius = (SHIP_RADIUS * CAMERA_ZOOM + 10 * CAMERA_ZOOM) * shield_size_mult * 1.2
            pygame.draw.circle(
                screen,
                COLORS["god_shield"] if god_mode else COLORS["pickup_shield"],
                (int(shield_screen_pos.x), int(shield_screen_pos.y)),
                max(1, int(shield_radius)),
                1,
            )

        for popup in damage_popups:
            screen_pos = world_to_screen(popup["pos"], ship_pos)
            alpha = int(255 * (popup["ttl"] / DAMAGE_POPUP_TTL))
            surface = popup["surface"]
            surface.set_alpha(max(0, min(255, alpha)))
            screen.blit(surface, (screen_pos.x - surface.get_width() / 2, screen_pos.y - surface.get_height() / 2))

        for shard in enemy_shards:
            alpha = shard["ttl"] / ENEMY_SHARD_TTL
            color = scale_color(shard.get("color", COLORS["enemy"]), alpha)
            start = world_to_screen(shard["start"], ship_pos)
            end = world_to_screen(shard["end"], ship_pos)
            pygame.draw.line(screen, color, start, end, 2)

        ship_color = COLORS["warning"] if game_over else COLORS["ship"]
        if thrusting_render and not game_over:
            thruster_scale = 2.0 if boost_time > 0 else 1.0
            draw_thruster(
                screen,
                pygame.Vector2(WIDTH / 2, HEIGHT / 2),
                ship_angle,
                COLORS["pickup_rapid"],
                thruster_scale,
            )
        if stop_thruster_timer > 0 and not game_over:
            alpha = stop_thruster_timer / STOP_THRUSTER_TTL
            draw_stop_thruster(
                screen,
                pygame.Vector2(WIDTH / 2, HEIGHT / 2),
                ship_angle,
                scale_color(COLORS["pickup_boost"], alpha),
                stop_thruster_side,
            )
        if (strafe_left or strafe_right) and not game_over:
            strafe_side = "right" if strafe_left and not strafe_right else "left"
            draw_stop_thruster(
                screen,
                pygame.Vector2(WIDTH / 2, HEIGHT / 2),
                ship_angle,
                scale_color(COLORS["pickup_boost"], 0.7),
                strafe_side,
            )
        draw_ship(screen, pygame.Vector2(WIDTH / 2, HEIGHT / 2), ship_angle, ship_color)

        ui_pickups = [
            ("shield", COLORS["god_shield"] if god_mode else COLORS["pickup_shield"], shield_stock, shield_time, "1"),
            ("boost", COLORS["pickup_boost"], boost_stock, boost_time, "2"),
            ("spread", COLORS["pickup_spread"], spread_stock, spread_time, "3"),
            ("mine", COLORS["pickup_mine"], mine_stock, 0.0, "4"),
        ]
        start_x = WIDTH / 2 - UI_PICKUP_SPACING * ((len(ui_pickups) - 1) / 2)
        for index, (kind, color, count, timer, key_label) in enumerate(ui_pickups):
            center = pygame.Vector2(start_x + index * UI_PICKUP_SPACING, UI_PICKUP_TOP_Y)
            active = count > 0 or timer > 0
            draw_color = color if active else scale_color(color, 0.35)
            pickup_radius = UI_PICKUP_RADIUS
            core_radius = max(2, int(pickup_radius * 0.4))
            pygame.draw.circle(screen, draw_color, (int(center.x), int(center.y)), pickup_radius, 2)
            pygame.draw.circle(screen, draw_color, (int(center.x), int(center.y)), core_radius, 0)

            count_text = str(count)
            count_surface = font.render(count_text, True, COLORS["ui"])
            screen.blit(
                count_surface,
                (center.x + pickup_radius + 8, center.y - count_surface.get_height() / 2),
            )
            if show_gamepad_debug:
                key_surface = debug_font.render(key_label, True, COLORS["ui"])
                screen.blit(
                    key_surface,
                    (center.x - key_surface.get_width() / 2, center.y - pickup_radius - 18),
                )
            if timer > 0:
                timer_text = f"{timer:.1f}s"
                timer_surface = debug_font.render(timer_text, True, COLORS["ui"])
                screen.blit(
                    timer_surface,
                    (center.x - timer_surface.get_width() / 2, center.y + pickup_radius + 6),
                )

        nearest_planet = None
        nearest_dist_sq = None
        for landmark in landmarks:
            if landmark.kind != "planet":
                continue
            delta = landmark.pos - ship_pos
            dist_sq = delta.length_squared()
            if nearest_dist_sq is None or dist_sq < nearest_dist_sq:
                nearest_dist_sq = dist_sq
                nearest_planet = delta
        if nearest_planet is not None:
            draw_edge_arrow(screen, nearest_planet, COLORS["planet"])

        if show_gamepad_debug:
            ram_mb = get_process_ram_mb()
            lines = [
                f"Gamepad: {joy_name}",
                f"Axes: {joy_axes}  Buttons: {joy_buttons}  Hats: {joy_hats}",
            ]
            if ram_mb is not None:
                lines.append(f"RAM: {ram_mb:.1f} MB")
            if joystick:
                if joy_hats > 0:
                    lines.append(f"Hat0: {joystick.get_hat(0)}")
                if joy_buttons > 0:
                    pressed = [str(i) for i in range(joy_buttons) if joystick.get_button(i)]
                    lines.append(f"Pressed: {' '.join(pressed) if pressed else '-'}")
                if joy_axes > 0:
                    axes = " ".join(f"{i}:{joystick.get_axis(i):.2f}" for i in range(min(8, joy_axes)))
                    lines.append(f"Axes: {axes}")
            for i, line in enumerate(lines):
                text = debug_font.render(line, True, COLORS["ui"])
                screen.blit(text, (10, HEIGHT - 120 + i * 18))

        lives_text = font.render(f"Lives: {lives}", True, COLORS["ui"])
        screen.blit(lives_text, (10, 10))

        score_text = font.render(f"Score: {score}", True, COLORS["ui"])
        screen.blit(score_text, (WIDTH - score_text.get_width() - 10, 10))

        if show_gamepad_debug:
            ram_mb = get_process_ram_mb()
            hud = [
                f"Seed: {seed}",
                f"Shield: {shield_time:.1f}s" if shield_time > 0 else "Shield: -",
                f"Shield Stock: {shield_stock}",
                f"Spread: {spread_time:.1f}s" if spread_time > 0 else "Spread: -",
                f"Spread Stock: {spread_stock}",
                f"Mine Stock: {mine_stock}",
                f"Boost: {boost_time:.1f}s" if boost_time > 0 else "Boost: -",
                f"Boost Stock: {boost_stock}",
            ]
            hud.append(f"RAM: {ram_mb:.1f} MB" if ram_mb is not None else "RAM: n/a")
            hud.append(f"Last Death: {last_death_cause}" if last_death_cause else "Last Death: -")
            for i, line in enumerate(hud):
                text = font.render(line, True, COLORS["ui"])
                screen.blit(text, (10, 10 + (i + 1) * 20))

        if show_gamepad_debug:
            help_text = "Arrows/WASD move  Q/E strafe  LShift stop  L-stick aim  R1 thrust  L1 brake  Space shoot  1 shield  2 boost  3 spread  4 mine  M map  F5 save  F6 load  F2 god shield  N new seed"
            text = font.render(help_text, True, COLORS["ui"])
            screen.blit(text, (10, HEIGHT - 28))

        if game_over:
            title = "Game Over"
            reason = f"{(last_death_cause or 'Unknown').title()} Killed You"
            prompt = "Press N key for New Map"
            title_surface = game_over_font_big.render(title, True, COLORS["warning"])
            reason_surface = game_over_font_med.render(reason, True, COLORS["warning"])
            prompt_surface = game_over_font_small.render(prompt, True, COLORS["warning"])
            total_h = title_surface.get_height() + reason_surface.get_height() + prompt_surface.get_height() + 18
            start_y = HEIGHT / 2 - total_h / 2
            screen.blit(title_surface, (WIDTH / 2 - title_surface.get_width() / 2, start_y))
            screen.blit(
                reason_surface,
                (WIDTH / 2 - reason_surface.get_width() / 2, start_y + title_surface.get_height() + 8),
            )
            screen.blit(
                prompt_surface,
                (
                    WIDTH / 2 - prompt_surface.get_width() / 2,
                    start_y + title_surface.get_height() + reason_surface.get_height() + 16,
                ),
            )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
