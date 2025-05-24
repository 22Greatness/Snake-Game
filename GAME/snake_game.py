import pygame
import sys
import random
import time
import json
import os

# ---- CONFIG ----
CELL_SIZE       = 20
GRID_WIDTH      = 30
GRID_HEIGHT     = 20
SIDEBAR_WIDTH   = 200
WINDOW_WIDTH    = CELL_SIZE * GRID_WIDTH + SIDEBAR_WIDTH
WINDOW_HEIGHT   = CELL_SIZE * GRID_HEIGHT
BASE_FPS        = 10

SMALL_APPLE_CHANCE = 0.8
NUM_OBSTACLES      = 30
POWERUP_CHANCE     = 0.005  # chance per frame
POWERUP_TYPES      = ['speed', 'slow', 'shield', 'bonus']
POWERUP_DURATION   = 5     # seconds

# colors
WHITE       = (255,255,255)
BLACK       = (0,0,0)
RED         = (200,0,0)
GREEN       = (0,200,0)
GRAY        = (40,40,40)
DARK_GRAY   = (50,50,50)
SNAKE_BODY  = (0,100,0)
SNAKE_HEAD  = (0,150,0)
CYAN        = (0,200,200)
YELLOW      = (200,200,0)
BLUE        = (0,0,200)
GOLD        = (200,200,100)

# file paths
DATA_DIR       = os.path.dirname(__file__)
HIGHSCORE_FILE = os.path.join(DATA_DIR, 'highscores.json')
ACHIEVE_FILE   = os.path.join(DATA_DIR, 'achievements.json')

# ensure files exist
if not os.path.exists(HIGHSCORE_FILE):
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump([], f)
if not os.path.exists(ACHIEVE_FILE):
    with open(ACHIEVE_FILE, 'w') as f:
        json.dump({}, f)

# persistence
def load_highscores():
    with open(HIGHSCORE_FILE) as f:
        return json.load(f)

def save_highscores(scores):
    scores = sorted(scores, reverse=True)[:5]
    with open(HIGHSCORE_FILE, 'w') as f:
        json.dump(scores, f)

def load_achievements():
    with open(ACHIEVE_FILE) as f:
        return json.load(f)

def save_achievements(ach):
    with open(ACHIEVE_FILE, 'w') as f:
        json.dump(ach, f)

# spawn utilities
def get_random_cell(exclude):
    while True:
        pos = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
        if pos not in exclude:
            return pos

obstacles = []
def init_obstacles():
    global obstacles
    obstacles = []
    used = []
    for _ in range(NUM_OBSTACLES):
        p = get_random_cell(used)
        obstacles.append(p)
        used.append(p)

def spawn_apple(exclude):
    pos = get_random_cell(exclude)
    growth = 1 if random.random() < SMALL_APPLE_CHANCE else 2
    return pos, growth

def spawn_powerup(exclude):
    pos = get_random_cell(exclude)
    ptype = random.choice(POWERUP_TYPES)
    return pos, ptype

# drawing
def draw_cell(surface, pos, color, size_ratio=1.0):
    x,y = pos
    size = int(CELL_SIZE * size_ratio)
    offset = (CELL_SIZE - size) // 2
    rect = pygame.Rect(x*CELL_SIZE + offset, y*CELL_SIZE + offset, size, size)
    pygame.draw.rect(surface, color, rect)

def draw_circle_cell(surface, pos, color):
    draw_cell(surface, pos, color, size_ratio=0.8)

# reset game state
def reset_game():
    init_obstacles()
    mid_x = GRID_WIDTH // 2
    mid_y = GRID_HEIGHT // 2
    snake = [(mid_x - i, mid_y) for i in range(3)]
    length = 3
    dx, dy = 1, 0
    score = 0
    apple_pos, apple_growth = spawn_apple(snake + obstacles)
    powerups = {}
    shield_active = False
    shield_end = 0
    speed_mult = 1.0
    speed_end = 0
    start_time = time.time()
    game_over = False
    paused = False
    return (snake, length, dx, dy, apple_pos, apple_growth,
            score, powerups, shield_active, shield_end,
            speed_mult, speed_end, start_time, game_over, paused)

# main loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()
    font_big   = pygame.font.SysFont(None, 48)
    font_small = pygame.font.SysFont(None, 24)

    # UI elements
    sidebar_x   = GRID_WIDTH * CELL_SIZE
    pause_btn   = pygame.Rect(sidebar_x+10, 10, 80, 30)
    restart_btn = pygame.Rect(sidebar_x+100,10, 80, 30)

    highscores   = load_highscores()
    achievements = load_achievements()
    # initial state
    (snake, length, dx, dy, apple_pos, apple_growth,
     score, powerups, shield, shield_end,
     speed_mult, speed_end, start_time, game_over, paused) = reset_game()
    saved_score = False

    while True:
        now     = time.time()
        elapsed = now - start_time

        # events
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if evt.type == pygame.KEYDOWN and not game_over:
                if evt.key == pygame.K_UP    and dy == 0: dx,dy = 0,-1
                elif evt.key == pygame.K_DOWN  and dy == 0: dx,dy = 0, 1
                elif evt.key == pygame.K_LEFT  and dx == 0: dx,dy = -1,0
                elif evt.key == pygame.K_RIGHT and dx == 0: dx,dy =  1,0
            if evt.type == pygame.MOUSEBUTTONDOWN:
                mx,my = evt.pos
                if pause_btn.collidepoint(mx,my) and not game_over:
                    paused = not paused
                if restart_btn.collidepoint(mx,my):
                    (snake, length, dx, dy, apple_pos, apple_growth,
                     score, powerups, shield, shield_end,
                     speed_mult, speed_end, start_time, game_over, paused) = reset_game()
                    saved_score = False

        # update
        if not paused and not game_over:
            # dynamic difficulty
            fps_val = int(BASE_FPS + score // 10)
            # powerup expiration
            if speed_mult != 1.0 and now > speed_end:
                speed_mult = 1.0
            if shield and now > shield_end:
                shield = False
            # spawn new powerup
            if random.random() < POWERUP_CHANCE:
                ppos, ptype = spawn_powerup(snake + obstacles + list(powerups.keys()) + [apple_pos])
                powerups[ppos] = [ptype, now]
            # move snake
            nx = (snake[0][0] + dx) % GRID_WIDTH
            ny = (snake[0][1] + dy) % GRID_HEIGHT
            head = (nx, ny)
            collided = head in snake or head in obstacles
            if collided:
                if shield:
                    shield = False
                else:
                    game_over = True
            else:
                snake.insert(0, head)
                # apple
                if head == apple_pos:
                    length += apple_growth
                    score  += apple_growth
                    apple_pos, apple_growth = spawn_apple(snake + obstacles)
                    # achievement: eat 10 apples
                    if score >= 10 and not achievements.get('eat_10'):
                        achievements['eat_10'] = True
                        save_achievements(achievements)
                # powerup
                if head in powerups:
                    ptype, ts = powerups.pop(head)
                    if ptype == 'speed':
                        speed_mult = 2.0
                        speed_end = now + POWERUP_DURATION
                    elif ptype == 'slow':
                        speed_mult = 0.5
                        speed_end = now + POWERUP_DURATION
                    elif ptype == 'shield':
                        shield = True
                        shield_end = now + POWERUP_DURATION
                    elif ptype == 'bonus':
                        length += 3
                        score  += 3
                # trim tail
                while len(snake) > length:
                    snake.pop()
            # save score on first game over frame
            if game_over and not saved_score:
                highscores.append(score)
                save_highscores(highscores)
                saved_score = True

        # draw
        screen.fill(BLACK)
        # grid lines
        for x in range(GRID_WIDTH+1):
            pygame.draw.line(screen, GRAY, (x*CELL_SIZE,0), (x*CELL_SIZE,WINDOW_HEIGHT))
        for y in range(GRID_HEIGHT+1):
            pygame.draw.line(screen, GRAY, (0,y*CELL_SIZE), (GRID_WIDTH*CELL_SIZE,y*CELL_SIZE))
        # obstacles
        for obs in obstacles:
            draw_cell(screen, obs, DARK_GRAY)
        # apple
        draw_circle_cell(screen, apple_pos, RED)
        # powerups
        for ppos,(ptype,ts) in powerups.items():
            col = CYAN if ptype=='speed' else YELLOW if ptype=='slow' else BLUE if ptype=='shield' else GOLD
            draw_circle_cell(screen, ppos, col)
        # snake
        for idx,seg in enumerate(snake):
            if idx == 0:
                draw_circle_cell(screen, seg, SNAKE_HEAD)
                # eyes
                cx = seg[0]*CELL_SIZE + CELL_SIZE//2
                cy = seg[1]*CELL_SIZE + CELL_SIZE//2
                eye_r = 3
                off   = CELL_SIZE//4
                ex1 = cx + dx*off - dy*off//2
                ey1 = cy + dy*off + dx*off//2
                ex2 = cx + dx*off + dy*off//2
                ey2 = cy + dy*off - dx*off//2
                pygame.draw.circle(screen, WHITE, (int(ex1),int(ey1)), eye_r)
                pygame.draw.circle(screen, WHITE, (int(ex2),int(ey2)), eye_r)
            else:
                draw_circle_cell(screen, seg, SNAKE_BODY)
        # sidebar
        pygame.draw.rect(screen, DARK_GRAY, (GRID_WIDTH*CELL_SIZE, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT))
        # buttons
        pygame.draw.rect(screen, GRAY, pause_btn)
        pygame.draw.rect(screen, GRAY, restart_btn)
        screen.blit(font_small.render('Pause' if not paused else 'Resume', True, WHITE), (sidebar_x+15,15))
        screen.blit(font_small.render('Restart', True, WHITE), (sidebar_x+105,15))
        # stats
        screen.blit(font_small.render(f'Score: {score}', True, WHITE), (sidebar_x+10,60))
        screen.blit(font_small.render(f'Time: {int(elapsed)}s', True, WHITE), (sidebar_x+10,85))
        # high scores
        screen.blit(font_small.render('High Scores:', True, WHITE), (sidebar_x+10,120))
        for i,sc in enumerate(highscores):
            screen.blit(font_small.render(f'{i+1}. {sc}', True, WHITE), (sidebar_x+10,145+20*i))
        # missions
        screen.blit(font_small.render('Missions:', True, WHITE), (sidebar_x+10,270))
        prog  = f'{score}/10'
        mtext = '✓ Eat 10 apples' if achievements.get('eat_10') else f'Eat 10 apples ({prog})'
        screen.blit(font_small.render(mtext, True, WHITE), (sidebar_x+10,295))

        # game over
        if game_over:
            over = font_big.render('Game Over!', True, RED)
            rect = over.get_rect(center=(WINDOW_WIDTH//2 - SIDEBAR_WIDTH//2, WINDOW_HEIGHT//2))
            screen.blit(over, rect)

        pygame.display.flip()
        fps_val = int((BASE_FPS + score//10) * speed_mult)
        clock.tick(fps_val if fps_val>0 else 1)

if __name__ == '__main__':
    main()
