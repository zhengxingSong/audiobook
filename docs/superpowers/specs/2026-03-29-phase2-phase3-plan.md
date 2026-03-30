# Audiobook Converter - 后续阶段开发方案

> 本文档规划MVP Phase 1完成后的后续开发阶段

---

## 一、Phase 2: 场景音效 + 一致性控制

### 1.1 场景音效引擎

#### 1.1.1 功能概述

为有声书添加背景音乐和环境音效，将"有声书"升级为"音频剧"体验。

#### 1.1.2 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                    场景音效引擎                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入: 场景文本片段 + 角色状态                               │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ 场景识别器  │───▶│ 音效匹配器  │───▶│ 混音处理器  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │            │
│         ▼                  ▼                  ▼            │
│  场景类型标签        音效库查询          音量/时机控制       │
│  氛围判断            相似度匹配          淡入淡出           │
│                                                             │
│  输出: 音效配置 (环境音 + 背景音乐 + 混音参数)               │
└─────────────────────────────────────────────────────────────┘
```

#### 1.1.3 场景识别规则

**场景类型分类**:

| 场景类型 | 关键词标记 | 推荐环境音 | 推荐背景音乐 |
|---------|-----------|-----------|-------------|
| 室内-日常 | 房间、客厅、卧室 | 室内环境音 | 轻音乐 |
| 室内-紧张 | 审讯室、密室 | 寂静+心跳声 | 悬疑音乐 |
| 室外-白天 | 街道、广场、公园 | 人群声、鸟鸣 | 明快音乐 |
| 室外-夜晚 | 夜晚、月光、黑暗 | 虫鸣、风声 | 低沉音乐 |
| 自然-森林 | 森林、树林、山 | 鸟鸣、树叶沙沙 | 自然音乐 |
| 自然-水域 | 河边、湖边、海 | 水流声 | 舒缓音乐 |
| 天气-雨天 | 下雨、暴雨、雨声 | 雨声 | 忧伤音乐 |
| 天气-雪天 | 下雪、雪花、白雪 | 风声、踏雪声 | 纯净音乐 |
| 战斗场景 | 打斗、战斗、厮杀 | 武器碰撞声 | 激烈音乐 |
| 回忆场景 | 回忆、想起、当年 | 模糊音效 | 怀旧音乐 |

**氛围识别**:

```python
ATMOSPHERE_KEYWORDS = {
    "压抑": ["沉默", "压抑", "沉重", "窒息"],
    "悲伤": ["哭", "泪", "悲伤", "痛苦", "心碎"],
    "紧张": ["紧张", "危险", "不安", "恐惧"],
    "欢快": ["笑", "开心", "快乐", "喜悦"],
    "浪漫": ["温柔", "甜蜜", "爱情", "浪漫"],
    "神秘": ["神秘", "诡异", "未知", "谜"],
}
```

#### 1.1.4 音效库结构

```
~/.audiobook-converter/sound_library/
├── ambient/                    # 环境音
│   ├── indoor/
│   │   ├── room_ambient_01.wav
│   │   └── office_ambient_01.wav
│   ├── outdoor/
│   │   ├── street_day_01.wav
│   │   ├── street_night_01.wav
│   │   └── park_01.wav
│   ├── nature/
│   │   ├── forest_01.wav
│   │   ├── rain_heavy_01.wav
│   │   ├── rain_light_01.wav
│   │   └── wind_01.wav
│   └── weather/
│       ├── thunder_01.wav
│       └── snow_wind_01.wav
├── music/                      # 背景音乐
│   ├── emotional/
│   │   ├── sad_01.mp3
│   │   ├── happy_01.mp3
│   │   └── romantic_01.mp3
│   ├── atmospheric/
│   │   ├── suspense_01.mp3
│   │   ├── mysterious_01.mp3
│   │   └── peaceful_01.mp3
│   └── action/
│       ├── battle_01.mp3
│       └── tense_01.mp3
└── metadata.db                 # SQLite索引
```

#### 1.1.5 混音参数规范

| 音频层 | 默认音量 | 淡入时间 | 淡出时间 | 动态调节 |
|--------|---------|---------|---------|---------|
| 语音 | 1.0 (基准) | - | - | - |
| 环境音 | 0.2-0.4 | 2s | 1s | 情绪高潮时-0.1 |
| 背景音乐 | 0.1-0.2 | 3s | 2s | 情绪高潮时+0.05 |

**对话场景特殊处理**:
- 检测到对话时，环境音降低15%
- 对话结束后1秒恢复

#### 1.1.6 接口设计

```python
# src/audiobook/engines/sound_engine.py

@dataclass
class SoundConfig:
    """音效配置"""
    ambient_sound: Optional[str] = None      # 环境音ID
    background_music: Optional[str] = None   # 背景音乐ID
    ambient_volume: float = 0.3
    music_volume: float = 0.15
    fade_in: float = 2.0                     # 淡入秒数
    fade_out: float = 1.0                    # 淡出秒数
    crossfade: float = 1.0                   # 场景切换交叉淡入淡出


class SoundEngine:
    """场景音效引擎"""

    def __init__(self, library_path: str):
        self.library = SoundLibrary(library_path)

    def analyze_scene(self, text: str, character_states: dict) -> SceneAnalysis:
        """分析场景，返回场景类型和氛围"""

    def match_sound(self, analysis: SceneAnalysis) -> SoundConfig:
        """根据场景分析匹配合适的音效"""

    def mix_audio(
        self,
        voice_audio: bytes,
        sound_config: SoundConfig,
        duration: float
    ) -> bytes:
        """混合语音和音效，输出最终音频"""
```

#### 1.1.7 测试用例

- `test_scene_type_detection`: 测试场景类型识别
- `test_atmosphere_detection`: 测试氛围识别
- `test_sound_matching`: 测试音效匹配
- `test_mix_audio_parameters`: 测试混音参数
- `test_dialogue_volume_ducking`: 测试对话时音量降低

---

### 1.2 一致性控制器

#### 1.2.1 功能概述

确保同一角色在不同场景中保持声音特质连贯性，这是产品核心差异化功能。

#### 1.2.2 核心问题

GPT-SoVITS每次合成可能有细微差异，导致同一角色声音不一致。

#### 1.2.3 解决方案

```
┌─────────────────────────────────────────────────────────────┐
│                   一致性控制器                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  角色音色特质档案                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 角色ID: char_zhangsan                                │   │
│  │ 基准音色ID: voice_001                                │   │
│  │ 基准语速: 1.0                                        │   │
│  │ 基准音调: 中性                                       │   │
│  │ 特质锚点:                                            │   │
│  │   - 句尾: 微下沉                                     │   │
│  │   - 强调词: 力度增强                                 │   │
│  │ 历史片段样本: [frag_001, frag_005, frag_012]        │   │
│  │ 一致性得分: 0.85                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  一致性约束算法:                                            │
│  1. 情绪偏移量 = 当前情绪强度 × 情绪类型基准偏移表           │
│  2. 最终参数 = 基准参数 × (1 + 情绪偏移量) × 一致性权重      │
│  3. 一致性权重 = min(历史一致性得分, 0.9)                   │
│                                                             │
│  偏差检测机制:                                              │
│  合成后片段 vs 历史样本                                     │
│        ↓                                                    │
│  特征提取 (音调、语速、能量分布)                             │
│        ↓                                                    │
│  相似度计算                                                 │
│        ↓                                                    │
│  相似度 < 0.75 → 标记"一致性警告" → 加入人工确认队列         │
│  相似度 ≥ 0.75 → 更新历史样本库 → 继续处理                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2.4 情绪偏移表

```python
EMOTION_OFFSETS = {
    "愤怒": {"语速": 0.2, "音调": 0.15, "力度": 0.3},
    "悲伤": {"语速": -0.15, "音调": -0.1, "力度": -0.2},
    "喜悦": {"语速": 0.1, "音调": 0.1, "力度": 0.1},
    "恐惧": {"语速": -0.1, "音调": 0.05, "力度": -0.1},
    "平静": {"语速": 0.0, "音调": 0.0, "力度": 0.0},
    "紧张": {"语速": 0.15, "音调": 0.05, "力度": 0.1},
}
```

#### 1.2.5 音频特征提取

```python
# 使用librosa提取音频特征
def extract_voice_features(audio_path: str) -> dict:
    y, sr = librosa.load(audio_path)

    return {
        "pitch_mean": float(np.mean(librosa.yin(y, fmin=80, fmax=400))),
        "pitch_std": float(np.std(librosa.yin(y, fmin=80, fmax=400))),
        "energy_mean": float(np.mean(librosa.feature.rms(y=y))),
        "tempo": float(librosa.beat.tempo(y=y, sr=sr)[0]),
        "mfcc_mean": librosa.feature.mfcc(y=y, sr=sr).mean(axis=1).tolist(),
    }
```

#### 1.2.6 接口设计

```python
# src/audiobook/engines/consistency.py

@dataclass
class VoiceProfile:
    """角色音色特质档案"""
    character_id: str
    base_voice_id: str
    base_speed: float = 1.0
    base_pitch: str = "中性"
    feature_anchors: list[dict] = field(default_factory=list)
    history_samples: list[str] = field(default_factory=list)
    consistency_score: float = 1.0


class ConsistencyController:
    """一致性控制器"""

    def __init__(self, storage_path: str):
        self.profiles: dict[str, VoiceProfile] = {}

    def get_profile(self, character_id: str) -> VoiceProfile:
        """获取角色音色档案"""

    def update_profile(self, character_id: str, fragment: AudioFragment) -> None:
        """更新档案，添加新样本"""

    def calculate_adjusted_params(
        self,
        character_id: str,
        emotion: EmotionProfile
    ) -> SynthesisParams:
        """计算一致性约束后的合成参数"""

    def check_consistency(
        self,
        character_id: str,
        new_fragment: AudioFragment
    ) -> ConsistencyResult:
        """检查新片段与历史样本的一致性"""

    def get_reference_audio(self, character_id: str) -> Optional[str]:
        """获取角色的参考音频路径（用于GPT-SoVITS）"""
```

#### 1.2.7 测试用例

- `test_profile_creation`: 测试档案创建
- `test_profile_update`: 测试档案更新
- `test_emotion_offset_calculation`: 测试情绪偏移计算
- `test_consistency_check_high_score`: 测试高一致性片段
- `test_consistency_check_low_score`: 测试低一致性警告
- `test_reference_audio_selection`: 测试参考音频选择

---

## 二、Phase 3: 用户体验增强

### 2.1 预览播放器

#### 2.1.1 功能概述

允许用户在确认音色前预览效果，支持对比播放。

#### 2.1.2 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: 为角色"张三"选择音色                                 │
│        主角 · 已出场 23 次 · 性格: 沉稳内敛                   │
├─────────────────────────────────────────────────────────────┤
│ 候选音色                                                     │
│ ┌──────────────────┐ ┌──────────────────┐                  │
│ │ ○ voice_001      │ │ ○ voice_002      │                  │
│ │ 青年男声-温和     │ │ 青年男声-沉稳     │                  │
│ │ 匹配度: 92%      │ │ 匹配度: 87%      │                  │
│ │ [▶ 试听]         │ │ [▶ 试听]         │                  │
│ └──────────────────┘ └──────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│ 预览对比                                                     │
│ 原文: "我是张三，这件事我必须说清楚。"                        │
│                                                             │
│ voice_001: [▶ 播放] ████████░░░░ 00:03 / 00:05            │
│ voice_002: [▶ 播放]                                         │
├─────────────────────────────────────────────────────────────┤
│ [确认选择] [重新匹配] [手动选择]                              │
└─────────────────────────────────────────────────────────────┘
```

#### 2.1.3 技术实现

```python
# src/audiobook/preview/player.py

class PreviewPlayer:
    """预览播放器"""

    def __init__(self, tts_endpoint: str):
        self.synthesis = VoiceSynthesisEngine(endpoint=tts_endpoint)

    def generate_preview(
        self,
        voice: Voice,
        text: str,
        emotion: Optional[EmotionProfile] = None
    ) -> bytes:
        """生成预览音频"""

    def generate_comparison(
        self,
        voices: list[Voice],
        text: str,
        emotion: Optional[EmotionProfile] = None
    ) -> dict[str, bytes]:
        """生成多个音色的对比音频"""
```

#### 2.1.4 Web界面API

```python
# FastAPI/Flask端点

@app.post("/api/preview/generate")
async def generate_preview(request: PreviewRequest):
    """生成单个音色预览"""
    return {"audio_url": "/static/preview/xxx.wav"}

@app.post("/api/preview/compare")
async def compare_previews(request: CompareRequest):
    """生成多个音色对比预览"""
    return {
        "previews": [
            {"voice_id": "voice_001", "audio_url": "/static/preview/001.wav"},
            {"voice_id": "voice_002", "audio_url": "/static/preview/002.wav"},
        ]
    }
```

---

### 2.2 进度仪表盘

#### 2.2.1 功能概述

实时显示转换进度，包括已处理片段、失败片段、预计剩余时间。

#### 2.2.2 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│ 《示例小说》转换进度                                         │
│ 开始时间: 14:30 | 任务ID: job_20260329_143000              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│           ████████████████░░░░░░░░░░░░░                     │
│                        45%                                  │
│                                                             │
│         第 23 章 / 共 50 章                                 │
├─────────────────────────────────────────────────────────────┤
│ 已完成     │ 进行中     │ 待处理     │ 失败                 │
│ 1,125     │ 1          │ 1,374      │ 2                    │
│ 片段       │ 片段       │ 片段       │ 片段                 │
├─────────────────────────────────────────────────────────────┤
│ 已用时: 1小时30分 | 预计剩余: 1小时50分                      │
│ 处理速度: ~12.5 片段/分钟                                   │
├─────────────────────────────────────────────────────────────┤
│ 当前: 语音合成 - 第23章                                     │
│ 角色: 李四 | 情绪: 悲伤-中度                                │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2.3 数据结构

```python
@dataclass
class ProgressInfo:
    """进度信息"""
    job_id: str
    novel_name: str
    total_chapters: int
    current_chapter: int
    total_fragments: int
    processed_fragments: int
    failed_fragments: int
    start_time: datetime
    elapsed_seconds: int
    estimated_remaining_seconds: int
    current_stage: str          # "角色识别" | "音色匹配" | "语音合成" | "混音"
    current_character: str
    current_emotion: str
    processing_speed: float     # 片段/分钟

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "percent": round(self.processed_fragments / self.total_fragments * 100, 1),
            "progress_bar": self._generate_progress_bar(),
            "stats": {
                "completed": self.processed_fragments,
                "pending": self.total_fragments - self.processed_fragments,
                "failed": self.failed_fragments,
            },
            "time": {
                "elapsed": self._format_time(self.elapsed_seconds),
                "remaining": self._format_time(self.estimated_remaining_seconds),
            },
            "current": {
                "chapter": f"第 {self.current_chapter} 章 / 共 {self.total_chapters} 章",
                "stage": self.current_stage,
                "character": self.current_character,
                "emotion": self.current_emotion,
            }
        }
```

#### 2.2.4 SSE实时推送

```python
# FastAPI SSE端点

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

@app.get("/api/progress/{job_id}/stream")
async def progress_stream(job_id: str):
    """SSE实时推送进度"""
    async def event_generator():
        while True:
            progress = get_progress(job_id)
            yield f"data: {json.dumps(progress.to_dict())}\n\n"

            if progress.processed_fragments >= progress.total_fragments:
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

### 2.3 异常定位报告

#### 2.3.1 功能概述

处理完成后，生成异常报告，支持原文定位，方便用户修复问题。

#### 2.3.2 报告结构

```python
@dataclass
class ExceptionReport:
    """异常报告"""
    report_id: str
    job_id: str
    generated_at: datetime
    summary: dict                  # {"total": 2500, "failed": 3, "success_rate": "99.88%"}
    exceptions: list[FragmentException]


@dataclass
class FragmentException:
    """片段异常"""
    fragment_id: str
    chapter: int
    paragraph: int
    sentence: int
    original_text: str
    original_location: str         # "第5章第3段第2句"
    error_type: str                # "ConsistencyCheckError" | "SynthesisError" | "VoiceMatchError"
    error_message: str
    suggested_action: str          # "重新合成" | "手动确认音色" | "检查原文"
    audio_preview_url: Optional[str]
```

#### 2.3.3 界面设计

```
┌─────────────────────────────────────────────────────────────┐
│ 处理异常报告                                                 │
│ 成功率: 99.88% | 失败片段: 3 / 2,500                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ #1 [一致性警告] frag_0123                                   │
│    章节: 5 | 位置: 第3段第2句                                │
│    原文: "张三愤怒地拍桌而起..."                             │
│    问题: 一致性得分 0.72 < 阈值 0.75                         │
│    [查看原文 →] [重新合成] [标记忽略]                        │
│                                                             │
│ #2 [合成失败] frag_0456                                     │
│    章节: 12 | 位置: 第8段                                    │
│    原文: "..."                                              │
│    问题: GPT-SoVITS 返回损坏音频                            │
│    [查看原文 →] [重新合成] [标记忽略]                        │
│                                                             │
│ #3 [音色匹配失败] frag_0789                                 │
│    章节: 18 | 位置: 第2段                                    │
│    原文: "..."                                              │
│    问题: 无匹配候选，已使用默认音色                          │
│    [查看原文 →] [重新匹配] [标记忽略]                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [全部重新合成] [全部忽略] [导出报告]                         │
└─────────────────────────────────────────────────────────────┘
```

#### 2.3.4 原文定位

```python
class OriginalTextLocator:
    """原文定位器"""

    def locate(
        self,
        novel_path: str,
        chapter: int,
        paragraph: int,
        sentence: int
    ) -> TextLocation:
        """定位原文位置"""

    def highlight(
        self,
        location: TextLocation,
        context_lines: int = 3
    ) -> str:
        """生成高亮显示的上下文"""
        # 返回带高亮的文本，如:
        # 第5章
        # ...
        # 第2段：
        # 周围一片寂静。
        # >>> 张三愤怒地拍桌而起，声音回荡在空旷的大厅里。 <<<
        # 他死死盯着眼前的人。
        # ...
```

---

### 2.4 角色关系可视化

#### 2.4.1 功能概述

以关系图形式展示角色之间的关系，辅助用户理解角色网络。

#### 2.4.2 数据结构

```python
@dataclass
class CharacterRelation:
    """角色关系"""
    character1: str
    character2: str
    relation_type: str        # "敌对" | "信任" | "爱慕" | "亲情" | "朋友"
    strength: float           # 0.0-1.0 关系强度
    first_encounter: str      # 首次互动章节


class CharacterGraph:
    """角色关系图"""

    def __init__(self):
        self.nodes: list[CharacterNode] = []
        self.edges: list[CharacterRelation] = []

    def add_relation(self, relation: CharacterRelation) -> None:
        """添加关系"""

    def to_cytoscape(self) -> dict:
        """转换为Cytoscape.js格式，用于前端渲染"""
        return {
            "nodes": [
                {"data": {"id": c.name, "label": c.name, "importance": c.importance.value}}
                for c in self.nodes
            ],
            "edges": [
                {"data": {"source": e.character1, "target": e.character2, "label": e.relation_type}}
                for e in self.edges
            ]
        }
```

#### 2.4.3 关系提取

```python
class RelationExtractor:
    """关系提取器"""

    RELATION_PATTERNS = {
        "敌对": ["敌人", "仇人", "死对头", "敌意"],
        "信任": ["信任", "相信", "依赖", "托付"],
        "爱慕": ["喜欢", "爱", "心动", "暗恋"],
        "亲情": ["父亲", "母亲", "兄弟", "姐妹", "亲人"],
        "朋友": ["朋友", "好友", "知己", "发小"],
    }

    def extract_from_text(self, text: str, characters: list[str]) -> list[CharacterRelation]:
        """从文本中提取角色关系"""
```

---

## 三、实际测试方案

### 3.1 测试环境准备

#### 3.1.1 GPT-SoVITS部署

**方式一：本地部署（推荐开发测试）**

```bash
# 1. 克隆仓库
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS

# 2. 创建Conda环境
conda create -n GPTSoVits python=3.9
conda activate GPTSoVits

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载预训练模型
# 从 https://huggingface.co/lj1995/GPT-SoVITS 下载模型到 GPT_SoVITS/pretrained_models

# 5. 启动API服务
python api_v2.py -a 127.0.0.1 -p 9880 -dr True
```

**方式二：Docker部署**

```bash
docker run -d --name gpt-sovits \
  -p 9880:9880 \
  -v /path/to/models:/app/models \
  breakstring/gpt-sovits:latest
```

#### 3.1.2 测试音色准备

```bash
# 创建测试音色库
mkdir -p ~/.audiobook-converter/voices

# 准备参考音频（建议5-15秒，清晰无背景音）
# 从公开数据集获取或自行录制
```

**参考音频要求**:
- 格式: WAV (16kHz或44.1kHz)
- 时长: 5-15秒
- 内容: 自然说话片段
- 质量: 无背景噪音、无混响

### 3.2 集成测试用例

#### 3.2.1 端到端转换测试

```python
# tests/e2e/test_real_synthesis.py

import pytest
from pathlib import Path
from audiobook.processors import AudiobookPipeline
from audiobook.storage import VoiceLibrary

@pytest.mark.skipif(not os.environ.get("RUN_REAL_TTS"), reason="需要真实TTS服务")
class TestRealSynthesis:
    """真实TTS服务集成测试"""

    @pytest.fixture
    def pipeline(self, tmp_path):
        library = VoiceLibrary(path=str(tmp_path / "voices"))
        # 添加测试音色
        library.add(Voice(
            voice_id="test_male",
            name="测试男声",
            gender="男",
            age_range="青年",
            audio_path="tests/fixtures/reference_male.wav"
        ))
        return AudiobookPipeline(
            voice_library=library,
            tts_endpoint="http://localhost:9880"
        )

    def test_short_novel_conversion(self, pipeline, tmp_path):
        """测试短篇转换"""
        # 准备测试小说
        novel_path = tmp_path / "test.txt"
        novel_path.write_text('"你好，我是张三。"张三说道。')

        # 执行转换
        result = pipeline.convert(
            novel_path=str(novel_path),
            output_path=str(tmp_path / "output.wav")
        )

        # 验证
        assert result["status"] == "completed"
        assert (tmp_path / "output.wav").exists()

    def test_character_voice_consistency(self, pipeline):
        """测试同一角色语音一致性"""
        # 多次合成同一角色的不同文本
        # 验证音色特征相似度
```

#### 3.2.2 性能测试

```python
# tests/performance/test_synthesis_speed.py

class TestSynthesisPerformance:
    """合成性能测试"""

    def test_single_fragment_latency(self, synthesis_engine):
        """单片段合成延迟"""
        import time

        start = time.time()
        result = synthesis_engine.synthesize(
            prompt="测试提示词",
            text="这是一段测试文本，用于测量合成延迟。",
            voice_id="test_voice",
            reference_audio="tests/fixtures/ref.wav"
        )
        latency = time.time() - start

        # 合成100字应在30秒内完成
        assert latency < 30.0

    def test_throughput(self, pipeline, sample_novel):
        """吞吐量测试"""
        # 测试每分钟处理的片段数
```

### 3.3 手动测试清单

#### 3.3.1 CLI功能测试

```bash
# 1. 初始化
uv run audiobook init
# ✓ 验证：目录创建成功

# 2. 添加音色
uv run audiobook voice add reference.wav -n "青年男声" -g 男 -a 青年 -t 温和 -t 主角
# ✓ 验证：音色添加成功，可列出

# 3. 列出音色
uv run audiobook voice list
# ✓ 验证：显示刚添加的音色

# 4. 转换小说
uv run audiobook convert novel.txt -o output.wav
# ✓ 验证：转换完成，输出文件存在

# 5. 播放验证
# 使用音频播放器验证：
# - 语音清晰度
# - 情绪表达
# - 角色音色区分度
# - 音效融合（Phase 2）
```

#### 3.3.2 质量验证清单

| 测试项 | 验证内容 | 预期结果 |
|-------|---------|---------|
| 角色识别 | 主要角色是否正确识别 | 主角≥90%准确率 |
| 情绪识别 | 情绪类型和强度 | 与人工判断一致≥80% |
| 音色匹配 | 角色与音色契合度 | 用户满意度≥7/10 |
| 语音合成 | 音频质量 | 无明显杂音、断断续续 |
| 一致性 | 同一角色声音稳定性 | 相似度≥0.85 |
| 音效融合 | 背景/环境音融合 | 自然、不突兀 |
| 处理速度 | 单章处理时间 | <5分钟 |

### 3.4 测试数据集

#### 3.4.1 测试小说样本

```
tests/fixtures/novels/
├── short_dialogue.txt        # 纯对话测试
├── short_narration.txt      # 纯旁白测试
├── multi_character.txt      # 多角色测试（5+角色）
├── emotional_scenes.txt     # 情绪场景测试
├── long_chapter.txt         # 长章节测试（5000+字）
└── encoding_gbk.txt         # GBK编码测试
```

#### 3.4.2 测试音频样本

```
tests/fixtures/audio/
├── reference_male_01.wav    # 男声参考音频
├── reference_female_01.wav  # 女声参考音频
├── reference_narrator.wav   # 旁白参考音频
└── ambient_rain.wav         # 环境音测试样本
```

---

## 四、开发优先级

### Phase 2 优先级

| 功能 | 优先级 | 预计工作量 | 依赖 |
|------|--------|-----------|------|
| 一致性控制器 | P0 | M | Phase 1 |
| 场景识别 | P1 | S | Phase 1 |
| 音效库存储 | P1 | S | 无 |
| 音效匹配 | P1 | M | 场景识别、音效库 |
| 混音处理器 | P1 | M | 音效匹配 |

**推荐顺序**: 一致性控制器 → 场景识别 → 音效库存储 → 音效匹配 → 混音处理器

### Phase 3 优先级

| 功能 | 优先级 | 预计工作量 | 依赖 |
|------|--------|-----------|------|
| 进度仪表盘 | P0 | S | Phase 1 |
| 异常报告 | P0 | M | Phase 1 |
| 预览播放器 | P1 | M | Phase 1, 一致性控制器 |
| Web界面 | P1 | L | 所有Phase 2功能 |
| 角色关系图 | P2 | M | Phase 1 |

**推荐顺序**: 进度仪表盘 → 异常报告 → 预览播放器 → Web界面 → 角色关系图

---

## 五、风险与缓解

### 5.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| GPT-SoVITS服务不稳定 | 合成失败、延迟高 | 重试机制、本地缓存、服务健康检查 |
| 音色一致性难以保证 | 用户体验差 | 一致性控制器 + 人工确认机制 |
| 长篇小说处理时间过长 | 用户等待不耐烦 | 进度反馈 + 断点续传 |
| 情绪识别准确率低 | 音色匹配错误 | 多轮验证 + 用户反馈修正 |

### 5.2 性能优化方向

1. **并行合成**: 多个片段并行提交给GPT-SoVITS
2. **批量处理**: 合并短片段减少API调用
3. **缓存复用**: 相同文本+音色的缓存命中
4. **预加载**: 提前加载下一章节的音效资源

---

## 六、时间估算

| 阶段 | 功能模块 | 预计时间 |
|------|---------|---------|
| **Phase 2** | | **2-3周** |
| | 一致性控制器 | 3-4天 |
| | 场景音效引擎 | 4-5天 |
| | 集成测试 | 2天 |
| **Phase 3** | | **2-3周** |
| | 进度仪表盘 | 2天 |
| | 异常报告 | 2天 |
| | 预览播放器 | 3天 |
| | Web界面 | 5-7天 |
| **实际测试** | | **1周** |
| | GPT-SoVITS集成 | 2天 |
| | 真实数据测试 | 3天 |
| | 性能调优 | 2天 |

**总计**: 5-7周（不含并行开发优化）

---

*文档版本: 1.0*
*创建日期: 2026-03-29*
*适用项目: Audiobook Converter MVP*