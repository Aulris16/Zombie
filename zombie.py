import math
import random
import sys
import pygame

WIDTH, HEIGHT = 900, 600
FPS = 60
PLAYER_SPEED = 4.0
BULLET_SPEED = 12
ZOMBIE_SPEED_MIN = 0.6
ZOMBIE_SPEED_MAX = 1.6
SPAWN_INTERVAL = 2000 
ZOMBIE_HEALTH = 3
PLAYER_MAX_HEALTH = 10
LEVEL_COUNT = 3
LEVEL_DURATION = 60000 
FONT_NAME = None
BOSS_HEALTH = 60
BOSS_SPEED = 1.2
BOSS_BULLET_SPEED = 6.0
BOSS_ATTACK_COOLDOWN = 1200 
BOSS_FLEE_THRESHOLD = 20
BOSS_FLEE_SPEED = 2.5

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Shooter - Level Selection")
clock = pygame.time.Clock()
font = pygame.font.SysFont(FONT_NAME, 24)
big_font = pygame.font.SysFont(FONT_NAME, 48)

def vec_from_to(a, b):
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0, 0, 0
    return dx / dist, dy / dist, dist

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.radius = 18
        self.color = (30, 144, 255)
        self.health = PLAYER_MAX_HEALTH
        self.last_shot = 0
        self.shot_cooldown = 180 

    def update(self, dt, keys):
        vel = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            vel.y = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            vel.y = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            vel.x = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            vel.x = 1
        if vel.length_squared() > 0:
            vel = vel.normalize() * PLAYER_SPEED
        self.pos += vel * dt
        self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(HEIGHT - self.radius, self.pos.y))

    def draw(self, surf, mouse_pos):
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        dx, dy, d = vec_from_to(self.pos, mouse_pos)
        gun_len = 26
        end = (int(self.pos.x + dx * gun_len), int(self.pos.y + dy * gun_len))
        pygame.draw.line(surf, (10, 10, 10), (int(self.pos.x), int(self.pos.y)), end, 6)
        self._draw_healthbar(surf)

    def _draw_healthbar(self, surf):
        bar_w = 60
        bar_h = 8
        x = int(self.pos.x - bar_w / 2)
        y = int(self.pos.y - self.radius - 14)
        pygame.draw.rect(surf, (60, 60, 60), (x, y, bar_w, bar_h))
        health_pct = max(0, self.health) / PLAYER_MAX_HEALTH
        pygame.draw.rect(surf, (50, 205, 50), (x + 1, y + 1, int((bar_w - 2) * health_pct), bar_h - 2))

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= self.shot_cooldown

    def shoot(self, target_pos):
        self.last_shot = pygame.time.get_ticks()
        dx, dy, d = vec_from_to(self.pos, target_pos)
        vx = dx * BULLET_SPEED
        vy = dy * BULLET_SPEED
        return Bullet((self.pos.x + dx * 28, self.pos.y + dy * 28), (vx, vy))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, vel):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.radius = 5
        self.lifespan = 2000  # ms
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        self.pos += self.vel * dt
        if pygame.time.get_ticks() - self.spawn_time > self.lifespan:
            self.kill()
        if not (0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT):
            self.kill()

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 215, 0), (int(self.pos.x), int(self.pos.y)), self.radius)


class Zombie(pygame.sprite.Sprite):
    def __init__(self, pos, speed, health):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.radius = 20
        self.color = (34, 139, 34)
        self.speed = speed
        self.health = health

    def update(self, dt, player_pos):
        dx, dy, dist = vec_from_to(self.pos, player_pos)
        if dist > 0:
            self.pos.x += dx * self.speed * dt
            self.pos.y += dy * self.speed * dt

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        eye_offset = 6
        pygame.draw.circle(surf, (0, 0, 0), (int(self.pos.x - eye_offset), int(self.pos.y - 3)), 3)
        pygame.draw.circle(surf, (0, 0, 0), (int(self.pos.x + eye_offset), int(self.pos.y - 3)), 3)


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos, vel):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.radius = 6
        self.lifespan = 4000  # ms
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        self.pos += self.vel * dt
        if pygame.time.get_ticks() - self.spawn_time > self.lifespan:
            self.kill()
        if not (0 <= self.pos.x <= WIDTH and 0 <= self.pos.y <= HEIGHT):
            self.kill()

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 80, 80), (int(self.pos.x), int(self.pos.y)), self.radius)


class Boss(pygame.sprite.Sprite):
    def __init__(self, pos, speed, health):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.speed = speed
        self.health = health
        self.radius = 28
        self.color = (200, 40, 40)
        self.last_attack = 0
        self.fleeing = False
        self.escaped = False

    def can_attack(self):
        return pygame.time.get_ticks() - self.last_attack >= BOSS_ATTACK_COOLDOWN

    def attack(self, target_pos):
        self.last_attack = pygame.time.get_ticks()
        dx, dy, d = vec_from_to(self.pos, target_pos)
        vx = dx * BOSS_BULLET_SPEED
        vy = dy * BOSS_BULLET_SPEED
        return EnemyBullet((self.pos.x + dx * (self.radius + 4), self.pos.y + dy * (self.radius + 4)), (vx, vy))

    def update(self, dt, player_pos):
        if self.fleeing:
            dx, dy, dist = vec_from_to(player_pos, self.pos) 
            self.pos.x += dx * BOSS_FLEE_SPEED * dt
            self.pos.y += dy * BOSS_FLEE_SPEED * dt
            margin = 40
            if (self.pos.x < -margin or self.pos.x > WIDTH + margin or
                self.pos.y < -margin or self.pos.y > HEIGHT + margin):
                self.escaped = True
            return

        dx, dy, dist = vec_from_to(self.pos, player_pos)
        if dist > 0:
            self.pos.x += dx * self.speed * dt
            self.pos.y += dy * self.speed * dt

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(surf, (0, 0, 0), (int(self.pos.x - 8), int(self.pos.y - 4)), 4)
        pygame.draw.circle(surf, (0, 0, 0), (int(self.pos.x + 8), int(self.pos.y - 4)), 4)

class Game:
    def __init__(self, level=1):
        self.player = Player((WIDTH // 2, HEIGHT // 2))
        self.bullets = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.boss = None
        self.last_spawn = 0
        self.score = 0
        self.running = True
        self.game_over = False
        self.level = level
        self.zombies_killed = 0
        self.level_target = 10
        self.level_complete = False
        self.ask_next = False
        self.start_time = pygame.time.get_ticks()
        self.time_left = LEVEL_DURATION
        self.boss_defeated = False
        if self.level == 3:
            self.spawn_boss()

    def spawn_zombie(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            pos = (random.randint(0, WIDTH), -30)
        elif edge == 'bottom':
            pos = (random.randint(0, WIDTH), HEIGHT + 30)
        elif edge == 'left':
            pos = (-30, random.randint(0, HEIGHT))
        else:
            pos = (WIDTH + 30, random.randint(0, HEIGHT))
        speed = random.uniform(ZOMBIE_SPEED_MIN + 0.2 * self.level, ZOMBIE_SPEED_MAX + 0.3 * self.level)
        health = ZOMBIE_HEALTH + self.level - 1
        z = Zombie(pos, speed, health)
        self.zombies.add(z)

    def spawn_boss(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            pos = (random.randint(0, WIDTH), -40)
        elif edge == 'bottom':
            pos = (random.randint(0, WIDTH), HEIGHT + 40)
        elif edge == 'left':
            pos = (-40, random.randint(0, HEIGHT))
        else:
            pos = (WIDTH + 40, random.randint(0, HEIGHT))
        self.boss = Boss(pos, BOSS_SPEED, BOSS_HEALTH)

    def update(self, dt, keys, mouse_pos):
        if self.game_over or self.level_complete:
            return
        
        elapsed = pygame.time.get_ticks() - self.start_time
        self.time_left = max(0, LEVEL_DURATION - elapsed)
        
        if self.level != 3 and self.time_left <= 0:
            self.level_complete = True
            return
        
        self.player.update(dt, keys)
        for b in list(self.bullets):
            b.update(dt)
        for eb in list(self.enemy_bullets):
            eb.update(dt)
        for z in list(self.zombies):
            z.update(dt, self.player.pos)
        if self.level == 3 and self.boss:
            self.boss.update(dt, self.player.pos)
            if (not self.boss.fleeing) and self.boss.can_attack():
                self.enemy_bullets.add(self.boss.attack(self.player.pos))
        now = pygame.time.get_ticks()
        spawn_rate = max(1500, SPAWN_INTERVAL - 200 * self.level)
        if self.level != 3 and now - self.last_spawn > spawn_rate:
            self.spawn_zombie()
            self.last_spawn = now
        if self.level == 3 and self.boss is None:
            if not self.boss_defeated:
                self.spawn_boss()

        for b in list(self.bullets):
            hit_any = False
            for z in list(self.zombies):
                if (b.pos - z.pos).length_squared() <= (b.radius + z.radius) ** 2:
                    z.health -= 1
                    b.kill()
                    hit_any = True
                    if z.health <= 0:
                        z.kill()
                        self.score += 10 * self.level
                        self.zombies_killed += 1
                        if self.level != 3 and self.zombies_killed >= self.level_target:
                            self.level_complete = True
                    break
            if hit_any:
                continue
            if self.level == 3 and self.boss:
                if (b.pos - self.boss.pos).length_squared() <= (b.radius + self.boss.radius) ** 2:
                    self.boss.health -= 1
                    b.kill()
                    if self.boss.health < BOSS_FLEE_THRESHOLD and not self.boss.fleeing:
                        self.boss.fleeing = True
                    if self.boss.health <= 0:
                        self.boss.kill()
                        self.boss = None
                        self.boss_defeated = True
                        self.score += 200
                        self.level_complete = True

        for z in list(self.zombies):
            if (z.pos - self.player.pos).length_squared() <= (z.radius + self.player.radius) ** 2:
                self.player.health -= 1
                if self.player.health <= 0:
                    self.game_over = True
                    break

        if self.level == 3 and self.boss and self.boss.escaped:
            self.level_complete = True

        if not self.game_over:
            for eb in list(self.enemy_bullets):
                if (eb.pos - self.player.pos).length_squared() <= (eb.radius + self.player.radius) ** 2:
                    self.player.health -= 2
                    eb.kill()
                    if self.player.health <= 0:
                        self.game_over = True
                        break

    def draw(self, surf, mouse_pos):
        surf.fill((40, 40, 40))
        
        seconds = self.time_left // 1000
        minutes = seconds // 60
        secs = seconds % 60
        time_str = f"Time: {minutes:02d}:{secs:02d}"
        
        info_text = f"Level {self.level} | Score: {self.score}"
        if self.level != 3:
            info_text += f" | {time_str}"

        info = font.render(info_text, True, (255, 255, 255))
        surf.blit(info, (10, 10))
        for b in self.bullets:
            b.draw(surf)
        for z in self.zombies:
            z.draw(surf)
        if self.level == 3 and self.boss:
            self.boss.draw(surf)
            self._draw_boss_ui(surf, self.boss.health, BOSS_HEALTH)
        for eb in self.enemy_bullets:
            eb.draw(surf)
        self.player.draw(surf, mouse_pos)

        if self.game_over:
            self._draw_game_over(surf)
        elif self.level_complete:
            self._draw_level_complete(surf)

    def _draw_boss_ui(self, surf, hp, max_hp):
        bar_w = 300
        bar_h = 14
        x = WIDTH // 2 - bar_w // 2
        y = 50
        pygame.draw.rect(surf, (60, 60, 60), (x, y, bar_w, bar_h))
        pct = max(0, hp) / max_hp
        pygame.draw.rect(surf, (220, 60, 60), (x + 2, y + 2, int((bar_w - 4) * pct), bar_h - 4))
        label = font.render("Boss HP", True, (255, 255, 255))
        surf.blit(label, (WIDTH // 2 - label.get_width() // 2, y - 22))

    def _draw_game_over(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))
        text = big_font.render("GAME OVER", True, (255, 50, 50))
        text2 = font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        text3 = font.render("Press R to restart", True, (200, 200, 200))
        surf.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 80))
        surf.blit(text2, (WIDTH // 2 - text2.get_width() // 2, HEIGHT // 2 - 20))
        surf.blit(text3, (WIDTH // 2 - text3.get_width() // 2, HEIGHT // 2 + 24))

    def _draw_level_complete(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))
        
        if self.level == LEVEL_COUNT:
             text = big_font.render("YOU WIN!", True, (50, 255, 50))
             text2 = font.render("Press N to quit", True, (255, 255, 255))
        else:
            text = big_font.render(f"Level {self.level} Complete!", True, (255, 255, 0))
            text2 = font.render("Press Y to continue or N to quit", True, (255, 255, 255))

        surf.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40))
        surf.blit(text2, (WIDTH // 2 - text2.get_width() // 2, HEIGHT // 2 + 20))

    def handle_shoot(self, mouse_pos):
        if self.player.can_shoot() and not self.game_over and not self.level_complete:
            b = self.player.shoot(mouse_pos)
            self.bullets.add(b)

    def restart(self):
        self.__init__(1)

def show_menu():
    selecting = True
    while selecting:
        screen.fill((30, 30, 30))
        title = big_font.render("Zombie Shooter", True, (255, 255, 255))
        prompt = font.render("Press 1 to start Level 1", True, (200, 200, 200))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 60))
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 1

        clock.tick(30)

def main():
    level = show_menu()
    game = Game(level)
    running = True

    while running:
        dt = clock.tick(FPS) / (1000.0 / 60.0)
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not game.level_complete:
                if event.button == 1:
                    game.handle_shoot(mouse_pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game.restart()
                if game.level_complete:
                    if event.key == pygame.K_y:
                        if game.level < LEVEL_COUNT:
                            game = Game(game.level + 1)
                        else:
                            running = False 
                    elif event.key == pygame.K_n:
                        running = False

        if pygame.mouse.get_pressed()[0] and not game.level_complete:
            game.handle_shoot(mouse_pos)

        game.update(dt, keys, mouse_pos)
        game.draw(screen, mouse_pos)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()