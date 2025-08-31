import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import edge_tts
from edge_tts.submaker import SubMaker
import threading
import re
import os
import glob

def get_filename(text):
    """Generates a safe filename from the first 10 characters of the text."""
    name = ''.join(re.findall(r'\S', text))[:10]
    return f"{name}.mp3"

async def run_edge_tts_async(text, filename, voice, rate, progress_callback, on_finish):
    """Uses the edge_tts library directly to generate audio and subtitles asynchronously."""
    try:
        progress_callback(10)
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        sub_maker = SubMaker()
        srt_filename = filename.rsplit('.', 1)[0] + '.srt'

        with open(filename, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    sub_maker.add_sub(chunk["offset"], chunk["duration"], chunk["text"])
        
        with open(srt_filename, "w", encoding="utf-8") as file:
            file.write(sub_maker.get_srt())

        progress_callback(100)
        on_finish(None)
    except Exception as e:
        on_finish(f"生成失败: {e}")

def on_generate():
    """Handles the button click event to start the TTS process."""
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("提示", "请输入要合成的文本！")
        return
    
    filename = get_filename(text)
    voice = voice_var.get()
    rate_val = rate_var.get()
    rate_str = f"{rate_val:+}%"

    progress_var.set(0)
    progress_bar.update()
    btn_generate.config(state=tk.DISABLED)

    def progress_callback(val):
        root.after(0, progress_var.set, val)
        root.after(0, progress_bar.update)

    def on_finish(error_msg):
        def final_update():
            btn_generate.config(state=tk.NORMAL)
            if error_msg:
                messagebox.showerror("错误", error_msg)
            else:
                messagebox.showinfo("完成", f"音频已生成: {filename}")
                refresh_mp3_list()
        root.after(0, final_update)

    def async_runner():
        try:
            asyncio.run(run_edge_tts_async(text, filename, voice, rate_str, progress_callback, on_finish))
        except Exception as e:
            on_finish(f"线程启动失败: {e}")

    threading.Thread(target=async_runner, daemon=True).start()

def refresh_mp3_list():
    """Refreshes the list of MP3 files in the GUI."""
    mp3_listbox.delete(0, tk.END)
    mp3_files = glob.glob('*.mp3')
    for f in sorted(mp3_files):
        mp3_listbox.insert(tk.END, f)

def play_selected():
    """Plays the selected MP3 file using the default system player."""
    selected_indices = mp3_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("提示", "请先选择一个要播放的文件！")
        return
    selected_file = mp3_listbox.get(selected_indices[0])
    try:
        os.startfile(selected_file)
    except Exception as e:
        messagebox.showerror("播放失败", f"无法播放文件: {e}")

def delete_selected_file():
    """Deletes the selected MP3 and its corresponding SRT file."""
    selected_indices = mp3_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("提示", "请先选择要删除的文件！")
        return
    
    selected_file = mp3_listbox.get(selected_indices[0])
    
    if messagebox.askyesno("确认删除", f"您确定要永久删除文件 \n'{selected_file}' \n及其关联的字幕文件吗？此操作无法撤销。"):
        try:
            srt_file = selected_file.rsplit('.', 1)[0] + '.srt'
            os.remove(selected_file)
            if os.path.exists(srt_file):
                os.remove(srt_file)
            refresh_mp3_list()
        except OSError as e:
            messagebox.showerror("删除失败", f"无法删除文件: {e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("Edge-TTS 语音合成 GUI (v4)")

# ... (rest of the GUI setup is the same as before)

# --- Top Frame for TTS ---
tts_frame = ttk.Frame(root, padding="10")
tts_frame.pack(fill="x")

tk.Label(tts_frame, text="请输入要合成的文本：").pack(anchor="w")
text_input = tk.Text(tts_frame, width=60, height=8)
text_input.pack(fill="x", expand=True, pady=(0, 5))

# --- Options Frame ---
options_frame = ttk.Frame(tts_frame)
options_frame.pack(fill="x", pady=5)

# --- Voice Selection ---
tk.Label(options_frame, text="选择音色：").pack(side="left", padx=(0, 5))
voice_options = [
    ("普-晓晓(女)", "zh-CN-XiaoxiaoNeural"),
    ("普-晓伊(女)", "zh-CN-XiaoyiNeural"),
    ("普-云扬(男)", "zh-CN-YunyangNeural"),
    ("普-云希(男)", "zh-CN-YunxiNeural"),
    ("普-云野(男)", "zh-CN-YunyeNeural"),
    ("普-云泽(男)", "zh-CN-YunzeNeural"),
    ("普-晓辰(女)", "zh-CN-XiaochenNeural"),
    ("普-晓涵(女)", "zh-CN-XiaohanNeural"),
    ("普-晓墨(女)", "zh-CN-XiaomoNeural"),
    ("普-晓秋(女)", "zh-CN-XiaoqiuNeural"),
    ("普-晓睿(女)", "zh-CN-XiaoruiNeural"),
    ("普-晓双(女)", "zh-CN-XiaoshuangNeural"),
    ("普-晓颜(女)", "zh-CN-XiaoyanNeural"),
    ("普-晓悠(女)", "zh-CN-XiaoyouNeural"),
    ("普-云枫(男)", "zh-CN-YunfengNeural"),
    ("普-云皓(男)", "zh-CN-YunhaoNeural"),
    ("普-云健(男)", "zh-CN-YunjianNeural"),
    ("普-云夏(男)", "zh-CN-YunxiaNeural"),
    ("辽宁-小北(女)", "zh-CN-liaoning-XiaobeiNeural"),
    ("陕西-晓妮(女)", "zh-CN-shaanxi-XiaoniNeural"),
    ("四川-云希(男)", "zh-CN-sichuan-YunxiNeural"),
    ("河南-云登(男)", "zh-CN-henan-YundengNeural"),
    ("山东-云翔(男)", "zh-CN-shandong-YunxiangNeural"),
    ("台湾-晓臻(女)", "zh-TW-HsiaoChenNeural"),
    ("台湾-晓雨(女)", "zh-TW-HsiaoYuNeural"),
    ("台湾-云哲(男)", "zh-TW-YunJheNeural"),
    ("香港-晓佳(女)", "zh-HK-HiuGaaiNeural"),
    ("香港-晓曼(女)", "zh-HK-HiuMaanNeural"),
    ("香港-云龙(男)", "zh-HK-WanLungNeural"),
    ("吴语-晓彤(女)", "wuu-CN-XiaotongNeural"),
    ("吴语-云哲(男)", "wuu-CN-YunzheNeural"),
    ("粤语-晓敏(女)", "yue-CN-XiaoMinNeural"),
    ("粤语-云松(男)", "yue-CN-YunSongNeural"),
]
voice_var = tk.StringVar()
voice_menu = ttk.Combobox(options_frame, textvariable=voice_var, values=[v[0] for v in voice_options], state="readonly", width=20)
voice_menu.pack(side="left", padx=(0, 20))

def update_voice_var(event=None):
    idx = voice_menu.current()
    if idx >= 0:
        voice_var.set(voice_options[idx][1])
voice_menu.bind("<<ComboboxSelected>>", update_voice_var)
voice_menu.current(0)
update_voice_var()

# --- Rate Selection ---
rate_var = tk.IntVar(value=0)
rate_label_text = tk.StringVar()
def update_rate_label(*args):
    rate_label_text.set(f"语速: {rate_var.get():+d}%")
rate_label_text.set("语速: +0%")

tk.Label(options_frame, textvariable=rate_label_text).pack(side="left", padx=(0, 5))
rate_slider = ttk.Scale(options_frame, from_=-100, to=100, variable=rate_var, orient="horizontal", command=update_rate_label)
rate_slider.pack(side="left", fill="x", expand=True)


btn_generate = ttk.Button(tts_frame, text="生成音频", command=on_generate)
btn_generate.pack(pady=10)

progress_var = tk.IntVar(value=0)
progress_bar = ttk.Progressbar(tts_frame, maximum=100, variable=progress_var)
progress_bar.pack(fill="x", expand=True, pady=(0,5))

# --- Separator ---
ttk.Separator(root, orient='horizontal').pack(fill='x', padx=10, pady=5)

# --- Bottom Frame for Player ---
player_frame = ttk.LabelFrame(root, text="MP3 文件列表", padding="10")
player_frame.pack(fill="both", expand=True, padx=10, pady=10)

list_frame = ttk.Frame(player_frame)
list_frame.pack(fill="both", expand=True)

scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
mp3_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, width=60)
scrollbar.config(command=mp3_listbox.yview)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
mp3_listbox.pack(side=tk.LEFT, fill="both", expand=True)

player_buttons_frame = ttk.Frame(player_frame)
player_buttons_frame.pack(fill="x", pady=5)

btn_play = ttk.Button(player_buttons_frame, text="播放选中文件", command=play_selected)
btn_play.pack(side="left", expand=True, fill="x", padx=2)

btn_refresh = ttk.Button(player_buttons_frame, text="刷新列表", command=refresh_mp3_list)
btn_refresh.pack(side="left", expand=True, fill="x", padx=2)

btn_delete = ttk.Button(player_buttons_frame, text="删除选中文件", command=delete_selected_file)
btn_delete.pack(side="left", expand=True, fill="x", padx=2)

# Initial population of the list
refresh_mp3_list()

root.mainloop()