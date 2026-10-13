"""
Generates the console screenshots used in the project review.

How it works: the REAL program (main.run_menu) is executed with scripted
keyboard input. Everything the program prints, plus the typed answers, is
recorded and drawn as an image that looks like a terminal window.
(Typed answers are shown in yellow.)  A temporary data file is used, so the
real students.txt is not changed.

Run from the project folder:   python screenshots/generate_screenshots.py
Needs Pillow for drawing:      pip install pillow
"""

import builtins
import contextlib
import os
import sys
import tempfile
from unittest import mock

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATHS = ["C:/Windows/Fonts/consola.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]

BG, FG, INPUT_COLOR, BAR = (12, 12, 12), (204, 204, 204), (249, 241, 165), (45, 45, 48)


class Recorder:
    """Collects printed text and typed answers as (text, kind) pieces."""
    def __init__(self):
        self.pieces = []

    def write(self, text):
        if text:
            self.pieces.append((text, "out"))
        return len(text)

    def flush(self):
        pass

    def lines(self):
        """Return a list of lines; each line is a list of (text, kind) runs."""
        result, current = [], []
        for text, kind in self.pieces:
            parts = text.split("\n")
            for i, part in enumerate(parts):
                if i > 0:
                    result.append(current)
                    current = []
                if part:
                    current.append((part, kind))
        if current:
            result.append(current)
        return result


def run_session(path, answers):
    """Run the real menu with scripted answers; return the recorded lines."""
    recorder = Recorder()
    answer_iter = iter(answers)

    def fake_input(prompt=""):
        recorder.write(prompt)
        answer = next(answer_iter)
        recorder.pieces.append((answer + "\n", "in"))
        return answer

    with mock.patch.object(builtins, "input", fake_input):
        with contextlib.redirect_stdout(recorder):
            main.run_menu(main.StudentManagementSystem(path))
    return recorder.lines()


def line_text(line):
    return "".join(text for text, _ in line)


def split_cycles(lines):
    """Split a session into 'menu + one operation' blocks."""
    starts = []
    for i in range(len(lines) - 1):
        if line_text(lines[i]).startswith("=====") and "STUDENT MANAGEMENT" in line_text(lines[i + 1]):
            starts.append(max(i - 1, 0))          # include the blank line before the menu
    starts.append(len(lines))
    return [lines[starts[k]:starts[k + 1]] for k in range(len(starts) - 1)]


def without_menu(cycle):
    """Drop the menu box (keeps 'Enter your choice' line and the output)."""
    for i, line in enumerate(cycle):
        if line_text(line).startswith("Enter your choice"):
            return cycle[i:]
    return cycle


def trim_blank_edges(lines):
    while lines and not line_text(lines[0]).strip():
        lines = lines[1:]
    while lines and not line_text(lines[-1]).strip():
        lines = lines[:-1]
    return lines


def render(lines, filename, title="python main.py"):
    """Draw lines as a terminal window; save to filename (if given) and return the image."""
    font = None
    for candidate in FONT_PATHS:
        if os.path.exists(candidate):
            font = ImageFont.truetype(candidate, 22)
            break
    if font is None:
        raise SystemExit("No monospaced TrueType font found.")
    char_w = font.getlength("M")
    line_h, pad, bar_h = 30, 24, 40
    widest = max((len(line_text(l)) for l in lines), default=20)
    width = int(max(widest * char_w + 2 * pad, 700))
    height = bar_h + pad * 2 + line_h * len(lines)
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, bar_h], fill=BAR)
    for k, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([16 + k * 26, 13, 30 + k * 26, 27], fill=color)
    draw.text((width // 2 - len(title) * char_w / 4, 8), title, font=font, fill=(180, 180, 180))
    y = bar_h + pad
    for line in lines:
        x = pad
        for text, kind in line:
            draw.text((x, y), text, font=font, fill=INPUT_COLOR if kind == "in" else FG)
            x += char_w * len(text)
        y += line_h
    if filename:
        image.save(os.path.join(OUT_DIR, filename))
        print("saved", filename, "(%dx%d)" % (width, height))
    return image


def stack(*blocks):
    """Join several blocks of lines, with one blank line between them."""
    result = []
    for block in blocks:
        if result:
            result.append([])
        result.extend(trim_blank_edges(block))
    return result


def find_cycle(cycles, choice, nth=0):
    """Find the nth cycle where the menu choice typed was `choice`."""
    hits = [c for c in cycles
            if any(line_text(l).startswith("Enter your choice: " + choice) for l in c)]
    return hits[nth]


def main_script():
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, "students.txt")      # starts as a NEW file (first run)

    # 1. main menu
    menu_lines = run_session(path, ["7"])
    render(trim_blank_edges(split_cycles(menu_lines)[0]), "01_main_menu.png")

    # Session A: all operations in a single run
    answers = [
        "1", "1", "Sample Student One", "CSE", "8.5",
        "1", "2", "Sample Student Two", "IT", "7.25",
        "1", "3", "Sample Student Three", "ENTC", "9.1",
        "1", "1",                                    # duplicate roll number
        "2",                                         # display
        "3", "2",                                    # search (found)
        "3", "99",                                   # search (not found)
        "4", "2", "", "", "12",                      # update with invalid CGPA
        "4", "2", "", "", "8.0",                     # update with valid CGPA
        "6",                                         # average of 3 students
        "5", "1",                                    # delete existing
        "5", "99",                                   # delete missing
        "7"]
    lines = run_session(path, answers)
    cycles = split_cycles(lines)

    add_ok, add_dup = find_cycle(cycles, "1", 0), find_cycle(cycles, "1", 3)
    render(stack(without_menu(add_ok), without_menu(add_dup)), "02_add_student.png")

    render(trim_blank_edges(without_menu(find_cycle(cycles, "2"))), "03_display_students.png")

    render(stack(without_menu(find_cycle(cycles, "3", 0)), without_menu(find_cycle(cycles, "3", 1))),
           "04_search_student.png")

    render(stack(without_menu(find_cycle(cycles, "4", 0)), without_menu(find_cycle(cycles, "4", 1))),
           "05_update_student.png")

    render(stack(without_menu(find_cycle(cycles, "5", 0)), without_menu(find_cycle(cycles, "5", 1))),
           "06_delete_student.png")

    render(trim_blank_edges(without_menu(find_cycle(cycles, "6"))), "07_average_cgpa.png")

    # Independent check of the numbers shown on screen (8.5 + 8.0 + 9.1) / 3
    avg_text = "\n".join(line_text(l) for l in find_cycle(cycles, "6"))
    assert "Average CGPA: 8.53" in avg_text, avg_text

    # 8. Persistence: brand-new program run (records loaded from the file),
    #    above the contents of the data file itself.
    restart_cycles = split_cycles(run_session(path, ["2", "7"]))
    left = render(trim_blank_edges(without_menu(restart_cycles[0])), None, "python main.py  (new run)")
    with open(path, encoding="utf-8") as f:
        file_lines = [[(l, "out")] for l in f.read().splitlines()]
    right = render(file_lines, None, "students.txt  (data file)")
    gap = 16
    combined = Image.new("RGB", (max(left.width, right.width), left.height + right.height + gap),
                         (255, 255, 255))
    combined.paste(left, (0, 0))
    combined.paste(right, (0, left.height + gap))
    combined.save(os.path.join(OUT_DIR, "08_data_persistence.png"))
    print("saved 08_data_persistence.png (%dx%d)" % combined.size)


if __name__ == "__main__":
    main_script()
