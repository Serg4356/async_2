import time
import curses
import asyncio
import random
import sys
import os
import traceback
from space_garbage import fly_garbage
from physics import update_speed
from curses_tools import read_controls, draw_frame, get_frame_size
from obstacles import Obstacle, show_obstacles, has_collision



coroutines = []
obstacles = []
spaceship_frame = ''


def get_frame(file_path):
    with open(file_path, 'r') as file:
        return file.read()


def is_crossing_border(current_position ,shift_direction,
                       frame_length, canvas_size):
    space_near_border = 1
    critical_position = canvas_size - frame_length - space_near_border
    return ((current_position < critical_position) and (shift_direction > 0))\
           or ((current_position > space_near_border) and (shift_direction < 0))


async def run_spaceship(canvas, row, column):
    """ controls location of spaceship and draws it on the screen"""
    row_speed = column_speed = 0
    global spaceship_frame
    global coroutines
    while True:
        maxx, maxy = canvas.getmaxyx()
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        frame_rows, frame_columns = 6, 6
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)

        if is_crossing_border(row, row_speed, frame_rows, maxx):
            row += row_speed
        if is_crossing_border(column, column_speed, frame_columns, maxy):
            column += column_speed

        draw_frame(canvas, row, column, spaceship_frame)
        last_frame = spaceship_frame

        await sleep(1)
        if space_pressed:
            coroutines.append(fire(canvas, row, column+2))

        draw_frame(canvas, row, column, last_frame, negative=True)


async def animate_spaceship(frame_1, frame_2):
    """Renew spaceship frame but doesnt touch canvas and draw_frame"""
    frames = [frame_1, frame_2]
    global spaceship_frame
    while True:
        for frame in frames:
            spaceship_frame = frame
            await sleep(1)


def is_collision(row, column):
    global obstacles
    for obstacle in obstacles:
        if obstacle.has_collision(
            row,
            column
        ):
            return True


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep(1)

    canvas.addstr(round(row), round(column), 'O')
    await sleep(1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        if is_collision(row, column):
            return
        canvas.addstr(round(row), round(column), symbol)
        await sleep(1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def get_files_list(path):
    files_list = []
    accepted_extensions = ['.txt']
    for file_name in os.listdir(path):
        if os.path.splitext(file_name)[1].lower() in accepted_extensions:
            files_list.append(file_name)
    return files_list


def choose_star():
  stars = ['+', ':', '*', '.']
  return random.choice(stars)


async def sleep(tics=1):
    for tic in range(tics, 0, -1):
        await asyncio.sleep(0)


def choose_garbage_frame():
    garbage = []
    path_to_garbage = './animations/garbage/'
    frames_list = get_files_list(path_to_garbage)
    for frame in frames_list:
        garbage.append(get_frame(os.path.join(path_to_garbage, frame)))
    return random.choice(garbage)


async def fill_orbit_with_garbage(canvas,max_column):
    global coroutines
    global obstacles
    max_probability = 1000
    garbage_probability = 100
    while True:
        if random.randint(0, max_probability) < garbage_probability:
            garbage_frame = choose_garbage_frame()
            row, column = 1, random.randint(1, max_column)
            row_size, column_size = get_frame_size(garbage_frame)
            obstacle = Obstacle(row, column, row_size, column_size)
            obstacles.append(obstacle)
            coroutines.append(fly_garbage(
                canvas,
                column,
                garbage_frame,
                obstacle))
        await sleep(1)


def main(canvas):
    canvas.nodelay(True)
    curses.curs_set(False)
    stars_count = 200
    global coroutines
    global obstacles
    max_row, max_column = canvas.getmaxyx()
    space_near_border = 2
    for _ in range(stars_count):
        coroutines.append(blink(
            canvas,
            random.randint(space_near_border, max_row-space_near_border),
            random.randint(space_near_border, max_column - space_near_border),
            symbol=choose_star()
        ))
    frame_1 = get_frame('./animations/rocket/rocket_frame_1.txt')
    frame_2 = get_frame('./animations/rocket/rocket_frame_2.txt')
    spaceship_width, spaceship_height = get_frame_size(frame_1)
    rows_center = max_row//2-spaceship_width//2
    columns_center = max_column//2 - spaceship_height//2
    coroutines.append(fill_orbit_with_garbage(canvas, max_column))
    spaceship = run_spaceship(canvas, rows_center, columns_center)
    spaceship_animation = animate_spaceship(frame_1, frame_2)
    run_obstacles = show_obstacles(canvas, obstacles)
    coroutines.append(run_obstacles)
    coroutines.append(spaceship)
    coroutines.append(spaceship_animation)
    loop = 0
    loops_count = 100
    while loop < loops_count:
        loop += 1
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.border()
        canvas.refresh()
        time.sleep(0.1)


async def blink(canvas, row, column, symbol='*'):
    while True:
        await sleep(random.randint(1,20))

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(main)
    print(sys.last_traceback)
