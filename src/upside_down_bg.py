import pygame
import math
import random

# ---------------------------------------------------------------------------
# Upside Down Background  –  atmospheric teal/blue top-down view
#
# Usage:
#   from upside_down_bg import UpsideDownBackground
#   bg = UpsideDownBackground(seed=42)
#
#   In _draw_game, REPLACE self._draw_grid() with:
#   bg.draw(screen, player.world_x, player.world_y)
# ---------------------------------------------------------------------------

C_VOID        = (5, 5, 8)
C_GROUND_BASE = (18, 16, 20)
C_GROUND_MID  = (28, 24, 30)
C_GROUND_HI   = (40, 34, 42)
C_CRACK       = (8, 8, 10)
C_VINE        = (30, 32, 36)
C_VINE_NODE   = (50, 55, 60)
C_SPORE       = (90, 110, 120)
C_GLOW_INNER  = (40, 60, 70)
C_GLOW_MID    = (20, 30, 40)
C_VIGNETTE    = (2, 2, 4)


def _hex(c, a=255):
    return (*c, a)


class UpsideDownBackground:
    def __init__(self, tile_size: int = 120, seed: int = 0):
        self.tile_size = tile_size
        rng = random.Random(seed)

        t = tile_size
        self._tile = self._build_ground_tile(t, rng)

        BIG = t * 3
        self._big_tile = self._build_big_tile(BIG, rng)

        VP = 500
        self._vine_period = VP
        self._vines = self._gen_vines(VP, rng)

        PP = 700
        self._particle_period = PP
        self._particles = self._gen_particles(PP, rng)

        GP = 900
        self._glow_period = GP
        self._glows = self._gen_glows(GP, rng)
        self._glow_cache: dict = {}

        self._vignette = None
        self._vignette_size = (0, 0)

    def _build_ground_tile(self, t, rng):
        surf = pygame.Surface((t, t))
        surf.fill(C_GROUND_BASE)

        # uneven wet ground patches
        for _ in range(8):
            pw = rng.randint(12, 40)
            ph = rng.randint(4, 18)
            px = rng.randint(0, t - pw)
            py = rng.randint(0, t - ph)
            alpha = rng.randint(30, 90)
            patch = pygame.Surface((pw, ph), pygame.SRCALPHA)
            patch.fill(_hex(C_GROUND_MID, alpha))
            surf.blit(patch, (px, py))

        # wet highlight streaks
        for _ in range(4):
            sw = rng.randint(2, 8)
            sh = rng.randint(20, 55)
            sx = rng.randint(0, t - sw)
            sy = rng.randint(0, t - sh)
            alpha = rng.randint(20, 60)
            streak = pygame.Surface((sw, sh), pygame.SRCALPHA)
            streak.fill(_hex(C_GROUND_HI, alpha))
            surf.blit(streak, (sx, sy))

        # cracks
        for _ in range(rng.randint(4, 8)):
            x1, y1 = rng.randint(0, t), rng.randint(0, t)
            x2 = x1 + rng.randint(-30, 30)
            y2 = y1 + rng.randint(-30, 30)
            alpha = rng.randint(60, 130)
            crack = pygame.Surface((t, t), pygame.SRCALPHA)
            pygame.draw.line(crack, _hex(C_CRACK, alpha), (x1, y1), (x2, y2), 1)
            surf.blit(crack, (0, 0))

        pygame.draw.line(surf, C_CRACK, (0, 0), (t, 0), 1)
        pygame.draw.line(surf, C_CRACK, (0, 0), (0, t), 1)
        return surf

    def _build_big_tile(self, BIG, rng):
        surf = pygame.Surface((BIG, BIG))
        surf.fill(C_VOID)

        blob_surf = pygame.Surface((BIG, BIG), pygame.SRCALPHA)
        for _ in range(12):
            bx = rng.randint(0, BIG)
            by = rng.randint(0, BIG)
            brx = rng.randint(40, 140)
            bry = rng.randint(20, 80)
            alpha = rng.randint(20, 60)
            pygame.draw.ellipse(blob_surf, _hex(C_GROUND_BASE, alpha),
                                (bx - brx, by - bry, brx * 2, bry * 2))
        surf.blit(blob_surf, (0, 0))

        hi_surf = pygame.Surface((BIG, BIG), pygame.SRCALPHA)
        for _ in range(6):
            bx = rng.randint(0, BIG)
            by = rng.randint(0, BIG)
            brx = rng.randint(20, 70)
            bry = rng.randint(10, 40)
            alpha = rng.randint(10, 35)
            pygame.draw.ellipse(hi_surf, _hex(C_GROUND_HI, alpha),
                                (bx - brx, by - bry, brx * 2, bry * 2))
        surf.blit(hi_surf, (0, 0))
        return surf

    def _gen_vines(self, period, rng):
        vines = []
        for _ in range(18):
            x = rng.uniform(0, period)
            y = rng.uniform(0, period)
            pts = [(x, y)]
            nodes = []
            for s in range(rng.randint(6, 14)):
                dx = rng.uniform(-40, 40)
                dy = rng.uniform(-40, 40)
                pts.append((pts[-1][0] + dx, pts[-1][1] + dy))
                if rng.random() < 0.35:
                    nodes.append(len(pts) - 1)
            w = rng.choice([1, 1, 1, 2])
            vines.append((pts, w, nodes))
        return vines

    def _gen_particles(self, period, rng):
        particles = []
        for _ in range(60):
            px = rng.uniform(0, period)
            py = rng.uniform(0, period)
            pr = rng.uniform(1.0, 3.0)
            pa = rng.uniform(0.3, 0.85)
            pelong = rng.uniform(1.0, 2.5)
            particles.append((px, py, pr, pa, pelong))
        return particles

    def _gen_glows(self, period, rng):
        glows = []
        for _ in range(8):
            gx = rng.uniform(0, period)
            gy = rng.uniform(0, period)
            gr = rng.randint(35, 100)
            glows.append((gx, gy, gr))
        return glows

    def _get_glow_surf(self, radius: int) -> pygame.Surface:
        if radius not in self._glow_cache:
            d = radius * 2
            s = pygame.Surface((d, d), pygame.SRCALPHA)
            for r in range(radius, 0, -4):
                t_val = r / radius
                alpha = int(55 * (1 - t_val) ** 1.6)
                col = (
                    int(C_GLOW_INNER[0] * (1 - t_val) + C_GLOW_MID[0] * t_val),
                    int(C_GLOW_INNER[1] * (1 - t_val) + C_GLOW_MID[1] * t_val),
                    int(C_GLOW_INNER[2] * (1 - t_val) + C_GLOW_MID[2] * t_val),
                    max(0, min(255, alpha)),
                )
                pygame.draw.circle(s, col, (radius, radius), r)
            self._glow_cache[radius] = s
        return self._glow_cache[radius]

    def _build_vignette(self, sw, sh):
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        steps = 120
        for i in range(steps, 0, -1):
            t_val = i / steps
            alpha = int(200 * t_val ** 2.2)
            col = _hex(C_VIGNETTE, alpha)
            border = steps - i
            pygame.draw.rect(s, col,
                             (border, border, sw - border * 2, sh - border * 2), 1)
        self._vignette = s
        self._vignette_size = (sw, sh)

    def draw(self, screen: pygame.Surface,
             player_world_x: float, player_world_y: float):

        sw = screen.get_width()
        sh = screen.get_height()
        cx, cy = sw // 2, sh // 2
        t = self.tile_size

        world_left = player_world_x - cx
        world_top  = player_world_y - cy

        # 1. Macro slab layer
        BIG = self._big_tile.get_width()
        bs_col = int(world_left // BIG) - 1
        bs_row = int(world_top  // BIG) - 1
        for col in range(bs_col, bs_col + sw // BIG + 3):
            for row in range(bs_row, bs_row + sh // BIG + 3):
                screen.blit(self._big_tile,
                            (col * BIG - world_left, row * BIG - world_top))

        # 2. Fine ground tile
        start_col = int(world_left // t) - 1
        start_row = int(world_top  // t) - 1
        for col in range(start_col, start_col + sw // t + 3):
            for row in range(start_row, start_row + sh // t + 3):
                screen.blit(self._tile,
                            (col * t - world_left, row * t - world_top))


        # 4. Vines
        vp = self._vine_period
        vx_off = math.fmod(world_left, vp)
        vy_off = math.fmod(world_top,  vp)
        for (pts, width, node_idx) in self._vines:
            for ox in range(-1, 3):
                for oy in range(-1, 3):
                    shifted = [
                        (int(p[0] - vx_off + ox * vp),
                         int(p[1] - vy_off + oy * vp))
                        for p in pts
                    ]
                    xs = [p[0] for p in shifted]
                    ys = [p[1] for p in shifted]
                    if max(xs) < -30 or min(xs) > sw + 30:
                        continue
                    if max(ys) < -30 or min(ys) > sh + 30:
                        continue
                    if len(shifted) >= 2:
                        pygame.draw.lines(screen, C_VINE, False, shifted, width)
                    for ni in node_idx:
                        if 0 <= ni < len(shifted):
                            pygame.draw.circle(screen, C_VINE_NODE, shifted[ni], 2)

        # 5. Spore particles
        pp = self._particle_period
        px_off = math.fmod(world_left, pp)
        py_off = math.fmod(world_top,  pp)
        for (px, py, pr, pa, pelong) in self._particles:
            for ox in range(-1, 3):
                for oy in range(-1, 3):
                    sx = px - px_off + ox * pp
                    sy = py - py_off + oy * pp
                    if 0 <= sx <= sw and 0 <= sy <= sh:
                        r = max(1, int(pr))
                        h = max(1, int(pr * pelong))
                        alpha = int(pa * 255)
                        spore = pygame.Surface((r * 2 + 2, h * 2 + 2), pygame.SRCALPHA)
                        pygame.draw.ellipse(spore, (*C_SPORE, alpha),
                                            (0, 0, r * 2 + 2, h * 2 + 2))
                        screen.blit(spore, (int(sx) - r - 1, int(sy) - h - 1))

        # 7. Vignette
        if self._vignette_size != (sw, sh):
            self._build_vignette(sw, sh)
        screen.blit(self._vignette, (0, 0))
