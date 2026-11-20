"""Deterministic Python Reference Mirror of the Phase 1 (1982 Dig Dug Replica) C99 Engine.

Matches the exact integer Q12.4 fixed-point constants, 28x28 cell / 14x14 tile grid,
quadrant mask derivation, scoring tables, rock state machine, pump/deflate rules,
and Pooka/Fygar/escape AI implemented in `src/{world,score,actors,combat}/`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FP_SHIFT = 4
FP_ONE_PX = 16
FP_TILE_16 = 256

DIR_RIGHT, DIR_UP, DIR_LEFT, DIR_DOWN = 0, 1, 2, 3

PUMP_BASE_PTS = (200, 300, 400, 500)
ROCK_CRUSH_PTS = (0, 1000, 2500, 4000, 6000, 8000, 10000, 12000, 15000)


def stratum_for_y(py: int) -> int:
    if py < 64:
        return 0
    if py < 128:
        return 1
    if py < 176:
        return 2
    return 3


def score_for_pump_kill(stratum: int, is_fygar: bool, fygar_horizontal: bool) -> int:
    pts = PUMP_BASE_PTS[min(max(stratum, 0), 3)]
    return pts * 2 if (is_fygar and fygar_horizontal) else pts


def score_for_rock_crush(monsters_crushed: int) -> int:
    if monsters_crushed <= 0:
        return 0
    return ROCK_CRUSH_PTS[min(monsters_crushed, 8)]


def score_for_round_vegetable(round_num: int) -> int:
    if round_num <= 1:
        return 400
    if round_num == 2:
        return 600
    if round_num == 3:
        return 800
    if round_num <= 5:
        return 1000
    if round_num <= 7:
        return 2000
    if round_num <= 9:
        return 3000
    if round_num <= 11:
        return 4000
    if round_num <= 13:
        return 5000
    if round_num <= 15:
        return 6000
    if round_num <= 17:
        return 7000
    return 8000


@dataclass
class EnemySim:
    kind: str  # "pooka" or "fygar"
    x_fp: int
    y_fp: int
    dir: int = DIR_RIGHT
    horiz_facing: int = DIR_RIGHT
    state: str = "tunnel"  # tunnel, ghost, inhale, fire, inflated, popping, rock_held, dead, escaped
    inflate_stage: int = 0
    deflate_timer: int = 0
    phase_cooldown: int = 180
    fire_cooldown: int = 150
    state_timer: int = 0
    escaping: bool = False
    crushing_rock: int = -1


@dataclass
class RockSim:
    x_fp: int
    y_fp: int
    state: str = "supported"  # supported, held_by_player, wobble, falling, shatter, retired
    fall_start_y_px: int = 0
    state_timer: int = 0
    crushed_count: int = 0
    crushed_player: bool = False


@dataclass
class Phase1WorldSim:
    round_num: int = 1
    cells: list[list[int]] = field(default_factory=lambda: [[0 if r < 2 else 1 for _ in range(28)] for r in range(28)])
    tile_mask: list[list[int]] = field(default_factory=lambda: [[0] * 14 for _ in range(14)])
    px_fp: int = 96 * FP_ONE_PX
    py_fp: int = 112 * FP_ONE_PX
    p_dir: int = DIR_RIGHT
    p_state: str = "alive"
    p_moving: bool = False
    p_digging: bool = False
    harpoon_extending: bool = False
    harpoon_latched: bool = False
    harpoon_len_px: int = 0
    harpoon_target: int = -1
    harpoon_hold_timer: int = 0
    score: int = 0
    lives: int = 3
    extra_life_flags: int = 0
    rocks_dropped: int = 0
    veggie_active: bool = False
    veggie_pts: int = 0
    hurry_up: bool = False
    enemies: list[EnemySim] = field(default_factory=list)
    rocks: list[RockSim] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.round_num > 255:
            self.round_num = 13 + ((self.round_num - 256) & 7)
        self.carve_tile_box(6, 0, 1, 8)
        self.carve_tile_box(5, 7, 3, 1)
        self.recompute_all_masks()

    def recompute_tile_mask(self, tx: int, ty: int) -> None:
        cx, cy = tx * 2, ty * 2
        m = 0
        if self.cells[cy][cx]:
            m |= 1
        if self.cells[cy][cx + 1]:
            m |= 2
        if self.cells[cy + 1][cx]:
            m |= 4
        if self.cells[cy + 1][cx + 1]:
            m |= 8
        self.tile_mask[ty][tx] = m

    def recompute_all_masks(self) -> None:
        for ty in range(14):
            for tx in range(14):
                self.recompute_tile_mask(tx, ty)

    def cell_solid(self, cx: int, cy: int) -> bool:
        if 0 <= cx < 28 and 0 <= cy < 28:
            return self.cells[cy][cx] != 0
        return False

    def tile_open(self, tx: int, ty: int) -> bool:
        if 0 <= tx < 14 and 0 <= ty < 14:
            return self.tile_mask[ty][tx] == 0
        return False

    def carve_cell(self, cx: int, cy: int) -> int:
        if 0 <= cx < 28 and 0 <= cy < 28 and self.cells[cy][cx] != 0:
            self.cells[cy][cx] = 0
            self.recompute_tile_mask(cx >> 1, cy >> 1)
            return 1
        return 0

    def carve_footprint_16x16(self, px: int, py: int) -> int:
        dug = 0
        for cy in range((py + 2) >> 3, ((py + 13) >> 3) + 1):
            for cx in range((px + 2) >> 3, ((px + 13) >> 3) + 1):
                dug += self.carve_cell(cx, cy)
        return dug

    def carve_tile_box(self, tx: int, ty: int, w: int, h: int) -> None:
        for dy in range(h):
            for dx in range(w):
                x, y = tx + dx, ty + dy
                if 0 <= x < 14 and 0 <= y < 14:
                    self.cells[y * 2][x * 2] = 0
                    self.cells[y * 2][x * 2 + 1] = 0
                    self.cells[y * 2 + 1][x * 2] = 0
                    self.cells[y * 2 + 1][x * 2 + 1] = 0
                    self.tile_mask[y][x] = 0

    def award(self, pts: int) -> None:
        self.score += pts
        if not (self.extra_life_flags & 1) and self.score >= 20000:
            self.extra_life_flags |= 1
            self.lives += 1
        if not (self.extra_life_flags & 2) and self.score >= 60000:
            self.extra_life_flags |= 2
            self.lives += 1

    def alive_enemies(self) -> list[EnemySim]:
        return [e for e in self.enemies if e.state not in ("dead", "escaped")]

    def step(self, move_dir: int | None = None, btn_a_held: bool = False, btn_a_pressed: bool = False) -> None:
        # 1. Player movement & digging
        self.p_moving = False
        self.p_digging = False
        if self.p_state in ("alive", "pumping"):
            if move_dir is not None and self.harpoon_latched:
                self.harpoon_latched = False
                self.harpoon_extending = False
                self.harpoon_len_px = 0
                self.p_state = "alive"

            if not self.harpoon_extending and not self.harpoon_latched and move_dir is not None:
                d = move_dir
                px, py = self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT
                if d in (DIR_LEFT, DIR_RIGHT) and (py & 15) != 0:
                    rem = py & 15
                    d = DIR_UP if rem <= 5 else (DIR_DOWN if rem >= 11 else self.p_dir)
                elif d in (DIR_UP, DIR_DOWN) and (px & 15) != 0:
                    rem = px & 15
                    d = DIR_LEFT if rem <= 5 else (DIR_RIGHT if rem >= 11 else self.p_dir)

                if d in (DIR_LEFT, DIR_RIGHT):
                    self.py_fp = ((py + 8) & ~15) * FP_ONE_PX
                else:
                    self.px_fp = ((px + 8) & ~15) * FP_ONE_PX

                ppx, ppy = self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT
                dx = 2 if d == DIR_RIGHT else (-2 if d == DIR_LEFT else 0)
                dy = 2 if d == DIR_DOWN else (-2 if d == DIR_UP else 0)
                hits_dirt = any(
                    self.cell_solid((ppx + dx + ox) >> 3, (ppy + dy + oy) >> 3)
                    for ox in (2, 13)
                    for oy in (2, 13)
                )
                spd = 14 if hits_dirt else 20
                nx = max(0, min(208 * FP_ONE_PX, self.px_fp + (spd if d == DIR_RIGHT else (-spd if d == DIR_LEFT else 0))))
                ny = max(0, min(208 * FP_ONE_PX, self.py_fp + (spd if d == DIR_DOWN else (-spd if d == DIR_UP else 0))))
                self.p_dir = d
                self.p_moving = (nx != self.px_fp) or (ny != self.py_fp)
                self.px_fp, self.py_fp = nx, ny
                dug = self.carve_footprint_16x16(self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT)
                if dug:
                    self.p_digging = True
                    self.award(dug * 10)

            # Veggie pickup
            if self.veggie_active:
                px, py = self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT
                if px + 14 > 96 and px + 2 < 112 and py + 14 > 112 and py + 2 < 128:
                    self.award(self.veggie_pts)
                    self.veggie_active = False

        # 2. Harpoon & Pump
        if self.p_state in ("alive", "pumping"):
            if self.harpoon_latched:
                e = self.enemies[self.harpoon_target]
                if e.state != "inflated":
                    self.harpoon_latched = False
                    self.p_state = "alive"
                elif btn_a_pressed:
                    self.harpoon_hold_timer = 18
                    self._inflate_once(self.harpoon_target)
                elif btn_a_held:
                    if self.harpoon_hold_timer > 0:
                        self.harpoon_hold_timer -= 1
                    else:
                        self.harpoon_hold_timer = 18
                        self._inflate_once(self.harpoon_target)
            elif self.harpoon_extending:
                self.harpoon_len_px += 4
                px, py = self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT
                tx = px + 8 + ((6 + self.harpoon_len_px) if self.p_dir == DIR_RIGHT else (-(6 + self.harpoon_len_px) if self.p_dir == DIR_LEFT else 0))
                ty = py + 8 + ((6 + self.harpoon_len_px) if self.p_dir == DIR_DOWN else (-(6 + self.harpoon_len_px) if self.p_dir == DIR_UP else 0))
                hit = -1
                for idx, e in enumerate(self.enemies):
                    if e.state in ("dead", "popping", "rock_held", "escaped"):
                        continue
                    ex, ey = e.x_fp >> FP_SHIFT, e.y_fp >> FP_SHIFT
                    if e.state == "ghost" and self.cell_solid((ex + 8) >> 3, (ey + 8) >> 3):
                        continue
                    if ex <= tx <= ex + 16 and ey <= ty <= ey + 16:
                        hit = idx
                        break
                if hit >= 0:
                    self.harpoon_extending = False
                    self.harpoon_latched = True
                    self.harpoon_target = hit
                    self.harpoon_hold_timer = 18
                    self.p_state = "pumping"
                    self._inflate_once(hit)
                elif self.harpoon_len_px >= 32 or (self.harpoon_len_px > 8 and self.cell_solid(tx >> 3, ty >> 3)):
                    self.harpoon_extending = False
                    self.harpoon_len_px = 0
                    self.p_state = "alive"
            elif btn_a_pressed:
                self.harpoon_extending = True
                self.harpoon_len_px = 4
                self.p_state = "pumping"

        # 3. Rocks
        for r_idx, rk in enumerate(self.rocks):
            if rk.state == "retired":
                continue
            rx, ry = rk.x_fp >> FP_SHIFT, rk.y_fp >> FP_SHIFT
            supported = (ry + 16 >= 224) or self.cell_solid((rx + 2) >> 3, (ry + 16) >> 3) or self.cell_solid((rx + 13) >> 3, (ry + 16) >> 3)
            px, py = self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT
            held_below = self.p_state not in ("dead", "dying") and (px + 14 > rx and px + 2 < rx + 16 and ry + 10 <= py <= ry + 20)

            if rk.state == "supported" and not supported:
                if held_below:
                    rk.state = "held_by_player"
                else:
                    rk.state = "wobble"
                    rk.state_timer = 32
                    rk.fall_start_y_px = ry
                    self.carve_tile_box(rx >> 4, ry >> 4, 1, 1)
            elif rk.state == "held_by_player" and not held_below:
                rk.state = "wobble"
                rk.state_timer = 32
                rk.fall_start_y_px = ry
                self.carve_tile_box(rx >> 4, ry >> 4, 1, 1)
            elif rk.state == "wobble":
                if rk.state_timer > 0:
                    rk.state_timer -= 1
                else:
                    rk.state = "falling"
                    rk.crushed_count = 0
                    rk.crushed_player = False
            elif rk.state == "falling":
                rk.y_fp += 40
                ry = rk.y_fp >> FP_SHIFT
                self.carve_footprint_16x16(rx, ry)
                for e in self.enemies:
                    if e.state in ("dead", "escaped"):
                        continue
                    if e.state == "rock_held":
                        if e.crushing_rock == r_idx:
                            e.y_fp = rk.y_fp
                        continue
                    ex, ey = e.x_fp >> FP_SHIFT, e.y_fp >> FP_SHIFT
                    if ex + 14 > rx and ex + 2 < rx + 16 and ey + 14 > ry and ey + 2 < ry + 16:
                        e.state = "rock_held"
                        e.crushing_rock = r_idx
                        e.y_fp = rk.y_fp
                        rk.crushed_count += 1
                if self.p_state in ("alive", "pumping") and px + 13 > rx and px + 3 < rx + 16 and py + 13 > ry and py + 3 < ry + 16:
                    self.p_state = "crushed"
                    rk.crushed_player = True
                hit_floor = (ry >= 208) or ((ry - rk.fall_start_y_px >= 12) and (self.cell_solid((rx + 2) >> 3, (ry + 16) >> 3) or self.cell_solid((rx + 13) >> 3, (ry + 16) >> 3)))
                if hit_floor:
                    rk.state = "shatter"
                    rk.state_timer = 20
                    for e in self.enemies:
                        if e.state == "rock_held" and e.crushing_rock == r_idx:
                            e.state = "dead"
                    self.award(score_for_rock_crush(rk.crushed_count))
                    if rk.crushed_player:
                        self.p_state = "dying"
                    self.rocks_dropped += 1
                    if self.rocks_dropped == 2:
                        self.veggie_active = True
                        self.veggie_pts = score_for_round_vegetable(self.round_num)
            elif rk.state == "shatter":
                if rk.state_timer > 0:
                    rk.state_timer -= 1
                else:
                    rk.state = "retired"

        # 4. Enemies
        alive = self.alive_enemies()
        if len(alive) == 1:
            self.hurry_up = True
            alive[0].escaping = True

        px, py = self.px_fp >> FP_SHIFT, self.py_fp >> FP_SHIFT
        for idx, e in enumerate(self.enemies):
            if e.state in ("dead", "escaped", "rock_held"):
                continue
            if e.state == "popping":
                if e.state_timer > 0:
                    e.state_timer -= 1
                else:
                    e.state = "dead"
                continue
            if e.state == "inflated":
                actively_held = self.harpoon_latched and self.harpoon_target == idx and btn_a_held
                if not actively_held:
                    if e.deflate_timer > 0:
                        e.deflate_timer -= 1
                    else:
                        e.inflate_stage -= 1
                        e.deflate_timer = 36
                        if e.inflate_stage <= 0:
                            e.inflate_stage = 0
                            e.state = "tunnel"
                            if self.harpoon_latched and self.harpoon_target == idx:
                                self.harpoon_latched = False
                                self.p_state = "alive"
                continue  # Harmless pass-through!

            ex, ey = e.x_fp >> FP_SHIFT, e.y_fp >> FP_SHIFT
            if e.escaping and ex <= 2 and ey <= 2:
                e.state = "escaped"
                continue

            if e.state == "inhale":
                if e.state_timer > 0:
                    e.state_timer -= 1
                else:
                    e.state = "fire"
                    e.state_timer = 24
                continue
            if e.state == "fire":
                fx0 = ex + 16 if e.horiz_facing == DIR_RIGHT else ex - 48
                fx1 = ex + 64 if e.horiz_facing == DIR_RIGHT else ex
                if px + 12 > fx0 and px + 4 < fx1 and py + 12 > ey and py + 4 < ey + 16:
                    if self.p_state in ("alive", "pumping"):
                        self.p_state = "dying"
                if e.state_timer > 0:
                    e.state_timer -= 1
                else:
                    e.state = "tunnel"
                    e.fire_cooldown = 180
                continue

            tx_px = (0 if ey <= 2 else ex) if e.escaping else px
            ty_px = 0 if e.escaping else py
            if e.state == "ghost":
                e.state_timer += 1
                if tx_px > ex:
                    e.x_fp = min(208 * FP_ONE_PX, e.x_fp + 11)
                elif tx_px < ex:
                    e.x_fp = max(0, e.x_fp - 11)
                if ty_px > ey:
                    e.y_fp = min(208 * FP_ONE_PX, e.y_fp + 11)
                elif ty_px < ey:
                    e.y_fp = max(0, e.y_fp - 11)
                ex, ey = e.x_fp >> FP_SHIFT, e.y_fp >> FP_SHIFT
                if e.state_timer >= 24 and (ex & 15) <= 2 and (ey & 15) <= 2 and self.tile_open((ex + 4) >> 4, (ey + 4) >> 4):
                    e.x_fp = ((ex + 4) >> 4) * FP_TILE_16
                    e.y_fp = ((ey + 4) >> 4) * FP_TILE_16
                    e.state = "tunnel"
                    e.phase_cooldown = 240
            else:
                if e.kind == "fygar" and not e.escaping:
                    if e.fire_cooldown > 0:
                        e.fire_cooldown -= 1
                    elif (ey & 15) == 0 and e.dir in (DIR_LEFT, DIR_RIGHT):
                        e.state = "inhale"
                        e.state_timer = 24
                        continue
                if e.phase_cooldown > 0:
                    e.phase_cooldown -= 1
                elif not (e.escaping and ey == 0):
                    e.state = "ghost"
                    e.state_timer = 0
                    continue

                dirs_xy = ((1, 0), (0, -1), (-1, 0), (0, 1))
                if (ex & 15) == 0 and (ey & 15) == 0:
                    tx, ty = ex >> 4, ey >> 4
                    if e.escaping and ty == 0:
                        e.dir = DIR_LEFT
                        e.horiz_facing = DIR_LEFT
                    else:
                        rev = (e.dir + 2) & 3
                        best = (10**9, -1)
                        for cand, (ddx, ddy) in enumerate(dirs_xy):
                            if cand == rev:
                                continue
                            if self.tile_open(tx + ddx, ty + ddy):
                                dist = abs((tx + ddx) * 16 - tx_px) + abs((ty + ddy) * 16 - ty_px)
                                if dist < best[0]:
                                    best = (dist, cand)
                        if best[1] >= 0:
                            e.dir = best[1]
                        elif self.tile_open(tx + dirs_xy[rev][0], ty + dirs_xy[rev][1]):
                            e.dir = rev
                        elif e.escaping and ey > 0:
                            e.state = "ghost"
                            e.state_timer = 0
                            continue
                        if e.dir in (DIR_LEFT, DIR_RIGHT):
                            e.horiz_facing = e.dir

                can_advance = True
                if (ex & 15) == 0 and (ey & 15) == 0:
                    ddx, ddy = dirs_xy[e.dir]
                    can_advance = self.tile_open((ex >> 4) + ddx, (ey >> 4) + ddy)

                if can_advance:
                    spd = (22 if self.hurry_up else 18) if e.kind == "pooka" else (20 if self.hurry_up else 16)
                    if e.dir == DIR_RIGHT:
                        e.x_fp = min(208 * FP_ONE_PX, min(((ex >> 4) + 1) * FP_TILE_16, e.x_fp + spd))
                    elif e.dir == DIR_LEFT:
                        e.x_fp = max(0, max((((ex - 1) >> 4) * FP_TILE_16) if ex > 0 else 0, e.x_fp - spd))
                    elif e.dir == DIR_UP:
                        e.y_fp = max(0, max((((ey - 1) >> 4) * FP_TILE_16) if ey > 0 else 0, e.y_fp - spd))
                    elif e.dir == DIR_DOWN:
                        e.y_fp = min(208 * FP_ONE_PX, min(((ey >> 4) + 1) * FP_TILE_16, e.y_fp + spd))

            ex, ey = e.x_fp >> FP_SHIFT, e.y_fp >> FP_SHIFT
            if px + 12 > ex and px + 4 < ex + 16 and py + 12 > ey and py + 4 < ey + 16:
                if self.p_state in ("alive", "pumping"):
                    self.p_state = "dying"

    def _inflate_once(self, idx: int) -> None:
        e = self.enemies[idx]
        e.inflate_stage += 1
        e.deflate_timer = 36
        if e.inflate_stage >= 4:
            e.state = "popping"
            e.state_timer = 18
            ey = e.y_fp >> FP_SHIFT
            self.award(score_for_pump_kill(stratum_for_y(ey), e.kind == "fygar", e.dir in (DIR_LEFT, DIR_RIGHT)))
            self.harpoon_latched = False
            self.harpoon_extending = False
            self.harpoon_len_px = 0
            self.p_state = "alive"
        else:
            e.state = "inflated"
