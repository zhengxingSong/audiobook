#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""批量下载GPT-SoVITS原神角色模型"""

import os
import sys
import io
from pathlib import Path
from modelscope.hub.file_download import model_file_download

# 设置标准输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 角色列表
CHARACTERS = [
    "博士", "女士", "白老先生", "花角玉将", "队长", "七七", "上杉", "丹吉尔",
    "丽莎", "久利须", "久岐忍", "乐平波琳", "九条裟罗", "九条镰治", "云堇",
    "五百藏", "五郎", "伊利亚斯", "伊安珊", "伊迪娅", "优菈", "佐西摩斯",
    "元太", "克列门特", "克洛琳德", "克罗索", "克雷薇", "八重神子", "凝光",
    "凯亚", "凯瑟琳", "刻晴", "劳维克", "北斗", "千织", "博易", "博来",
    "卡佩", "卡利贝尔", "卡维", "卡莉露", "卡齐娜", "可莉", "叶德", "吴船长",
    "哲平", "嘉明", "嘉玛", "嘉良", "回声海螺", "坎蒂丝", "埃勒曼", "埃尔欣根",
    "埃德", "埃泽", "埃洛伊", "基尼奇", "塔杰·拉德卡尼", "塞塔蕾", "塞琉斯",
    "夏姆", "夏沃蕾", "夏洛蒂", "夏温", "多莉", "夜兰", "夜神", "大慈树王",
    "大肉丸", "天叔", "天目十五", "奥兹", "妮赫佳", "妮露", "娜维娅", "安柏",
    "安西", "宛烟", "宵宫", "小狼", "居勒什", "巴穆恩", "巴达维", "希巴拉克",
    "希格雯", "希诺宁", "席尔万", "常九爷", "庇兰", "康纳", "式大将", "弗洛朗",
    "弗洛莱恩", "德沃沙克", "恕筠", "恰斯卡", "恶龙", "悦", "慧心", "戴因斯雷布",
    "托克", "托马", "拉赫曼", "拉齐", "掇星攫辰天君", "探长", "提纳里", "斯坦利",
    "旁白", "早柚", "昆钧", "杏仁", "杜吉耶", "杜拉夫", "松浦", "林尼", "枫原万叶",
    "柊千里", "查尔斯", "柯莱", "梦见月瑞希", "欧洛伦", "欧菲妮", "毗伽尔",
    "沙扎曼", "波洛", "波顿", "泽维尔", "派蒙", "流浪者", "浮游水蕈兽·元素生命",
    "海妮耶", "海芭夏", "深渊使徒", "深渊法师", "渊上", "温迪", "漱玉", "烟绯",
    "爱德琳", "爱贝尔", "特拉佐莉", "特立尼达", "玛乔丽", "玛塞勒", "玛拉妮",
    "玛格丽特", "玛薇卡", "珊瑚", "珊瑚宫心海", "珐露珊", "班尼特", "琳妮特",
    "琴", "瑶瑶", "瓦伊纳", "甘雨", "田铁嘴", "申鹤", "留云借风真君", "白术",
    "百闻", "知易", "石头", "砂糖", "祖莉亚·德斯特雷", "神里绫人", "神里绫华",
    "科尔特", "穆托塔", "空", "笼钓瓶一心", "米卡", "纯水精灵", "纳比尔",
    "纳西妲", "绮良良", "维兰德", "维奇琳", "维查玛", "罗莎莉亚", "羽生田千鹤",
    "老孟", "胡桃", "舒伯特", "艾伯特", "艾尔海森", "艾德加", "艾文", "艾梅莉埃",
    "艾莉丝", "芙卡洛斯", "芙宁娜", "芭芭拉", "茜特菈莉", "荒泷一斗", "荧",
    "莎拉", "莫嘉娜", "莫塞伊思", "莫娜", "莱依拉", "莱欧斯利", "莺儿", "菲米尼",
    "菲谢尔", "萍姥姥", "萨赫哈蒂", "萨齐因", "葵可", "蒂玛乌斯", "蒙吕松", "蓝砚",
    "薇涅尔", "行秋", "西拉杰", "言笑", "诺艾尔", "谢赫祖拜尔", "赛索斯", "赛诺",
    "辛焱", "达达利亚", "迈勒斯", "迈蒙", "远黛", "迪卢克", "迪奥娜", "迪娜泽黛",
    "迪尔菲", "迪希雅", "那维莱特", "重云", "钟离", "长生", "闲云", "阿乔", "阿伽娅",
    "阿佩普", "阿圆", "阿娜耶", "阿守", "阿尔卡米", "阿尔帕", "阿巴图伊", "阿扎尔",
    "阿托莎", "阿拉夫", "阿晃", "阿洛瓦", "阿祇", "阿米娜", "阿蕾奇诺", "阿贝多",
    "陆行岩本真蕈·元素生命", "雷泽", "雷电将军", "霍夫曼", "香菱", "魈", "鹿野奈奈",
    "鹿野院平藏", "龙二"
]

MODEL_ID = "aihobbyist/GPT-SoVITS_Model_Collection"
DOWNLOAD_DIR = Path("D:/GPT-SoVITS-Downloads")
LOG_FILE = DOWNLOAD_DIR / "download_log.txt"

def download_character(char_name: str) -> bool:
    """下载单个角色模型"""
    file_path = f"原神/中文/{char_name}_ZH.zip"
    try:
        local_path = model_file_download(
            model_id=MODEL_ID,
            file_path=file_path,
            cache_dir=str(DOWNLOAD_DIR / "cache")
        )
        return True
    except Exception as e:
        log(f"ERROR downloading {char_name}: {e}")
        return False

def log(msg: str):
    """记录日志"""
    try:
        print(msg)
    except:
        print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    log(f"Start downloading {len(CHARACTERS)} character models")
    log(f"Target directory: {DOWNLOAD_DIR}")

    success = 0
    failed = 0
    failed_chars = []

    for i, char in enumerate(CHARACTERS, 1):
        log(f"[{i}/{len(CHARACTERS)}] Downloading {char}...")
        if download_character(char):
            success += 1
            log(f"  OK: {char}")
        else:
            failed += 1
            failed_chars.append(char)
            log(f"  FAIL: {char}")

    log(f"\n=== Download Complete ===")
    log(f"Success: {success}")
    log(f"Failed: {failed}")
    if failed_chars:
        log(f"Failed characters: {', '.join(failed_chars)}")

if __name__ == "__main__":
    main()