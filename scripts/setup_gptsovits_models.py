#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
解压和配置GPT-SoVITS原神角色模型

将下载的zip文件解压到目标目录，并生成音色库数据库
"""

import os
import sys
import io
import zipfile
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

# 设置标准输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 配置 - 优先使用主目录，回退到temp目录
SOURCE_DIR = Path("D:/GPT-SoVITS-Downloads/cache/aihobbyist/GPT-SoVITS_Model_Collection/原神/中文")
SOURCE_DIR_ALT = Path("D:/GPT-SoVITS-Downloads/cache/._____temp/aihobbyist/GPT-SoVITS_Model_Collection/原神/中文")
TARGET_DIR = Path("D:/GPT-SoVITS")
LOG_FILE = TARGET_DIR / "setup_log.txt"

# 目标目录
GPT_MODELS_DIR = TARGET_DIR / "models" / "GPT_models"
SOVITS_MODELS_DIR = TARGET_DIR / "models" / "SoVITS_models"
REFERENCE_AUDIOS_DIR = TARGET_DIR / "reference_audios"
CONFIGS_DIR = TARGET_DIR / "configs"

# 角色性别映射（常见角色）
MALE_CHARS = {
    "钟离", "迪卢克", "艾尔海森", "赛诺", "提纳里", "卡维", "托马", "班尼特",
    "雷泽", "重云", "行秋", "魈", "温迪", "枫原万叶", "荒泷一斗", "神里绫人",
    "五郎", "鹿野院平藏", "流浪者", "林尼", "莱欧斯利", "那维莱特", "闲云",
    "嘉明", "基尼奇", "欧洛伦", "赛索斯", "阿贝多", "空"
}

FEMALE_CHARS = {
    "刻晴", "甘雨", "胡桃", "雷电将军", "神里绫华", "宵宫", "八重神子", "珊瑚宫心海",
    "早柚", "九条裟罗", "夜兰", "申鹤", "云堇", "妮露", "纳西妲", "芙宁娜",
    "娜维娅", "夏沃蕾", "闲云", "千织", "绮良良", "琳妮特", "菲米尼", "克洛琳德",
    "希格雯", "艾梅莉埃", "玛拉妮", "茜特菈莉", "恰斯卡", "玛薇卡", "伊安珊", "荧",
    "琴", "莫娜", "芭芭拉", "安柏", "丽莎", "诺艾尔", "菲谢尔", "砂糖",
    "凝光", "北斗", "香菱", "罗莎莉亚", "烟绯", "优菈", "可莉", "七七",
    "瑶瑶", "白术", "坎蒂丝", "多莉", "珐露珊", "迪奥娜", "久岐忍", "蓝砚",
    "梦见月瑞希"
}

NEUTRAL_CHARS = {
    "派蒙", "旁白"
}


def log(msg: str):
    """记录日志"""
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def get_gender(char_name: str) -> str:
    """推断角色性别"""
    if char_name in MALE_CHARS:
        return "男"
    elif char_name in FEMALE_CHARS:
        return "女"
    elif char_name in NEUTRAL_CHARS:
        return "中性"
    else:
        # 默认根据名字特征推断
        return "未知"


def extract_character_name(zip_path: Path) -> str:
    """从zip文件名提取角色名"""
    # 格式: 「钟离」_ZH.zip 或 钟离_ZH.zip
    name = zip_path.stem  # 去掉.zip
    # 去掉 _ZH 后缀
    if name.endswith("_ZH"):
        name = name[:-3]
    # 去掉「」符号
    name = name.strip("「」")
    return name


def create_directories():
    """创建目标目录"""
    for d in [GPT_MODELS_DIR, SOVITS_MODELS_DIR, REFERENCE_AUDIOS_DIR, CONFIGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    log(f"Created directories under {TARGET_DIR}")


def process_zip(zip_path: Path) -> Optional[dict]:
    """处理单个zip文件，返回角色信息"""
    char_name = extract_character_name(zip_path)
    log(f"\nProcessing: {char_name} ({zip_path.name})")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 列出文件
            file_list = zf.namelist()

            # 查找模型文件和参考音频
            ckpt_file = None
            pth_file = None
            ref_audio = None

            for f in file_list:
                if f.endswith('.ckpt'):
                    ckpt_file = f
                elif f.endswith('.pth'):
                    pth_file = f
                elif '.wav' in f and 'reference_audios' in f:
                    if ref_audio is None:  # 只取第一个
                        ref_audio = f

            # 解压到临时目录
            temp_dir = TARGET_DIR / "temp_extract"
            temp_dir.mkdir(exist_ok=True)

            zf.extractall(temp_dir)

            # 移动模型文件
            if ckpt_file:
                src = temp_dir / ckpt_file
                dst = GPT_MODELS_DIR / f"{char_name}_ZH-e10.ckpt"
                shutil.move(str(src), str(dst))
                log(f"  Moved GPT model: {dst.name}")

            if pth_file:
                src = temp_dir / pth_file
                dst = SOVITS_MODELS_DIR / f"{char_name}_ZH_e10_s220_l32.pth"
                shutil.move(str(src), str(dst))
                log(f"  Moved SoVITS model: {dst.name}")

            # 移动参考音频
            if ref_audio:
                ref_dir = REFERENCE_AUDIOS_DIR / char_name / "中文" / "emotions"
                ref_dir.mkdir(parents=True, exist_ok=True)
                src = temp_dir / ref_audio
                dst = ref_dir / Path(ref_audio).name
                shutil.move(str(src), str(dst))
                ref_audio_path = str(dst)
                log(f"  Moved reference audio: {dst.name}")
            else:
                ref_audio_path = None

            # 清理临时目录中的解压内容
            for item in temp_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)

            return {
                "name": char_name,
                "gender": get_gender(char_name),
                "ref_audio": ref_audio_path,
                "ckpt": f"{char_name}_ZH-e10.ckpt" if ckpt_file else None,
                "pth": f"{char_name}_ZH_e10_s220_l32.pth" if pth_file else None,
            }

    except Exception as e:
        log(f"  ERROR: {e}")
        return None


def create_voice_library(characters: list[dict]):
    """创建音色库SQLite数据库"""
    db_path = CONFIGS_DIR / "voice_library.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voices (
        voice_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        gender TEXT,
        age_range TEXT DEFAULT '成年',
        tags TEXT,
        description TEXT,
        audio_path TEXT,
        ckpt_path TEXT,
        pth_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 插入数据
    for char in characters:
        voice_id = f"genshin_{char['name']}"
        tags = ["原神", char['gender']]

        cursor.execute('''
        INSERT OR REPLACE INTO voices
        (voice_id, name, gender, tags, description, audio_path, ckpt_path, pth_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            voice_id,
            char['name'],
            char['gender'],
            ','.join(tags),
            f"原神角色-{char['name']}",
            char.get('ref_audio'),
            str(GPT_MODELS_DIR / char['ckpt']) if char.get('ckpt') else None,
            str(SOVITS_MODELS_DIR / char['pth']) if char.get('pth') else None,
        ))

    conn.commit()
    conn.close()
    log(f"\nCreated voice library with {len(characters)} voices at {db_path}")


def main():
    """主函数"""
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    log("=" * 60)
    log("GPT-SoVITS 原神角色模型配置")
    log("=" * 60)

    # 创建目录
    create_directories()

    # 查找所有zip文件 - 先检查主目录，再检查temp目录
    zip_files = list(SOURCE_DIR.glob("*.zip"))
    source_used = SOURCE_DIR

    if not zip_files and SOURCE_DIR_ALT.exists():
        zip_files = list(SOURCE_DIR_ALT.glob("*.zip"))
        source_used = SOURCE_DIR_ALT

    log(f"\nFound {len(zip_files)} zip files in {source_used}")

    if not zip_files:
        log("No zip files found! Please wait for download to complete.")
        return

    # 处理每个zip
    characters = []
    success = 0
    failed = 0

    for i, zip_path in enumerate(zip_files, 1):
        log(f"\n[{i}/{len(zip_files)}]")
        result = process_zip(zip_path)
        if result:
            characters.append(result)
            success += 1
        else:
            failed += 1

    # 创建音色库
    if characters:
        create_voice_library(characters)

    # 清理临时目录
    temp_dir = TARGET_DIR / "temp_extract"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    log("\n" + "=" * 60)
    log(f"Setup Complete!")
    log(f"  Success: {success}")
    log(f"  Failed: {failed}")
    log(f"  Total: {len(zip_files)}")
    log(f"\nModels saved to:")
    log(f"  GPT: {GPT_MODELS_DIR}")
    log(f"  SoVITS: {SOVITS_MODELS_DIR}")
    log(f"  Reference Audios: {REFERENCE_AUDIOS_DIR}")
    log(f"  Voice Library: {CONFIGS_DIR / 'voice_library.db'}")
    log("=" * 60)


if __name__ == "__main__":
    main()