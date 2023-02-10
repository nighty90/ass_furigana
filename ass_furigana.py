import re
from pathlib import Path
from math import ceil
import tkinter as tk
from tkinter.filedialog import askopenfilename
from pykakasi import kakasi

KANJI_RE = r"[㐀-䶵一-鿋豈-頻]"
NOT_KANJI_RE = r"[^㐀-䶵一-鿋豈-頻]"
K_TIME_RE = r"(\{\\k\d+})"


# open a window for choosing file
def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = askopenfilename()
    if not file_path:
        print("No file is chosen. Exit.")
        exit()
    return Path(file_path)


# create a dictionary mapping kanji to hiragana
def get_furi(word):

    # simple deletion of the following hiraganas
    for i in range(-1, (-1*len(word["orig"]) - 1), -1):
        if word["orig"][i] != word["hira"][i]:
            i += 1
            if i != 0:
                word["hira"] = word["hira"][:i]
            break
    
    # create kanji - hiragana mapping
    # initialize
    furi_dict = {}
    word_kanjis = re.findall(KANJI_RE, word["orig"])
    if not word_kanjis:
        return furi_dict
    
    # evenly assign hiraganas to each kanji
    furi_length = ceil(len(word["hira"]) / len(word_kanjis))
    for i, kanji in enumerate(word_kanjis):
        start = i * furi_length
        end = start + furi_length
        furi_dict[kanji] = word["hira"][start:end]
    return furi_dict


# process a line in ass file
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

        # calculate and add k_time for each character
        item_k_time = re.search(r"\d+", processed_items[-1])
        item_k_time = int(item_k_time.group(0))
        time_each, time_mod = divmod(item_k_time, len(item))
        processed_items[-1] = r"{\k%s}" % (time_each + time_mod)
        char_k_time = r"{\k%s}" % time_each
        item_add_furi = char_k_time.join(char_add_furi)
        processed_items.append(item_add_furi)

    processed_text = "".join(processed_items)
    ass_line = ass_line_items[:-1]
    ass_line.append(processed_text)
    return ",".join(ass_line)


if __name__ == "__main__":
    # chooose the input file
    input_path = choose_file()
    ass = open(input_path, "r", encoding="utf-8")
    output_path = input_path.with_stem(input_path.stem + "_furigana")
    ass_furi = open(output_path, "w", encoding="utf-8")
    
    # process each line
    kks = kakasi()
    for line in ass:
        if not line.startswith("Dialogue: "):
            ass_furi.write(line)
        else:
            ass_furi.write(process_line(line, kks))

    ass.close()
    ass_furi.close()
