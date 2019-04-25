import time
import curses
import asyncio
import random
import sys
import os
from physics import update_speed
from curses_tools import read_controls, draw_frame, get_frame_size
from obstacles import Obstacle, show_obstacles, has_collision
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics



coroutines = []
obstacles = []
obstacles_in_last_collision = []
spaceship_frame = ''
year = 1957


def get_frame(file_path):
    with open(file_path, 'r') as file:
        return file.read()


async def show_gameover(canvas):
    rows_number, columns_number = canvas.getmaxyx()
    size = 'large'
    large_screen_size = 75
    medium_screen_size = 45
    if medium_screen_size < columns_number < large_screen_size:
        size = 'small'
    elif columns_number < medium_screen_size:
        size = 'mini'
    go_frame = get_frame(f'./animations/gameover/gameover_{size}.txt')
    frame_width, frame_height = get_frame_size(go_frame)
    time.sleep(5)
    loop = 0
    loops = 20
    while loop < loops:
        loop += 1
        draw_frame(canvas, rows_number//2 - frame_width//2, columns_number//2 - frame_height//2, go_frame)
        await sleep(1)
    sys.exit('Game over')


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
    global year
    spaceship_collision = False
    while not spaceship_collision:
        maxx, maxy = canvas.getmaxyx()
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        frame_rows, frame_columns = get_frame_size(spaceship_frame)
        if is_crossing_border(row, row_speed, frame_rows, maxx):
            row += row_speed
        if is_crossing_border(column, column_speed, frame_columns, maxy):
            column += column_speed

        draw_frame(canvas, row, column, spaceship_frame)
        last_frame = spaceship_frame

        frame_rows, frame_columns = get_frame_size(spaceship_frame)
        await sleep(1)
        if space_pressed and (year >= 2020):
            coroutines.append(fire(canvas, row, column+2))

        draw_frame(canvas, row, column, last_frame, negative=True)

        if is_collision(row, column, frame_rows, frame_columns):
            spaceship_collision = True
    coroutines.append(explode(canvas, row+frame_rows//2, column+frame_columns//2))
    coroutines.append(show_gameover(canvas))




async def animate_spaceship(frame_1, frame_2):
    """Renew spaceship frame but doesnt touch canvas and draw_frame"""
    frames = [frame_1, frame_2]
    global spaceship_frame
    while True:
        for frame in frames:
            spaceship_frame = frame
            await sleep(1)


def is_collision(row, column, size_rows=1, size_columns=1):
    global obstacles
    global obstacles_in_last_collision
    for obstacle in obstacles:
        if obstacle.has_collision(
            row,
            column,
            size_rows,
            size_columns
        ):
            obstacles_in_last_collision.append(obstacle)
            obstacles.remove(obstacle)
            obstacle.uid = True
            return True


async def fire(canvas, start_row, start_column, rows_speed=-0.7, columns_speed=0):
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



async def fly_garbage(canvas, column, garbage_frame, obstacle, speed=0.5):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""
    global obstacles

    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    while row < rows_number:
        if not obstacle.uid:
            draw_frame(canvas, row, column, garbage_frame)
            obstacle.row = row
            obstacle.column = column
            await asyncio.sleep(0)
            draw_frame(canvas, row, column, garbage_frame, negative=True)
            row += speed
        else:
            width, height = get_frame_size(garbage_frame)
            coroutines.append(explode(canvas, row + width//2, column + height//2))
            return
    obstacles.remove(obstacle)


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
    global year
    global obstacles
    while True:
        tics_until_spawn = get_garbage_delay_tics(year)
        if tics_until_spawn:
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
            await sleep(tics_until_spawn - 1)
        await sleep(1)


async def count_years():
    global year
    while True:
        year += 1
        await sleep(15)


def get_label_center_coords(max_width, str_len):
    return max_width//2 - str_len//2


async def year_label(sub_canvas):
    global year
    event = 0
    max_row, max_column = sub_canvas.getmaxyx()
    while True:
        year_label = f'Year: {year}'
        sub_canvas.addstr(1,
                          get_label_center_coords(max_column, len(year_label)),
                          year_label)
        if year in PHRASES.keys():
            event = year
            phrase = PHRASES[year]
            sub_canvas.addstr(2,
                              get_label_center_coords(max_column, len(phrase)),
                              phrase)
        if event == year-3:
            sub_canvas.addstr(2,
                              get_label_center_coords(max_column, len(phrase)),
                              ' '*len(phrase))
        await sleep(1)


def main(canvas, obstacles_visible=False):
    canvas.nodelay(True)
    curses.curs_set(False)
    stars_count = 200
    global year
    global coroutines
    global obstacles
    space_near_border = 2
    max_row, max_column = canvas.getmaxyx()
    sub_canvas_columns = max_column - space_near_border*2
    sub_canvas_rows = 3
    sub_canvas_start_row = max_row - 5
    sub_canvas_start_column = space_near_border + 1
    sub_canvas = canvas.derwin(sub_canvas_rows,
                               sub_canvas_columns,
                               sub_canvas_start_row,
                               sub_canvas_start_column)
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
    year_counter = count_years()
    coroutines.append(year_counter)
    year_lab = year_label(sub_canvas)
    coroutines.append(year_lab)
    if obstacles_visible:
        run_obstacles = show_obstacles(canvas, obstacles)
        coroutines.append(run_obstacles)
    coroutines.append(spaceship_animation)
    coroutines.append(spaceship)
    loop = 0
    loops_count = 500
    while loop < loops_count:
        loop += 1
        for coroutine in coroutines:
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.border()
        sub_canvas.refresh()
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
