import serial
import pygame
import numpy as np
from time import sleep

RUN = True
FAIL_COLOR = '\033[91m'
PORT = input('Serial connection port: ')

try:
    ARDUINO_PORT = serial.Serial(PORT, 9600)
except serial.serialutil.SerialException:
    print(f'{FAIL_COLOR}COM connection error...\n'
          f'Try again after serial port connected or rename the connection port.\n'
          f'App is closing now...')
    sleep(5)
    RUN = False

WIDTH, HEIGHT = 1200, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
FPS = 60
BLOCKSIZE = 40
Z = 0.5 * HEIGHT
CIRCLE_CENTER = (0.5 * (WIDTH - 2 * BLOCKSIZE) + 1.5 * BLOCKSIZE, HEIGHT - BLOCKSIZE)
SMALL_RADIUS = (0.5 * (WIDTH - 2 * BLOCKSIZE)) * 0.2
LARGE_RADIUS = 0.5 * (WIDTH - 2 * BLOCKSIZE)
INV_Y_CC = HEIGHT - CIRCLE_CENTER[1]

SCALE_CONST_Z = 100 / (HEIGHT - int(1.5 * BLOCKSIZE))

H = 30  # [cm]
ARM_LENGTH = 2 * H

COLORS = {
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'green': (0, 255, 0),
    'red': (255, 0, 0),
    'purple': (255, 0, 255),
    'grey': (200, 200, 200),
    'blue': (0, 0, 255)
}


def get_y_on_arc(mid: tuple, x, radius):
    y = np.sqrt(radius ** 2 - (x - mid[0]) ** 2) + mid[1]
    return y


def transfer_data(port: serial.serialwin32.Serial, data: bytes):
    port.write(data)


def draw_circle(position: tuple, radius_factor=1.0, fill=False, color='black', clickable=False, draw_top_right=False, draw_top_left=False):
    pygame.draw.circle(WIN,
                       COLORS['red'] if pygame.mouse.get_pressed()[0] and clickable is True else COLORS[color],
                       position, radius_factor * (0.5 * (WIDTH - 2 * BLOCKSIZE)),
                       2 if fill is False else 0,
                       draw_top_right=draw_top_right, draw_top_left=draw_top_left)


def draw_sideGrid(color: str, fill=False):
    bs = int(0.5 * BLOCKSIZE)
    rect = pygame.Rect(bs, bs,
                       bs, HEIGHT - 2 * bs)
    pygame.draw.rect(WIN, COLORS[color], rect,
                     1 if fill is False else 0)


def draw_line(start_pos: tuple, end_pos: tuple):
    pygame.draw.line(WIN, COLORS['black'], start_pos=start_pos, end_pos=end_pos, width=2)


def display_text(text: str, font: pygame.font.Font, color, position: tuple):
    scoretext = font.render(text, True, COLORS[color])
    WIN.blit(scoretext, position)


def draw_arc(angle: float, radius):
    rect = pygame.Rect(CIRCLE_CENTER[0] - radius, CIRCLE_CENTER[1] - radius, 2 * radius, 2 * radius)
    pygame.draw.arc(WIN, COLORS['black'], rect, np.pi - angle, -np.pi)


def cursor(x_coordinate, y_coordiante, color: str, clickable=False, size_factor=1.0):
    head_rect = pygame.Rect(x_coordinate, y_coordiante, int(BLOCKSIZE * size_factor), int(BLOCKSIZE * size_factor))
    pygame.draw.rect(WIN,
                     COLORS['red'] if pygame.mouse.get_pressed()[0] and clickable is True else COLORS[color],
                     head_rect)


def running():
    global Z
    global RUN

    new_x = pygame.mouse.get_pos()[0]
    new_y = pygame.mouse.get_pos()[1]

    inverted_y = HEIGHT - new_y

    if new_x > WIDTH - int(0.5 * BLOCKSIZE):
        x = WIDTH - int(0.5 * BLOCKSIZE)
    elif new_x < 1.5 * BLOCKSIZE:
        x = 1.5 * BLOCKSIZE
    else:
        x = new_x

    if inverted_y < get_y_on_arc((CIRCLE_CENTER[0], INV_Y_CC), x, SMALL_RADIUS):
        y = (get_y_on_arc((CIRCLE_CENTER[0], INV_Y_CC), x, SMALL_RADIUS) - HEIGHT) * -1

    elif inverted_y > get_y_on_arc((CIRCLE_CENTER[0], INV_Y_CC), x, LARGE_RADIUS):
        y = (get_y_on_arc((CIRCLE_CENTER[0], INV_Y_CC), x, LARGE_RADIUS) - HEIGHT) * -1

    elif new_y > HEIGHT - BLOCKSIZE:
        y = HEIGHT - BLOCKSIZE

    else:
        y = new_y

    keys = pygame.key.get_pressed()
    mouse_status = pygame.mouse.get_pressed()[0]

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            RUN = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                RUN = False

    if keys[pygame.K_UP] and Z > int(0.5 * BLOCKSIZE):
        Z -= int(BLOCKSIZE * 0.1)
    elif keys[pygame.K_DOWN] and Z < HEIGHT - 2 * int(BLOCKSIZE * 0.5):
        Z += int(BLOCKSIZE * 0.1)

    diff = CIRCLE_CENTER[0] - x

    try:
        quotient = (HEIGHT - y - BLOCKSIZE) / abs(diff)
    except ZeroDivisionError:
        quotient = np.tan(np.pi / 2)

    alpha = np.arctan(quotient) if diff > 0 else np.pi - np.arctan(quotient)

    draw_circle(position=(x, y), color='green', fill=True, radius_factor=0.02, clickable=True)
    cursor(int(BLOCKSIZE * 0.5), Z, color='purple', clickable=False, size_factor=0.5)
    draw_line(start_pos=CIRCLE_CENTER, end_pos=(x, y))

    distance = np.sqrt((CIRCLE_CENTER[0] - x) ** 2 + (CIRCLE_CENTER[1] - y) ** 2)

    draw_arc(angle=alpha, radius=2 * BLOCKSIZE)

    return round(np.rad2deg(alpha), 1), Z, distance, mouse_status


def compute_servo_data(height, angle, dist, pressed=False):
    inp1 = round(angle)

    z = height / 100
    x = round(ARM_LENGTH * dist / LARGE_RADIUS, 1)
    y = round(ARM_LENGTH * z, 1)
    g = round(np.sqrt(x ** 2 + y ** 2), 1)

    if g > ARM_LENGTH:
        g = float(ARM_LENGTH)

    try:
        delta = np.arctan(y / x)
    except ZeroDivisionError:
        delta = 90

    epsilon = np.arccos(0.5 * g / H)
    alpha = delta + epsilon
    beta = 2 * np.arcsin(0.5 * g / H)
    inp2 = round(np.rad2deg(alpha))
    inp3 = round(np.rad2deg(beta))
    inp4 = 180 if pressed is True else 0

    return inp1, inp2, inp3, inp4


def main():
    global Z

    pygame.init()
    default_font = pygame.font.Font(None, 30)
    clock = pygame.time.Clock()
    pygame.display.set_caption('Trackpad')
    icon = pygame.image.load('icon.ico')
    pygame.display.set_icon(icon)

    while RUN:
        clock.tick(FPS)
        WIN.fill(COLORS['grey'])
        draw_circle(position=CIRCLE_CENTER, radius_factor=1.0, draw_top_right=True, draw_top_left=True, color='white', fill=True)
        draw_circle(position=CIRCLE_CENTER, radius_factor=0.2, draw_top_right=True, draw_top_left=True, color='grey', fill=True)
        draw_circle(position=CIRCLE_CENTER, radius_factor=1.0, draw_top_right=True, draw_top_left=True)
        draw_circle(position=CIRCLE_CENTER, radius_factor=0.2, draw_top_right=True, draw_top_left=True)
        draw_sideGrid(color='white', fill=True)
        draw_sideGrid(color='black', fill=False)
        draw_line(start_pos=(1.5 * BLOCKSIZE, CIRCLE_CENTER[1]),
                  end_pos=(WIDTH - 0.5 * BLOCKSIZE, CIRCLE_CENTER[1]))
        inp_alpha, z, inp_l, mouse_status = running()
        inp_z = 100 - round((z - int(0.5 * BLOCKSIZE)) * SCALE_CONST_Z)
        draw_line(start_pos=CIRCLE_CENTER, end_pos=(CIRCLE_CENTER[0], CIRCLE_CENTER[1] - 0.5 * (WIDTH - 2 * BLOCKSIZE)))
        display_text(f'Winkel: {inp_alpha}°', default_font, 'blue', (CIRCLE_CENTER[0] - 1.5 * BLOCKSIZE, 2 * BLOCKSIZE))
        display_text(f'{inp_z}%', default_font, 'purple', (50, Z))

        inp1, inp2, inp3, inp4 = compute_servo_data(height=inp_z, angle=inp_alpha, dist=inp_l, pressed=mouse_status)

        pygame.display.update()

        print(f'{inp1}|{inp2}|{inp3}|{inp4}')

        trans_str = f'a{inp1}b{inp2}c{inp3}d{inp4}'.encode()
        transfer_data(ARDUINO_PORT, trans_str)

    pygame.quit()


if __name__ == '__main__':
    main()
