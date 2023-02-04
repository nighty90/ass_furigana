import re
from pathlib import Path
from math import ceil
import tkinter as tk
from tkinter.filedialog import askopenfilename
from pykakasi import kakasi

KANJI_RE = r"[㐀-䶵一-鿋豈-頻]"
NOT_KANJI_RE = r"[^㐀-䶵一-鿋豈-頻]"
K_TIME_RE = r"(\{\\k\d+})"


def choose_file():
    root = tk.Tk()
    root.withdraw()
    return Path(askopenfilename())


def get_furi(word):
    if not re.search(KANJI_RE, word["orig"][-2:]):
        word["hira"] = word["hira"][:-2]
    elif not re.search(KANJI_RE, word["orig"][-1]):
        word["hira"] = word["hira"][:-1]

    furi_dict = {}
    word_kanjis = re.findall(KANJI_RE, word["orig"])
    if not word_kanjis:
        return furi_dict

    furi_length = ceil(len(word["hira"]) / len(word_kanjis))
    for i, kanji in enumerate(word_kanjis):
        start = i * furi_length
        end = start + furi_length
        furi_dict[kanji] = word["hira"][start:end]
    return furi_dict


def process_line(ass_line, kks_obj):
    ass_line_items = ass_line.split(",")
    text = ass_line_items[-1]
    text_items = re.split(K_TIME_RE, text)

    lyric = re.sub(K_TIME_RE, "", text)
    kks_res = kks_obj.convert(lyric)
    cur_word = kks_res.pop(0)
    cur_word_end = len(cur_word["orig"])
    cur_pos = 0
    processed_items = []
    for item in text_items:
        # if current position reach the end of current word, then get next word
        while cur_pos >= cur_word_end:
            cur_word = kks_res.pop(0)
            cur_word_end += len(cur_word["orig"])

        # item is not in the lyric, which means item is k_time
        if item not in lyric:
            processed_items.append(item)
            continue

        # item is in the lyric, but it does not contain any kanji
        if not re.search(KANJI_RE, item):
            processed_items.append(item)
            cur_pos += len(item)
            continue

        # item contains kanji
        char_add_furi = []
        cur_furi = get_furi(cur_word)
        for char in item:
            if cur_pos >= cur_word_end:
                cur_word = kks_res.pop(0)
                cur_furi = get_furi(cur_word)
                cur_word_end += len(cur_word["orig"])
            if re.match(KANJI_RE, char):
                char_add_furi.append(f"{char}|<{cur_furi[char]}")
            else:
                char_add_furi.append(char)
            cur_pos += 1
        item_add_furi = r"{\k0}".join(char_add_furi)
        processed_items.append(item_add_furi)

    processed_text = "".join(processed_items)
    ass_line = ass_line_items[:-1]
    ass_line.append(processed_text)
    return ",".join(ass_line)


if __name__ == "__main__":
    input_path = choose_file()
    ass = open(input_path, "r", encoding="utf-8")
    output_path = input_path.with_stem(input_path.stem + "_furigana")
    ass_furi = open(output_path, "w", encoding="utf-8")

    kks = kakasi()
    for line in ass:
        if not line.startswith("Dialogue: "):
            ass_furi.write(line)
        else:
            ass_furi.write(process_line(line, kks))

    ass.close()
    ass_furi.close()
