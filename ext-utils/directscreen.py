import serial

WHITE = 1
BLACK = 0

def bit(n):
    return 1 << n

def rbit(n):
    return 0xff ^ (1 << n)

def sendc_retry(_serial: serial.Serial, char: bytes, max_retries=5):
    _serial.write(b'S')
    resp = _serial.read()
    tries = 0
    while resp == b"":
        _serial.write(b'p')
        tries += 1
        if tries == max_retries:
            return 0
        resp = _serial.read()
    
    return resp

def send(_serial: serial.Serial, _data: bytearray):
    _serial.timeout = 0.1
    if not sendc_retry(_serial, b"S"): raise TimeoutError("Timed out after maximum attempts have been reached.")
    _serial.write(b'd')
    _serial.flush()
    _serial.reset_input_buffer()
    
    i = 0

    while True:
        byte = _data[i]
        _serial.write(bytearray([byte]))
        r = _serial.read(1)
        if r == b"":
            continue
        i += 1
        if i == len(_data):
            break
    

class ESPRuler:
    def __init__(self, s: serial.Serial):
        self.serial = s
        self.width = 128
        self.height = 32

        self.__buf = bytearray((128*32)//8)  # 1 row = 16 bytes, 32 rows

        # self.serial.write(b'S')
        # self.serial.flush()

    
    def update(self):
        # for i in range(0, len(self.__buf), 16):
        #     l = int().from_bytes(self.__buf[i:i+16], "big")
        #     print(f"{l:0128b}")
        send(self.serial, self.__buf)
        
    def set(self, x, y, color):
        byte_pos = y*16 + x//8
        bit_pos = 7 - (x % 8)
        
        # Clear bit
        self.__buf[byte_pos] &= rbit(bit_pos)

        if color:
            self.__buf[byte_pos] |= bit(bit_pos)

    def clear(self): 
        self.__buf = bytearray((128*32)//8)
    
    def poll_buttons(self, max_tries=5) -> int:
        self.serial.timeout = 0.1
        if not sendc_retry(self.serial, b"S", max_retries=max_tries): raise TimeoutError("Timed out after maximum attempts have been reached.")
        self.serial.write(b'p')
        resp = self.serial.read()
        tries = 0
        while resp == b"":
            self.serial.write(b'p')
            tries += 1
            if tries == max_tries:
                raise TimeoutError("Poll timed out after maximum attempts have been reached.")
            resp = self.serial.read()
        
        return int(resp[0])
        

    def poll_buttons_tuple(self) -> tuple:
        buttons = self.poll_buttons()
        return bool(buttons & 1), bool(buttons & 2), bool(buttons & 4), bool(buttons & 8)


class ObjectRenderer:
    def __init__(self, window: ESPRuler):
        self.window: ESPRuler = window

    def __clip_window_bounds(self, x, y):
        return max(min(x, self.window.width - 1), 0), max(min(y, self.window.height - 1), 0)

    def dot(self, x, y, color):
        self.window.set(x, y, color)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: int, fill=False):
        x0, y0 = self.__clip_window_bounds(x0, y0)
        x1, y1 = self.__clip_window_bounds(x1, y1)
        """Draw a rectangle on the screen."""
        if fill:
            """Draw a filled rectangle on the screen."""
            for y in range(y0, y1+1):
                for x in range(x0, x1+1):
                    self.window.set(x, y, color)
        else:
            """Draw a rectangle on the screen."""
            for x in range(x0, x1 + 1):
                self.window.set(x, y0, color)
                self.window.set(x, y1, color)
            for y in range(y0, y1 + 1):
                self.window.set(x0, y, color)
                self.window.set(x1, y, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        """Draw a line on the screen."""
        x0, y0 = self.__clip_window_bounds(x0, y0)
        x1, y1 = self.__clip_window_bounds(x1, y1)

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            if width > 1:
                self.circle(x0, y0, width-1, color, True)
            else:
                self.window.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def __line_points(self, x0, y0, x1, y1):
        out = []
        x0, y0 = self.__clip_window_bounds(x0, y0)
        x1, y1 = self.__clip_window_bounds(x1, y1)

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            out.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

        return out

    def __straight_x(self, x0, x1, y, color):
        back = x0 > x1
        n = -1 if back else 1
        for x in range(x0, x1+n, n):
            if x in range(0, self.window.width) and y in range(0, self.window.height):
                self.window.set(x, y, color)

    def __straight_y(self, y0, y1, x, color):
        back = y0 > y1
        n = -1 if back else 1
        for y in range(y0, y1+n, n):
            if x in range(0, self.window.width) and y in range(0, self.window.height):
                self.window.set(x, y, color)

    def __circle_outline_pixels(self, x0: int, y0: int, r: int):
        pixels = []

        t1 = r / 16
        x = r
        y = 0
        while not x < y:
            points = [
                (x0 + x, y0 + y),
                (x0 + x, y0 - y),
                (x0 - x, y0 + y),
                (x0 - x, y0 - y),

                (x0 + y, y0 + x),
                (x0 + y, y0 - x),
                (x0 - y, y0 + x),
                (x0 - y, y0 - x),
            ]
            pixels += points
            y = y + 1
            t1 = t1 + y
            t2 = t1 - x
            if t2 >= 0:
                t1 = t2
                x = x - 1

        return pixels

    def circle(self, x0: int, y0: int, r: int, color: int, fill=False, outline_width: int = 1):
        outline = self.__circle_outline_pixels(x0, y0, r)

        if fill:
            y_groups = {}
            for pixel in outline:
                x, y = pixel
                if y not in y_groups:
                    y_groups[y] = [x]
                else:
                    y_groups[y].append(x)
            for group in y_groups:
                if len(y_groups[group]) == 1:
                    continue
                self.__straight_x(min(y_groups[group]), max(y_groups[group]), group, color)
        else:
            for _x, _y in outline:
                if _x in range(0, self.window.width) and _y in range(0, self.window.height):
                    if outline_width <= 1:
                        self.window.set(_x, _y, color)
                    else:
                        self.circle(_x, _y, outline_width-1, color, fill=True)

    def polygon_cve(self, points, color):
        for i in range(len(points)):
            a = points[i]
            if i+1 == len(points):
                b = points[0]
            else:
                b = points[i+1]
            self.line(*a, *b, color)

    def polygon_cvx(self, points, color, fill=False):
        """Draw a convex polygon. DO NOT USE WITH CONCAVE POLYGONS AS THE FILL WILL BREAK!"""
        if fill:
            outline = []
            for i in range(len(points)):
                a = points[i]
                if i+1 == len(points):
                    b = points[0]
                else:
                    b = points[i+1]
                outline += self.__line_points(*a, *b)


            y_groups = {}
            for pixel in outline:
                x, y = pixel
                if y not in y_groups:
                    y_groups[y] = [x]
                else:
                    y_groups[y].append(x)
            for group in y_groups:
                if len(y_groups[group]) == 1:
                    continue
                self.__straight_x(min(y_groups[group]), max(y_groups[group]), group, color)
        else:
            for i in range(len(points)):
                a = points[i]
                if i+1 == len(points):
                    b = points[0]
                else:
                    b = points[i+1]
                self.line(*a, *b, color)

    # def text(self, x0: int, y0: int, s: str, color: int | str, _font: Font = None):
    #     """Simple function to render text from a bitmap font (Font())"""
    #     if not _font:
    #         _font = Font(font_builtin)
    #     s = str(s)
    #     chars = _font.charmap
    #     font_height = _font.height
    #     screen_pixels: list[list[bool]] = [[False] for _ in range(font_height)]
    #     x = 0
    #     line = 0
    #     for char in s:
    #         if char == "\n":
    #             line += 1
    #             x = 0
    #             continue
    #         if char not in chars:
    #             char = "\x00"
    #         bitmap, width = _font.bitmap(char)
    #         if width == 0:
    #             continue
    #         for y in range(font_height):
    #             for char_x in range(width):
    #                 bit = bitmap[y] << char_x & 2 ** (width - 1)
    #                 if bit:
    #                     # screen_pixels[y].append(True)
    #                     if x + char_x + x0 in range(0, self.window.width) and y + y0 + (line*(font_height+1)) in range(0, self.window.height):
    #                         self.window.set(x + char_x + x0, y + y0 + (line*(font_height+1)), color)
    #                 # else:
    #                     # screen_pixels[y].append(False)
    #         x += width + 1


    def update_screen(self):
        self.window.update()

    def clear_screen(self):
        self.window.clear()

if __name__ == "__main__":
    import time, random
    ruler = ESPRuler(serial.Serial("COM18"))
    renderer = ObjectRenderer(ruler)
    renderer.rect(0, 0, 127 ,31, 1)
    next_screen_update = 0
    x, y, r = random.randint(5, 122), random.randint(5, 26), random.randint(2, 5)
    last_buttons = 0
    while True:
        now = time.time()
        if now > next_screen_update:
            renderer.clear_screen()
            renderer.circle(x, y, r, WHITE, fill=True)
            renderer.update_screen()

            next_screen_update = now + 0.5

        buttons = ruler.poll_buttons()
        if buttons != last_buttons:
            
            if buttons & 1 and not last_buttons:
                x, y, r = random.randint(5, 122), random.randint(5, 26), random.randint(2, 5)
                next_screen_update = 0
            
            last_buttons = buttons