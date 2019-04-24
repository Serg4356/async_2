from curses_tools import draw_frame
import asyncio

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
            return
    obstacles.remove(obstacle)
