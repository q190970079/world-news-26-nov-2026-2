"""The World Today: 26 November 2026 in one image.

A pure standard-library Python program that draws a newspaper front
page summarising the world news of Thursday 26 November 2026 and
writes it as a deterministic PNG to /output/entry.png (or to the
directory named by MAKEFUN_OUTPUT_DIR when that variable is set).

Stories carried, each reported on 26 November by at least two outlets:
China launches Shenzhou-24, carrying Pakistani pilot Muhammad
Zeeshan Ali, the first foreign astronaut to board the Tiangong space
station; China investigates Shanghai party chief Chen Jining, a
Politburo member, the fourth probed since 2025; leaked Rosstat data
analysed by the BBC, Meduza and Mediazona puts the Russian military
death toll in Ukraine near 500,000, about 700,000 counting the
missing; North Korea expels Swiss envoy Sylvain Astier and closes
its Pyongyang office over sanctions on the Songdowon camp; Colombian
forces storm a Cartagena supermarket after a 17-hour siege and free
all 20 hostages, one captor killed. The ticker adds the
Australia-Solomon Islands security pact, the Bangladesh garment pay
rise, India's Constitution Day, the Mercury mission and the US
tariff plan.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (176, 42, 30)
BLUE = (29, 78, 121)
GREY = (96, 96, 96)
LIGHT = (226, 219, 198)
GREEN = (58, 128, 62)
GOLD = (198, 146, 32)
TEAL = (28, 110, 110)
SKY = (18, 52, 96)
ORANGE = (224, 122, 32)


# A 5x7 bitmap font. Each glyph is seven rows of five bits.
FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17), "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14), "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31), "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15), "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14), "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17), "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17), "N": (17, 17, 25, 21, 19, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14), "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13), "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30), "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14), "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17), "X": (17, 10, 4, 4, 4, 10, 17),
    "Y": (17, 10, 4, 4, 4, 4, 4), "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14), "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31), "3": (14, 17, 1, 6, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2), "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14), "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14), "9": (14, 17, 17, 15, 1, 2, 12),
    ".": (0, 0, 0, 0, 0, 12, 12), ",": (0, 0, 0, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0), '"': (10, 10, 10, 0, 0, 0, 0),
    "-": (0, 0, 0, 31, 0, 0, 0), ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8), "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 2, 4, 0, 4), "/": (1, 1, 2, 4, 8, 16, 16),
    "(": (2, 4, 8, 8, 8, 4, 2), ")": (8, 4, 2, 2, 2, 4, 8),
    "$": (4, 15, 20, 14, 5, 30, 4), "%": (24, 25, 2, 4, 8, 19, 3),
    "+": (0, 4, 4, 31, 4, 4, 0), "&": (12, 18, 20, 8, 21, 18, 13),
    " ": (0, 0, 0, 0, 0, 0, 0),
}


class Canvas:
    """A tiny RGB framebuffer with just enough drawing for a page."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def set(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            off = (y * self.width + x) * 3
            self.pixels[off:off + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, colour)

    def frame(self, x, y, w, h, colour, thick=3):
        self.rect(x, y, w, thick, colour)
        self.rect(x, y + h - thick, w, thick, colour)
        self.rect(x, y, thick, h, colour)
        self.rect(x + w - thick, y, thick, h, colour)

    def line(self, x0, y0, x1, y1, colour, thick=2):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.rect(x - thick // 2, y - thick // 2, thick, thick, colour)

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, colour)

    def text(self, x, y, s, scale, colour):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, colour)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return max(len(s) - 1, 0) * 6 * scale + 5 * scale if s else 0

    def centred(self, y, s, scale, colour):
        x = (self.width - self.text_width(s, scale)) // 2
        self.text(x, y, s, scale, colour)

    def wrapped(self, x, y, s, scale, colour, max_width, leading=None):
        if leading is None:
            leading = 9 * scale
        words = s.split()
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if self.text_width(trial, scale) <= max_width:
                line = trial
            else:
                self.text(x, y, line, scale, colour)
                y += leading
                line = word
        if line:
            self.text(x, y, line, scale, colour)
            y += leading
        return y


def draw_rocket(cv, x, y, w, h):
    """Lead picture: Shenzhou-24 lifting off toward Tiangong."""
    cv.rect(x, y, w, h, SKY)
    for sx, sy in [(x + 40, y + 30), (x + 120, y + 60), (x + 820, y + 40),
                   (x + 900, y + 90), (x + 60, y + 150), (x + 880, y + 170)]:
        cv.disc(sx, sy, 4, PAPER)
    cv.rect(x + 620, y + 36, 260, 26, LIGHT)
    cv.rect(x + 640, y + 62, 40, 14, GREY)
    cv.rect(x + 800, y + 62, 40, 14, GREY)
    cv.rect(x + 580, y + 44, 40, 10, TEAL)
    cv.rect(x + 880, y + 44, 40, 10, TEAL)
    cv.text(x + 620, y + 84, "TIANGONG", 2, PAPER)
    rx = x + 300
    cv.rect(rx, y + 60, 60, 110, PAPER)
    cv.rect(rx + 24, y + 34, 12, 26, RED)
    cv.rect(rx - 18, y + 130, 18, 40, RED)
    cv.rect(rx + 60, y + 130, 18, 40, RED)
    cv.text(rx + 8, y + 90, "24", 3, RED)
    cv.rect(rx + 14, y + 170, 32, 26, ORANGE)
    cv.rect(rx + 22, y + 170, 16, 26, GOLD)
    cv.disc(rx - 10, y + 192, 10, LIGHT)
    cv.disc(rx + 70, y + 192, 10, LIGHT)
    cv.text(x + 18, y + h - 30, "FIRST FOREIGN ASTRONAUT ABOARD", 2, PAPER)


def draw_office(cv, x, y):
    cv.rect(x + 6, y + 34, 50, 26, INK)
    cv.rect(x + 10, y + 40, 42, 4, PAPER)
    cv.line(x + 31, y + 6, x + 31, y + 34, INK, 3)
    cv.rect(x + 31, y + 6, 22, 12, RED)


def draw_store(cv, x, y):
    cv.rect(x + 4, y + 30, 54, 30, INK)
    cv.rect(x + 8, y + 20, 46, 10, RED)
    cv.rect(x + 22, y + 40, 18, 20, PAPER)


def draw_columns(cv, x, y):
    cv.rect(x + 6, y + 34, 50, 6, INK)
    cv.rect(x + 10, y + 40, 42, 4, INK)
    for i in range(4):
        cv.rect(x + 12 + i * 11, y + 20, 5, 14, INK)
    cv.disc(x + 31, y + 14, 10, INK)
    cv.rect(x + 29, y + 0, 4, 6, INK)


def draw_toll_chart(cv, x, y):
    bars = [14, 22, 30, 38, 46]
    for i, bh in enumerate(bars):
        cv.rect(x + i * 12, y + 56 - bh, 8, bh, RED)
    cv.rect(x, y + 56, 60, 3, INK)


def story(cv, x, y, w, icon, kicker, headline, body):
    cv.text(x, y, kicker, 2, RED)
    y += 22
    y = cv.wrapped(x, y, headline, 2, INK, w, leading=18)
    y += 4
    icon(cv, x, y)
    y = cv.wrapped(x + 72, y, body, 2, INK, w - 72, leading=18)
    return y


def write_png(path, cv):
    raw = b""
    for yy in range(cv.height):
        raw += b"\x00"
        raw += bytes(cv.pixels[yy * cv.width * 3:(yy + 1) * cv.width * 3])
    data = zlib.compress(raw, 9)

    def chunk(kind, payload):
        out = struct.pack(">I", len(payload)) + kind + payload
        out += struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.width, cv.height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    cv.frame(8, 8, WIDTH - 16, HEIGHT - 16, INK, 4)
    cv.centred(28, "THE WORLD TODAY", 5, INK)
    cv.centred(78, "THURSDAY 26 NOVEMBER 2026", 2, GREY)
    cv.rect(32, 104, WIDTH - 64, 3, INK)
    y = cv.wrapped(32, 120, "SHENZHOU-24: FIRST FOREIGN ASTRONAUT REACHES TIANGONG", 3, INK, WIDTH - 64, leading=28)
    draw_rocket(cv, 32, y + 8, WIDTH - 64, 200)
    y = y + 216
    y = cv.wrapped(32, y, "CHINA LAUNCHED SHENZHOU-24 ON WEDNESDAY, CARRYING PAKISTANI PILOT MUHAMMAD ZEESHAN ALI, THE FIRST FOREIGNER TO BOARD THE TIANGONG SPACE STATION. COMMANDER TANG HONGBO AND WU YI FLEW WITH HIM. THE CREW DOCKED IN 3.5 HOURS AND WILL RUN 90 EXPERIMENTS. ALI STAYS ABOUT A WEEK.", 2, INK, WIDTH - 64, leading=18)
    cv.rect(32, y + 6, WIDTH - 64, 3, INK)
    top = y + 18
    end1 = story(cv, 32, top, 464, draw_columns, "CHINA",
                 "SHANGHAI CHIEF UNDER PROBE",
                 "CHINA IS INVESTIGATING SHANGHAI PARTY CHIEF CHEN JINING, A POLITBURO MEMBER, FOR SUSPECTED SERIOUS VIOLATIONS. HE IS THE FOURTH POLITBURO MEMBER PROBED SINCE 2025.")
    end2 = story(cv, 528, top, 464, draw_toll_chart, "UKRAINE",
                 "ROSSTAT LEAK: NEARLY 500,000 DEAD",
                 "LEAKED RUSSIAN DATA ANALYSED BY THE BBC, MEDUZA AND MEDIAZONA PUTS THE MILITARY DEATH TOLL NEAR 500,000, ABOUT 700,000 COUNTING THE MISSING.")
    mid = max(end1, end2)
    cv.rect(32, mid + 8, WIDTH - 64, 3, INK)
    top2 = mid + 20
    end3 = story(cv, 32, top2, 464, draw_office, "DIPLOMACY",
                 "NORTH KOREA EXPELS SWISS ENVOY",
                 "PYONGYANG DECLARED SYLVAIN ASTIER PERSONA NON GRATA AND ORDERED HIM OUT IN 48 HOURS, CLOSING THE SWISS OFFICE REOPENED IN OCTOBER. THE MOVE FOLLOWS SWISS SANCTIONS ON THE SONGDOWON CHILDREN'S CAMP.")
    end4 = story(cv, 528, top2, 464, draw_store, "COLOMBIA",
                 "ALL 20 HOSTAGES FREED IN CARTAGENA",
                 "FORCES STORMED AN EXITO SUPERMARKET AFTER A 17-HOUR SIEGE, RESCUING ALL 20 HOSTAGES. ONE CAPTOR WAS KILLED. TEN PEOPLE HAD BEEN FREED EARLIER.")
    bottom = max(end3, end4)
    cv.rect(32, bottom + 8, WIDTH - 64, 3, INK)
    cv.wrapped(32, bottom + 18, "SOLOMONS CHOOSE AUSTRALIA AS PRIMARY SECURITY PARTNER + BANGLADESH GARMENT PAY UP 36% + INDIA MARKS CONSTITUTION DAY + MERCURY MISSION ARRIVES AFTER 8 YEARS + US PREPARING NEW TARIFF PLAN", 2, GREY, WIDTH - 64, leading=18)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), cv)


if __name__ == "__main__":
    main()
