import json
import math
import os
import random
import time
from dataclasses import dataclass
from typing import Optional

import pygame


WIDTH = 1024
HEIGHT = 768
WORLD_WIDTH = 80000
WORLD_HEIGHT = 60000
FPS = 60
CAMERA_ZOOM = 0.5
STAR_PARALLAX = 0.18

SAVE_PATH = "save.json"

SHIP_RADIUS = 12
SHIP_THRUST = 260
SHIP_REVERSE_THRUST = 120
SHIP_BRAKE = 360
SHIP_STOP_DAMP = 6.0
SHIP_TURN_SPEED = 200  # degrees/sec
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
ENEMY_PURSUE_RADIUS = 450
ENEMY_FIRE_RANGE = 300
ENEMY_FIRE_COOLDOWN = 1.4
ENEMY_BULLET_SPEED = 400
ENEMY_BULLET_TTL = 4.0
ENEMY_SHIELD_HITS = 1
ENEMY_NEARBY_TARGET = 12
ENEMY_NEARBY_RADIUS = 3600
ENEMY_SPAWN_RADIUS = 4000
ENEMY_SPAWN_BUFFER = 1800
ENEMY_OFFSCREEN_MARGIN = 240
ENEMY_DESPAWN_RADIUS = 5200
ENEMY_SPAWN_INTERVAL = 3.2

PICKUP_TTL = 15.0
PICKUP_GRID_SPACING = 1.25
PICKUP_RADIUS = 24
CANISTER_RADIUS = 26
CANISTER_HITS = 4
BOOST_MULTIPLIER = 1.5
BOOST_TIME = 3.0
STAR_COUNT = 500
FREIGHTER_COUNT = 10
FREIGHTER_SPEED = (70, 110)
FREIGHTER_RADIUS = SHIP_RADIUS * 4
JOY_AXIS_X = 0
JOY_AXIS_Y = 4
JOY_AXIS_DEADZONE = 0.5


COLORS = {
    "bg": (5, 7, 10),
    "ship": (230, 230, 230),
    "bullet": (255, 250, 200),
    "asteroid": (245, 245, 245),
    "planet": (120, 220, 140),
    "moon": (120, 170, 255),
    "pickup_shield": (120, 200, 255),
    "pickup_rapid": (255, 190, 120),
    "pickup_boost": (255, 170, 90),
    "pickup_canister": (170, 90, 220),
    "pickup_boost": (170, 90, 220),
    "enemy": (235, 90, 90),
    "enemy_shield": (255, 140, 140),
    "freighter": (150, 110, 80),
    "freighter_shield": (120, 160, 200),
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
    prev: Optional[pygame.Vector2] = None


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
    prev: Optional[pygame.Vector2] = None


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
    kind = rng.choice(["shield", "rapid", "boost_canister"])
    pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
    shell_hp = CANISTER_HITS if kind == "boost_canister" else 0
    return Pickup(kind=kind, pos=pos, ttl=PICKUP_TTL, shell_hp=shell_hp)


def spawn_enemy(rng):
    pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
    angle = rng.uniform(0, 360)
    return Enemy(
        pos=pos,
        vel=pygame.Vector2(0, 0),
        angle=angle,
        shield=ENEMY_SHIELD_HITS,
        fire_timer=rng.uniform(0, ENEMY_FIRE_COOLDOWN),
        wander_timer=rng.uniform(0.5, 1.5),
        wander_angle=angle,
    )


def spawn_enemy_near(rng, center):
    view_half_w = WIDTH / (2 * CAMERA_ZOOM) + ENEMY_OFFSCREEN_MARGIN
    view_half_h = HEIGHT / (2 * CAMERA_ZOOM) + ENEMY_OFFSCREEN_MARGIN
    for _ in range(60):
        offset = pygame.Vector2(rng.uniform(ENEMY_SPAWN_BUFFER, ENEMY_SPAWN_RADIUS), 0).rotate(
            rng.uniform(0, 360)
        )
        pos = center + offset
        if not (0 <= pos.x <= WORLD_WIDTH and 0 <= pos.y <= WORLD_HEIGHT):
            continue
        if abs(pos.x - center.x) < view_half_w and abs(pos.y - center.y) < view_half_h:
            continue
        enemy = spawn_enemy(rng)
        enemy.pos = pos
        return enemy
    enemy = spawn_enemy(rng)
    enemy.pos = clamp_position(center + pygame.Vector2(ENEMY_SPAWN_RADIUS, 0), radius=ENEMY_RADIUS)
    return enemy


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
    planet_count = 20
    planets = []
    planet_id = 0
    for _ in range(planet_count):
        radius = rng.randint(1760, 2880)
        for _ in range(40):
            pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
            if all((pos - p["pos"]).length() >= p["radius"] + radius + 220 for p in planets):
                planets.append(
                    {
                        "id": planet_id,
                        "kind": "planet",
                        "pos": pos,
                        "radius": radius,
                        "color": COLORS["planet"],
                    }
                )
                planet_id += 1
                break
        else:
            planets.append(
                {
                    "id": planet_id,
                    "kind": "planet",
                    "pos": pos,
                    "radius": radius,
                    "color": COLORS["planet"],
                }
            )
            planet_id += 1
    landmarks.extend(planets)
    moon_id = 0
    for parent in planets:
        size = rng.randint(int(parent["radius"] * 0.16), int(parent["radius"] * 0.4))
        min_orbit = parent["radius"] + size + 120
        max_orbit = parent["radius"] + size + 520
        offset = pygame.Vector2(rng.uniform(min_orbit, max_orbit), 0).rotate(rng.uniform(0, 360))
        moon_pos = clamp_position(parent["pos"] + offset, radius=size)
        landmarks.append(
            {
                "id": moon_id,
                "kind": "moon",
                "pos": moon_pos,
                "radius": size,
                "color": COLORS["moon"],
                "parent_id": parent["id"],
            }
        )
        moon_id += 1
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


def generate_enemies(seed, center):
    rng = random.Random(seed ^ 0x1EADBEEF)
    enemies = []
    for _ in range(ENEMY_NEARBY_TARGET):
        enemies.append(spawn_enemy_near(rng, center))
    return enemies


def generate_starfield(seed):
    rng = random.Random(seed ^ 0xA5A5A5A5)
    stars = []
    for _ in range(STAR_COUNT):
        pos = pygame.Vector2(rng.uniform(0, WORLD_WIDTH), rng.uniform(0, WORLD_HEIGHT))
        brightness = rng.randint(35, 95)
        size = 1 if rng.random() < 0.9 else 2
        stars.append({"pos": pos, "brightness": brightness, "size": size})
    return stars


def pick_nearest_moon(planet, moons):
    best = None
    best_dist_sq = None
    for moon in moons:
        dist_sq = (moon["pos"] - planet["pos"]).length_squared()
        if best_dist_sq is None or dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            best = moon
    return best


def generate_freighters(seed, landmarks):
    rng = random.Random(seed ^ 0x7F4A7C15)
    planets = [l for l in landmarks if l["kind"] == "planet"]
    moons = [l for l in landmarks if l["kind"] == "moon"]
    if len(planets) < 2 or len(moons) < 2:
        return []
    freighters = []
    for _ in range(FREIGHTER_COUNT):
        origin, dest = rng.sample(planets, 2)
        origin_moon = pick_nearest_moon(origin, moons)
        dest_moon = pick_nearest_moon(dest, moons)
        if not origin_moon or not dest_moon:
            continue
        pos = pygame.Vector2(origin_moon["pos"])
        speed = rng.uniform(*FREIGHTER_SPEED)
        freighters.append(
            {
                "pos": pos,
                "vel": pygame.Vector2(0, 0),
                "angle": rng.uniform(0, 360),
                "from": pygame.Vector2(origin_moon["pos"]),
                "to": pygame.Vector2(dest_moon["pos"]),
                "target": pygame.Vector2(dest_moon["pos"]),
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
    enemies = generate_enemies(seed, center)
    landmarks = generate_landmarks(seed)
    stars = generate_starfield(seed)
    freighters = generate_freighters(seed, landmarks)
    return asteroids, pickups, enemies, landmarks, stars, freighters


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


def serialize_enemy(enemy):
    return {
        "pos": serialize_vec(enemy.pos),
        "angle": enemy.angle,
        "shield": enemy.shield,
        "fire_timer": enemy.fire_timer,
        "wander_timer": enemy.wander_timer,
        "wander_angle": enemy.wander_angle,
    }


def deserialize_enemy(data):
    angle = data.get("angle", 0.0)
    return Enemy(
        pos=deserialize_vec(data["pos"]),
        vel=pygame.Vector2(0, 0),
        angle=angle,
        shield=data.get("shield", ENEMY_SHIELD_HITS),
        fire_timer=data.get("fire_timer", 0.0),
        wander_timer=data.get("wander_timer", 0.0),
        wander_angle=data.get("wander_angle", angle),
    )


def draw_vector_shape(surface, pos, angle, points, color, width=2):
    rotated = []
    for x, y in points:
        vec = pygame.Vector2(x, y).rotate(angle) * CAMERA_ZOOM
        rotated.append((pos.x + vec.x, pos.y + vec.y))
    pygame.draw.lines(surface, color, True, rotated, width)


def draw_ship(surface, pos, angle, color):
    render_radius = SHIP_RADIUS * CAMERA_ZOOM
    nose = pygame.Vector2(render_radius * 1.2, 0).rotate(angle)
    left = pygame.Vector2(-render_radius, -render_radius * 0.7).rotate(angle)
    right = pygame.Vector2(-render_radius, render_radius * 0.7).rotate(angle)
    points = [
        (pos.x + nose.x, pos.y + nose.y),
        (pos.x + left.x, pos.y + left.y),
        (pos.x + right.x, pos.y + right.y),
    ]
    pygame.draw.lines(surface, color, True, points, 2)


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


def draw_thruster(surface, pos, angle, color, scale=1.0):
    render_radius = SHIP_RADIUS * CAMERA_ZOOM
    back = pygame.Vector2(-render_radius * 1.7, 0).rotate(angle)
    perp = pygame.Vector2(0, render_radius * 0.35).rotate(angle)
    base = pos + back
    lengths = [render_radius * 1.8 * scale, render_radius * 1.3 * scale, render_radius * 0.9 * scale]
    offsets = [0.0, render_radius * 0.22, -render_radius * 0.22]
    for length, offset in zip(lengths, offsets):
        start = base + perp * offset
        end = start + pygame.Vector2(-length, 0).rotate(angle)
        pygame.draw.line(surface, color, start, end, 2)


def main():
    pygame.init()
    pygame.joystick.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Seeded Asteroids - Prototype")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 18)
    debug_font = pygame.font.SysFont("Consolas", 16)
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
    asteroids, pickups, enemies, landmarks, stars, freighters = new_world(seed)

    ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
    ship_vel = pygame.Vector2(0, 0)
    ship_angle = -90

    bullets = []
    enemy_bullets = []
    fire_timer = 0.0
    score = 0
    lives = 3
    game_over = False
    last_death_cause = None

    shield_time = 0.0
    shield_stock = 0
    rapid_time = 0.0
    boost_time = 0.0
    boost_stock = 0
    asteroid_spawn_timer = 0.0
    enemy_spawn_timer = 0.0
    thrusting_render = False
    show_map = False
    discovered_planets = set()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        ship_prev = pygame.Vector2(ship_pos)
        shield_prev = shield_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    show_gamepad_debug = not show_gamepad_debug
                elif event.key == pygame.K_m:
                    show_map = not show_map
                elif event.key == pygame.K_r and not game_over:
                    if shield_stock > 0 and shield_time <= 0:
                        shield_stock -= 1
                        shield_time = 8.0
                elif event.key == pygame.K_f and not game_over:
                    if boost_stock > 0 and boost_time <= 0:
                        boost_stock -= 1
                        boost_time = BOOST_TIME

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
                kind = landmark.get("kind")
                if kind == "planet":
                    if landmark.get("id") not in discovered_planets:
                        continue
                    color = COLORS["planet"]
                elif kind == "moon":
                    if landmark.get("parent_id") not in discovered_planets:
                        continue
                    color = COLORS["moon"]
                else:
                    continue
                map_x = map_rect.x + (landmark["pos"].x / WORLD_WIDTH) * map_rect.width
                map_y = map_rect.y + (landmark["pos"].y / WORLD_HEIGHT) * map_rect.height
                map_radius = max(1, int(landmark["radius"] * map_scale))
                pygame.draw.circle(screen, color, (int(map_x), int(map_y)), map_radius, 1)
            for freighter in freighters:
                map_x = map_rect.x + (freighter["pos"].x / WORLD_WIDTH) * map_rect.width
                map_y = map_rect.y + (freighter["pos"].y / WORLD_HEIGHT) * map_rect.height
                pygame.draw.circle(screen, COLORS["freighter"], (int(map_x), int(map_y)), 3, 0)
            map_x = map_rect.x + (ship_pos.x / WORLD_WIDTH) * map_rect.width
            map_y = map_rect.y + (ship_pos.y / WORLD_HEIGHT) * map_rect.height
            pygame.draw.circle(screen, COLORS["pickup_shield"], (int(map_x), int(map_y)), 5, 0)
            title = font.render("Map - press M to close", True, COLORS["ui"])
            screen.blit(title, (WIDTH / 2 - title.get_width() / 2, 24))
            pygame.display.flip()
            continue

        if keys[pygame.K_n]:
            seed = seed_from_time()
            asteroids, pickups, enemies, landmarks, stars, freighters = new_world(seed)
            bullets = []
            enemy_bullets = []
            ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
            ship_vel = pygame.Vector2(0, 0)
            ship_angle = -90
            score = 0
            lives = 3
            shield_time = 0.0
            shield_stock = 0
            rapid_time = 0.0
            boost_time = 0.0
            boost_stock = 0
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
                    "boost_time": boost_time,
                    "boost_stock": boost_stock,
                },
                "asteroids": [serialize_asteroid(a) for a in asteroids],
                "pickups": [serialize_pickup(p) for p in pickups],
                "enemies": [serialize_enemy(e) for e in enemies],
                "discovered_planets": sorted(discovered_planets),
            }
            save_state(state)

        if keys[pygame.K_l]:
            data = load_state()
            if data:
                seed = data["seed"]
                asteroids = [deserialize_asteroid(a) for a in data["asteroids"]]
                pickups = [deserialize_pickup(p) for p in data["pickups"]]
                if "enemies" in data:
                    enemies = [deserialize_enemy(e) for e in data["enemies"]]
                else:
                    enemies = generate_enemies(seed, pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2))
                landmarks = generate_landmarks(seed)
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
                boost_time = player.get("boost_time", 0.0)
                boost_stock = player.get("boost_stock", 0)
                game_over = False
                last_death_cause = None
                discovered_planets = set(data.get("discovered_planets", []))
                if len(enemies) < ENEMY_NEARBY_TARGET:
                    rng = random.Random(seed ^ int(time.time()))
                    for _ in range(ENEMY_NEARBY_TARGET - len(enemies)):
                        enemies.append(spawn_enemy_near(rng, ship_pos))

        if not game_over:
            turn = 0
            thrusting = False
            reversing = False
            stopping = False
            hat_x = 0
            hat_y = 0
            fire_button = False
            stop_button = False
            axis_x = 0.0
            axis_y = 0.0
            axis_values = []
            if joystick:
                if joystick.get_numhats() > 0:
                    hat = joystick.get_hat(0)
                    hat_x, hat_y = hat[0], hat[1]
                if joystick.get_numaxes() > 0:
                    axis_values = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
                    if len(axis_values) > JOY_AXIS_X:
                        axis_x = axis_values[JOY_AXIS_X]
                    if len(axis_values) > JOY_AXIS_Y:
                        axis_y = axis_values[JOY_AXIS_Y]
                fire_button = joystick.get_button(2)
                stop_button = joystick.get_button(1)
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                turn -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                turn += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                thrusting = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                reversing = True
            if keys[pygame.K_q]:
                stopping = True
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
                if axis_y < -JOY_AXIS_DEADZONE:
                    thrusting = True
                if axis_y > JOY_AXIS_DEADZONE:
                    reversing = True
            thrusting_render = thrusting
            if stop_button:
                stopping = True

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
            if stopping:
                ship_vel *= max(0.0, 1.0 - SHIP_STOP_DAMP * dt)

            max_speed = SHIP_MAX_SPEED * boost_multiplier
            if ship_vel.length() > max_speed:
                ship_vel.scale_to_length(max_speed)

            new_pos = ship_pos + ship_vel * dt
            wrapped = False
            if new_pos.x < 0 or new_pos.x >= WORLD_WIDTH:
                new_pos.x %= WORLD_WIDTH
                wrapped = True
            if new_pos.y < 0 or new_pos.y >= WORLD_HEIGHT:
                new_pos.y %= WORLD_HEIGHT
                wrapped = True
            ship_pos = new_pos
            if wrapped:
                ship_prev = pygame.Vector2(ship_pos)

            fire_timer = max(0.0, fire_timer - dt)
            rapid_multiplier = 0.55 if rapid_time > 0 else 1.0
            cooldown = FIRE_COOLDOWN * rapid_multiplier
            if (keys[pygame.K_SPACE] or fire_button) and fire_timer <= 0.0:
                bullet_vel = angle_to_vector(ship_angle) * BULLET_SPEED + ship_vel * 0.35
                bullets.append(
                    {
                        "pos": pygame.Vector2(ship_pos),
                        "prev": pygame.Vector2(ship_pos),
                        "vel": bullet_vel,
                        "ttl": BULLET_TTL,
                    }
                )
                fire_timer = cooldown

        shield_time = max(0.0, shield_time - dt)
        rapid_time = max(0.0, rapid_time - dt)
        boost_time = max(0.0, boost_time - dt)

        for i in range(len(bullets) - 1, -1, -1):
            bullet = bullets[i]
            bullet["prev"] = pygame.Vector2(bullet["pos"])
            bullet["pos"] += bullet["vel"] * dt
            bullet["ttl"] -= dt
            if bullet["ttl"] <= 0:
                bullets.pop(i)

        for i in range(len(enemy_bullets) - 1, -1, -1):
            bullet = enemy_bullets[i]
            bullet["prev"] = pygame.Vector2(bullet["pos"])
            bullet["pos"] += bullet["vel"] * dt
            bullet["ttl"] -= dt
            if bullet["ttl"] <= 0:
                enemy_bullets.pop(i)

        for asteroid in asteroids:
            asteroid.prev = pygame.Vector2(asteroid.pos)
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
                    enemies.append(spawn_enemy_near(rng, ship_pos))
        despawn_sq = ENEMY_DESPAWN_RADIUS * ENEMY_DESPAWN_RADIUS
        for enemy in enemies[:]:
            if (enemy.pos - ship_pos).length_squared() > despawn_sq:
                enemies.remove(enemy)

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

        for enemy in enemies:
            enemy.prev = pygame.Vector2(enemy.pos)
            to_player = ship_pos - enemy.pos
            dist_sq = to_player.length_squared()
            pursuing = dist_sq <= ENEMY_PURSUE_RADIUS * ENEMY_PURSUE_RADIUS
            if pursuing and dist_sq > 0:
                target_angle = vector_to_angle(to_player)
                enemy.angle = turn_towards(enemy.angle, target_angle, ENEMY_TURN_SPEED * dt)
                speed = ENEMY_PURSUE_SPEED
            else:
                enemy.wander_timer -= dt
                if enemy.wander_timer <= 0:
                    enemy.wander_timer = random.uniform(0.8, 2.2)
                    enemy.wander_angle = (enemy.angle + random.uniform(-120, 120)) % 360
                enemy.angle = turn_towards(enemy.angle, enemy.wander_angle, ENEMY_TURN_SPEED * dt * 0.6)
                speed = ENEMY_SCOUT_SPEED

            enemy.vel = angle_to_vector(enemy.angle) * speed
            enemy.pos = enemy.pos + enemy.vel * dt
            if enemy.pos.x < ENEMY_RADIUS:
                enemy.pos.x = ENEMY_RADIUS
                enemy.vel.x = abs(enemy.vel.x)
                enemy.angle = vector_to_angle(enemy.vel)
            elif enemy.pos.x > WORLD_WIDTH - ENEMY_RADIUS:
                enemy.pos.x = WORLD_WIDTH - ENEMY_RADIUS
                enemy.vel.x = -abs(enemy.vel.x)
                enemy.angle = vector_to_angle(enemy.vel)
            if enemy.pos.y < ENEMY_RADIUS:
                enemy.pos.y = ENEMY_RADIUS
                enemy.vel.y = abs(enemy.vel.y)
                enemy.angle = vector_to_angle(enemy.vel)
            elif enemy.pos.y > WORLD_HEIGHT - ENEMY_RADIUS:
                enemy.pos.y = WORLD_HEIGHT - ENEMY_RADIUS
                enemy.vel.y = -abs(enemy.vel.y)
                enemy.angle = vector_to_angle(enemy.vel)
            enemy.fire_timer = max(0.0, enemy.fire_timer - dt)
            if (
                pursuing
                and dist_sq <= ENEMY_FIRE_RANGE * ENEMY_FIRE_RANGE
                and enemy.fire_timer <= 0.0
            ):
                bullet_vel = angle_to_vector(enemy.angle) * ENEMY_BULLET_SPEED + enemy.vel * 0.2
                enemy_bullets.append(
                    {
                        "pos": pygame.Vector2(enemy.pos),
                        "prev": pygame.Vector2(enemy.pos),
                        "vel": bullet_vel,
                        "ttl": ENEMY_BULLET_TTL,
                    }
                )
                enemy.fire_timer = ENEMY_FIRE_COOLDOWN

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
                        lives -= 1
                        last_death_cause = "asteroid"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        if lives <= 0:
                            game_over = True
                        break
                if not game_over:
                    for landmark in landmarks:
                        hit_radius = landmark["radius"] + SHIP_RADIUS
                        if moving_circle_hit(ship_pos, ship_pos, landmark["pos"], landmark["pos"], hit_radius):
                            lives -= 1
                            if landmark.get("kind") == "moon":
                                last_death_cause = "moon"
                            else:
                                last_death_cause = "planet"
                            ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                            ship_vel = pygame.Vector2(0, 0)
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
                    elif pickup.kind == "boost":
                        boost_stock += 1
                    else:
                        rapid_time = 7.0
                    pickups.remove(pickup)
                    break

            for bullet in enemy_bullets[:]:
                if moving_circle_hit(bullet["prev"], bullet["pos"], ship_prev, ship_pos, SHIP_RADIUS + 4):
                    enemy_bullets.remove(bullet)
                    if shield_time <= 0:
                        lives -= 1
                        last_death_cause = "enemy bullet"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        if lives <= 0:
                            game_over = True
                    break

            for enemy in enemies:
                enemy_prev = enemy.prev or enemy.pos
                hit_radius = ENEMY_RADIUS + SHIP_RADIUS
                if moving_circle_hit(enemy_prev, enemy.pos, ship_prev, ship_pos, hit_radius):
                    if shield_time <= 0:
                        lives -= 1
                        last_death_cause = "enemy ship"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        if lives <= 0:
                            game_over = True
                    break

            for asteroid in asteroids[:]:
                asteroid_prev = asteroid.prev or asteroid.pos
                hit_radius = asteroid.radius + SHIP_RADIUS
                if moving_circle_hit(ship_prev, ship_pos, asteroid_prev, asteroid.pos, hit_radius):
                    if shield_time <= 0:
                        lives -= 1
                        last_death_cause = "asteroid"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
                        if lives <= 0:
                            game_over = True
                    break

            for bullet in bullets[:]:
                hit_enemy = None
                for enemy in enemies:
                    enemy_prev = enemy.prev or enemy.pos
                    bullet_prev = bullet.get("prev", bullet["pos"])
                    radius = ENEMY_RADIUS + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], enemy_prev, enemy.pos, radius):
                        hit_enemy = enemy
                        break
                if hit_enemy:
                    bullets.remove(bullet)
                    if hit_enemy.shield > 0:
                        hit_enemy.shield -= 1
                    else:
                        enemies.remove(hit_enemy)
                        score += 100
                    continue

                hit_canister = None
                for pickup in pickups:
                    if pickup.kind != "boost_canister":
                        continue
                    bullet_prev = bullet.get("prev", bullet["pos"])
                    radius = CANISTER_RADIUS + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], pickup.pos, pickup.pos, radius):
                        hit_canister = pickup
                        break
                if hit_canister:
                    bullets.remove(bullet)
                    hit_canister.shell_hp = max(0, hit_canister.shell_hp - 1)
                    if hit_canister.shell_hp <= 0:
                        hit_canister.kind = "boost"
                        hit_canister.shell_hp = 0
                    continue

                hit = None
                for asteroid in asteroids:
                    asteroid_prev = asteroid.prev or asteroid.pos
                    bullet_prev = bullet.get("prev", bullet["pos"])
                    radius = asteroid.radius + BULLET_HIT_SLOP
                    if moving_circle_hit(bullet_prev, bullet["pos"], asteroid_prev, asteroid.pos, radius):
                        hit = asteroid
                        break
                if hit:
                    bullets.remove(bullet)
                    asteroids.remove(hit)
                    score += 10 * hit.size
                    if hit.size > 1:
                        rng = random.Random(seed + score + int(hit.pos.x))
                        for _ in range(2):
                            child = spawn_asteroid(rng, hit.size - 1, avoid_center=False)
                            child.pos = pygame.Vector2(hit.pos)
                            child.vel = hit.vel.rotate(rng.uniform(-50, 50)) * 1.2
                            asteroids.append(child)
                    break

            for enemy in enemies[:]:
                if enemy.shield > 0:
                    continue
                enemy_prev = enemy.prev or enemy.pos
                for asteroid in asteroids:
                    asteroid_prev = asteroid.prev or asteroid.pos
                    hit_radius = asteroid.radius + ENEMY_RADIUS
                    if moving_circle_hit(enemy_prev, enemy.pos, asteroid_prev, asteroid.pos, hit_radius):
                        enemies.remove(enemy)
                        score += 100
                        break

            for landmark in landmarks:
                hit_radius = landmark["radius"] + SHIP_RADIUS
                if moving_circle_hit(ship_prev, ship_pos, landmark["pos"], landmark["pos"], hit_radius):
                    if shield_time <= 0:
                        lives -= 1
                        if landmark.get("kind") == "moon":
                            last_death_cause = "moon"
                        else:
                            last_death_cause = "planet"
                        ship_pos = pygame.Vector2(WORLD_WIDTH / 2, WORLD_HEIGHT / 2)
                        ship_vel = pygame.Vector2(0, 0)
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
                asteroid_prev = asteroid.prev or asteroid.pos
                hit_radius = asteroid.radius + landmark["radius"]
                if moving_circle_hit(asteroid_prev, asteroid.pos, landmark["pos"], landmark["pos"], hit_radius):
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

        for star in stars:
            delta = toroidal_delta_world(ship_pos, star["pos"])
            screen_pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2) + delta * STAR_PARALLAX
            screen_pos.x %= WIDTH
            screen_pos.y %= HEIGHT
            color = (star["brightness"], star["brightness"], star["brightness"])
            pygame.draw.circle(
                screen,
                color,
                (int(screen_pos.x), int(screen_pos.y)),
                star["size"],
            )

        for landmark in landmarks:
            screen_pos = world_to_screen(landmark["pos"], ship_pos)
            draw_radius = landmark["radius"] * CAMERA_ZOOM
            pygame.draw.circle(
                screen,
                landmark["color"],
                (int(screen_pos.x), int(screen_pos.y)),
                max(1, int(draw_radius)),
                2,
            )
            if landmark.get("kind") == "planet":
                on_screen = (
                    -draw_radius <= screen_pos.x <= WIDTH + draw_radius
                    and -draw_radius <= screen_pos.y <= HEIGHT + draw_radius
                )
                if on_screen:
                    discovered_planets.add(landmark.get("id"))

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

        for enemy in enemies:
            screen_pos = world_to_screen(enemy.pos, ship_pos)
            if enemy.shield > 0:
                shield_radius = (ENEMY_RADIUS + 8) * CAMERA_ZOOM
                pygame.draw.circle(
                    screen,
                    COLORS["enemy_shield"],
                    (int(screen_pos.x), int(screen_pos.y)),
                    max(1, int(shield_radius)),
                    1,
                )
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
            elif pickup.kind == "boost":
                color = COLORS["pickup_boost"]
            else:
                color = COLORS["pickup_rapid"]
            pickup_radius = max(2, int(PICKUP_RADIUS * CAMERA_ZOOM))
            core_radius = max(1, int((PICKUP_RADIUS * 0.25) * CAMERA_ZOOM))
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), pickup_radius, 2)
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), core_radius, 0)

        if shield_time > 0:
            shield_screen_pos = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
            shield_radius = SHIP_RADIUS * CAMERA_ZOOM + 10 * CAMERA_ZOOM
            pygame.draw.circle(
                screen,
                COLORS["pickup_shield"],
                (int(shield_screen_pos.x), int(shield_screen_pos.y)),
                max(1, int(shield_radius)),
                1,
            )

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
        draw_ship(screen, pygame.Vector2(WIDTH / 2, HEIGHT / 2), ship_angle, ship_color)

        nearest_planet = None
        nearest_dist_sq = None
        for landmark in landmarks:
            if landmark["kind"] != "planet":
                continue
            delta = landmark["pos"] - ship_pos
            dist_sq = delta.length_squared()
            if nearest_dist_sq is None or dist_sq < nearest_dist_sq:
                nearest_dist_sq = dist_sq
                nearest_planet = delta
        if nearest_planet is not None:
            draw_edge_arrow(screen, nearest_planet, COLORS["planet"])

        if show_gamepad_debug:
            lines = [
                f"Gamepad: {joy_name}",
                f"Axes: {joy_axes}  Buttons: {joy_buttons}  Hats: {joy_hats}",
            ]
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

        hud = [
            f"Seed: {seed}",
            f"Score: {score}",
            f"Lives: {lives}",
            f"Shield: {shield_time:.1f}s" if shield_time > 0 else "Shield: -",
            f"Shield Stock: {shield_stock}",
            f"Rapid: {rapid_time:.1f}s" if rapid_time > 0 else "Rapid: -",
            f"Boost: {boost_time:.1f}s" if boost_time > 0 else "Boost: -",
            f"Boost Stock: {boost_stock}",
        ]
        if show_gamepad_debug:
            hud.append(f"Last Death: {last_death_cause}" if last_death_cause else "Last Death: -")
        for i, line in enumerate(hud):
            text = font.render(line, True, COLORS["ui"])
            screen.blit(text, (10, 10 + i * 20))

        help_text = "Arrows/WASD move  Space shoot  R shield  F boost  M map  Q stop  F5 save  L load  N new seed"
        text = font.render(help_text, True, COLORS["ui"])
        screen.blit(text, (10, HEIGHT - 28))

        if game_over:
            if last_death_cause:
                msg_text = f"Game Over - {last_death_cause} - press N for new seed"
            else:
                msg_text = "Game Over - press N for new seed"
            msg = font.render(msg_text, True, COLORS["warning"])
            screen.blit(msg, (WIDTH / 2 - msg.get_width() / 2, HEIGHT / 2))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
