# 智能有声书转换软件设计文档

> CEO Review: 2026-03-29 | Mode: SCOPE EXPANSION | Status: REVIEWED & ENHANCED

## 一、产品概述

### 1.1 产品定位

将小说转换为有声书的智能软件，核心差异化：**角色音色动态匹配 + 情绪化语音演绎 + 场景音效自动匹配 ★**

- **痛点解决**：现有有声书转换软件使用单一音色阅读全文，男女老少同音，缺乏代入感
- **目标效果**：像专业配音演员演播，旁白有旁白风格，每个角色根据性格特征与情绪状态选择合适音色，场景自动匹配背景音乐和环境音效

### 1.2 演进路径

```
个人使用验证 → 工具化服务创作者 → 平台化服务市场
```

**架构原则**：核心层抽象接口预留扩展点，避免每次迭代重构

---

## 二、技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           用户交互层                                          │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ CLI 工具     │ Web界面      │ 预览播放器★  │ 进度仪表盘★  │ 异常定位报告★   │
│ ·参数配置    │ ·音色库管理  │ ·片段预览    │ ·实时进度    │ ·原文高亮链接   │
│ ·命令执行    │ ·音色确认    │ ·对比播放    │ ·剩余时间    │ ·标记汇总       │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
                              ↓ ↑ (双向交互)
┌─────────────────────────────────────────────────────────────────────────────┐
│                           核心引擎层                                          │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┤
│ 小说解析引擎  │ 角色识别引擎  │ 音色匹配引擎  │ 语音合成引擎  │ 场景音效引擎★   │
│ ·分块策略    │ ·状态追踪    │ ·三层筛选    │ ·提示词生成   │ ·场景识别★      │
│ ·边界识别    │ ·情绪识别    │ ·语义搜索★   │ ·GPT-SoVITS  │ ·音效匹配★      │
│ ·角色名扫描  │ ·关系图谱★   │ ·预览对比★   │ ·一致性控制★ │ ·背景混音★      │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           数据存储层                                          │
├──────────────────┬──────────────────┬──────────────────┬───────────────────┤
│ 音色库            │ 音效库★          │ 处理状态         │ 输出缓存          │
│ ·音频文件        │ ·环境音效★       │ ·进度追踪器★     │ ·音频片段        │
│ ·SQLite元数据    │ ·音乐素材★       │ ·异常标记★       │ ·完整有声书      │
│ ·语义嵌入向量    │ ·场景匹配规则★   │ ·角色状态对象    │ ·预览缓存★       │
└──────────────────┴──────────────────┴──────────────────┴───────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           语音引擎层                                          │
│  GPT-SoVITS API → 一致性控制器★ → 音色特质参数化 → 情绪提示词模板            │
│  扩展接口预留: 云服务模型部署                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           音频合成层                                          │
│  语音合成 → 场景音效叠加★ → 片段缓存 → 实时预览★ → 拼接输出 → 有声书文件     │
│  功能: 边处理边合成 / 缓存片段 / 支持局部替换 / 进度追踪★ / 预览播放★         │
└─────────────────────────────────────────────────────────────────────────────┘

★ = CEO Review 扩展功能
```

### 2.2 模块职责说明

| 模块 | 职责 | 关键功能 |
|-----|------|---------|
| **小说解析引擎** | 文本预处理与分块 | 代码扫描角色名、场景边界识别、分块策略 |
| **角色识别引擎** | 识别角色及其状态 | 角色是谁、复合情绪+强度、状态追踪传递、角色关系图谱★ |
| **音色匹配引擎** | 匹配合适音色 | 三层筛选流程、置信度计算、主角配角分层处理、语义搜索★、预览对比★ |
| **语音合成引擎** | 生成情绪化语音 | 提示词模板生成、调用GPT-SoVITS、异常重试、一致性控制★ |
| **场景音效引擎★** | 场景音效匹配 | 场景识别、音效匹配、背景混音 |
| **音频合成层** | 输出完整有声书 | 片段缓存、拼接合成、局部替换接口、进度追踪★、预览播放★ |

### 2.3 模块依赖关系图

```
┌─────────────────┐
│   小说解析引擎   │ ───────────────────────────────────┐
└────────┬────────┘                                    │
         │ 分块边界                                    │
         ▼                                             │
┌─────────────────┐    角色状态    ┌─────────────────┐  │
│   角色识别引擎   │ ────────────▶ │   状态传递机制   │  │
└────────┬────────┘               └────────┬────────┘  │
         │ 情绪识别                         │           │
         │ 角色关系                         ▼           │
         ▼                        ┌─────────────────┐  │
┌─────────────────┐               │ 一致性控制器★   │  │
│ 场景音效引擎★   │ ◀─────────────│ 音色特质档案   │  │
└────────┬────────┘               └────────┬────────┘  │
         │ 场景识别/音效参数               │           │
         │                                    │ 候选音色
         ▼                                    ▼           │
┌─────────────────┐               ┌─────────────────┐  │
│   音效库★       │               │   音色匹配引擎   │ ◀─┘
└─────────────────┘               └────────┬────────┘
                                             │ 确认音色
                                             ▼
                                    ┌─────────────────┐
                                    │   音色库        │
                                    └─────────────────┘
                                             │
                                             ▼
┌─────────────────┐               ┌─────────────────┐
│   预览播放器★   │ ◀─────────────│   语音合成引擎   │
└────────┬────────┘               └────────┬────────┘
         │ 播放请求                        │ 语音片段
         ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐
│   进度追踪器★   │ ◀─────────────│   音频合成层     │
└────────┬────────┘               └────────┬────────┘
         │ 进度/状态                       │ 合成输出
         ▼                                 ▼
┌─────────────────┐               ┌─────────────────┐
│   进度仪表盘★   │               │   输出缓存       │
└─────────────────┘               └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │ 异常定位报告★   │
                                    └─────────────────┘
```

---

## 三、完整处理流程

### 3.1 流程总览

```
预处理 → 渐进披露分析 → 语音合成 → 合成输出
```

### 3.2 预处理阶段

```
上传小说 → 代码扫描角色名 → AI抽样验证 → TF-IDF计算重要度 → 角色分层
                              ↓
                    用户查看角色列表，了解工作量
```

**角色名扫描**：
- 代码规则匹配："张三说"、"李四道"、"王五问"等对话标记
- 提取角色名列表，秒级完成

**AI抽样验证**：
- 随机抽取N处提及（如10处）
- AI验证角色非虚构/误识别
- 确认角色真实存在且重要

**TF-IDF重要度计算**：
- 计算每个角色出场频率
- 自动划分主角/配角阈值
- 输出角色重要度排名列表

### 3.3 渐进披露分析阶段

```
代码标记分块边界 → AI验证边界 → 确定场景分块
                              ↓
                    按场景分块渐进处理
```

**场景分块策略**：

第一层：代码粗分割
- 章节边界：识别"第X章"、标题格式
- 段落边界：空行、换行符
- 时间词标记："第二天"、"三个月后"、"傍晚时分"
- 地点词标记："来到了"、"回到"、"走进"
- 对话切换：连续对话段落 vs 描写段落

第二层：AI边界验证
- 对代码识别的"疑似边界点"逐个验证
- 判断是否是真正的场景转换
- 最终确定分块位置

**分块处理流程**：

```
每个场景分块:
  ├── 角色识别: 谁在说话/心理活动
  ├── 情绪识别: 复合情绪 + 强度分级
  ├── 角色状态更新: 结构化对象 + 关键对话摘要传递
  └── 音色匹配:
      ├── 主角: 三层筛选 → 人工确认
      └── 配角: 三层筛选 → 自动选择最高置信度
```

### 3.4 角色状态传递机制

**混合方案：结构化状态对象 + 最近N块角色关键对话摘要**

**角色状态结构**：
```json
{
  "角色名": "张三",
  "基础音色ID": "voice_001",
  "当前情绪": {
    "类型": "愤怒+隐忍",
    "强度": "中度"
  },
  "关键关系": ["李四-敌对", "王五-信任"],
  "重要经历摘要": ["第三章被背叛", "第五章得知真相"],
  "最近对话摘要": "最近N块中该角色的关键对话内容",
  "音色首次确认": true,
  "历史情绪记录": ["平静", "激动-强烈", "悲伤-中度"],
  "基准音色参数★": {
    "音色ID": "voice_001",
    "基准语速": 1.0,
    "基准音调": "中性",
    "特质锚点": [
      {"位置": "句尾", "特征": "微下沉"},
      {"位置": "强调词", "特征": "力度增强"}
    ]
  },
  "历史片段样本★": ["片段1_hash", "片段2_hash"],
  "一致性得分★": 0.85
}
```

**传递流程**：
- 每处理完一块，更新所有出场角色的状态对象
- 下块处理时，加载相关角色的状态对象作为上下文
- 主角状态完整传递，配角状态简化传递

### 3.5 语音合成阶段

```
基础音色 → 情绪提示词模板+参数化调整 → GPT-SoVITS合成
                              ↓
                    音频片段缓存 → 实时进度反馈
```

**提示词生成流程**：
```
识别结果(角色+复合情绪+强度)
        ↓
情绪提示词模板框架
  · 基础模板: {音色ID} + {情绪类型}
  · 参数化调整: {强度参数} + {语速参数} + {语气细节}
        ↓
AI根据场景上下文填充参数值
        ↓
具体提示词 → GPT-SoVITS
        ↓
情绪化语音输出
```

**异常处理**：
- 合成失败重试3次
- 降级到备用音色
- 标记待人工处理片段

### 3.6 合成输出阶段

```
音频片段拼接 → 完整有声书输出 → 异常汇总报告
                              ↓
                    用户处理待确认片段
```

**分层缓存合成**：
- 每块合成后缓存音频片段
- 支持局部片段替换修改
- 批量替换某角色所有片段接口
- 实时进度反馈

---

## 四、音色库设计

### 4.1 音色库架构

**存储方案**：
- 音色音频文件：本地目录存储，方便备份迁移
- 元数据索引：SQLite数据库，支持快速查询和倒排索引
- 管理工具：CLI/Web工具，增删改查、标签编辑、批量导入

### 4.2 音色标签体系

**分层设计**：

| 层级 | 维度 | 内容 | 示例 |
|-----|------|------|------|
| **标签初筛层** | 基础属性 | 性别、年龄段、声音类型 | 男、青年、柔和 |
| | 场景适配 | 旁白/角色、正派/反派 | 适合反派角色 |
| **语义匹配层** | 声音特质描述 | 自然语言画像 | "声音温润有磁性，说话节奏舒缓，尾音微微下沉带一点慵懒感" |
| | 情感表达范围 | 不同情绪下的变化特征 | 平静/激动/悲伤/愤怒的表现方式 |
| | 角色形象关联 | 音色与角色气质映射 | "适合阅历丰富的长辈角色，说话有种看透世事的感觉" |
| **行为样本层** | 标注音频片段 | 不同情绪状态的实际表现 | 平静段落、激动段落、悲伤段落的参考音频 |

### 4.3 音色匹配流程

```
角色描述(含情绪状态)
        ↓
【第一层】标签初筛
  · 基础属性倒排索引快速过滤
  · 缩小候选集范围
        ↓
【第二层】语义匹配
  · 角色画像 vs 音色描述 → 语义相似度计算
  · 情感表达范围 vs 角色当前情绪 → 契合度计算
        ↓
【第三层】行为样本匹配
  · 对比候选音色的参考音频片段
  · 精确验证匹配度
        ↓
置信度得分排序
        ↓
主角: 用户确认 (支持预览对比★)
配角: 自动选最高置信度
```

---

## 五、情绪识别设计

### 5.1 情绪识别粒度

**组合方案：复合情绪 + 强度分级**

**复合情绪示例**：
- 悲伤中带一丝希望
- 愤怒下的隐忍
- 表面平静内心波澜
- 喜悦中夹杂不安

**强度分级**：
- 轻度：微弱情绪波动，语气略有变化
- 中度：明显情绪状态，声音特征显著
- 强烈：强烈情绪爆发，声音张力最大

### 5.2 情绪识别输出

```json
{
  "角色": "张三",
  "情绪类型": "愤怒+隐忍",
  "情绪强度": "中度",
  "场景上下文": "被好友背叛，但需要保持冷静",
  "建议音色调整": "压抑的愤怒表达，语速略慢，语气带压抑感"
}
```

---

## 六、异常处理策略

### 6.1 处理原则

| 异常类型 | 处理策略 | 具体操作 |
|---------|---------|---------|
| **语音合成失败** | 重试 → 降级 → 标记 | 重试3次，失败后降级备用音色，标记待人工处理 |
| **角色识别低置信度** | 标记 → 汇总确认 | 标记疑问片段，流程结束后汇总用户确认 |
| **音色匹配无候选** | 提示 → 降级选择 | 提示用户补充音色库，或自动选最接近音色 |
| **小说格式不规范** | 尽力解析 → 提示 | 尽力解析，提示用户预处理建议 |

### 6.2 异常处理流程

```
异常发生 → 分类判断
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
可恢复异常           致命异常
    ↓                   ↓
标记+继续            报错+暂停
    ↓                   ↓
流程结束汇总        用户决策后继续
```

### 6.3 完整错误处理矩阵 ★

| 方法/代码路径 | 可能失败的场景 | 异常类型 | 捕获? | 救援操作 | 用户可见消息 |
|--------------|---------------|---------|------|---------|-------------|
| 小说解析引擎#分块 | 文件编码错误 | EncodingError | Y | 尝试UTF-8/GBK/GB18030解码 | "检测文件编码..." |
| | 文件不存在 | FileNotFoundError | Y | 提示用户检查路径 | "文件不存在: {path}" |
| | 文件为空 | EmptyFileError | Y | 报错退出 | "文件为空，请检查文件内容" |
| 角色识别引擎#识别 | LLM API 超时 | LLMTimeoutError | Y | 重试3次，间隔递增 | "AI分析超时，重试中..." |
| | 角色识别低置信度 | LowConfidenceError | Y | 标记待确认，继续处理 | "角色识别需确认" |
| | 零角色识别 | ZeroCharacterError | Y | 提示用户选择处理方式 | "未识别到角色，作为旁白处理?" |
| 音色匹配引擎#匹配 | 音色库为空 | EmptyVoiceLibraryError | Y | 停止处理，提示导入音色 | "请先添加音色到音色库" |
| | 无匹配候选 | NoMatchError | Y | 降级到最接近音色 | "使用近似音色: {id}" |
| | 用户拒绝所有候选 | AllCandidatesRejectedError | Y | 提供重新匹配/手动选择选项 | "请选择: 重新匹配/手动选择/使用默认" |
| 语音合成引擎#合成 | GPT-SoVITS 服务不可用 | TTSServiceUnavailableError | Y | 重试3次，间隔递增 | "语音服务不可用，重试中..." |
| | 返回损坏音频 | CorruptedAudioError | Y | 完整性校验后重新合成 | "音频损坏，重新合成..." |
| | 一致性检查失败 | ConsistencyCheckError | Y | 标记一致性警告，继续处理 | "音色一致性异常，已标记" |
| 场景音效引擎#匹配★ | 音效库为空 | EmptySoundLibraryError | Y | 跳过音效叠加，仅语音输出 | "音效库为空，跳过背景音" |
| | 混音处理失败 | AudioMixingError | Y | 跳过混音，输出纯语音 | "混音失败，输出纯语音版本" |

---

## 七、安全设计 ★

### 7.1 输入验证规范

**文件路径验证**：
- 禁止字符: "..", "~", "|", "<", ">", ":", "*", "?", "\"
- 路径规范化: os.path.normpath() 后验证是否在允许目录内
- 绝对路径限制: 仅允许用户明确指定的输出目录

**文件类型验证**：
- 小说文件: 仅接受 .txt, .md, .epub (解压后验证)
- 音色文件: 检查音频文件头 (RIFF, ID3, OggS)
- 禁止双扩展名: "file.txt.exe" 等拒绝

**文件大小限制**：
- 小说文件: 最大 50MB
- 音色文件: 单文件最大 10MB
- 总音色库: 最大 1GB (可配置)

### 7.2 文件处理安全策略

**输出文件保护**：
- 存在检查: 输出前检查文件是否存在
- 覆盖确认: 文件存在时提示 "文件已存在，是否覆盖? (y/N)"
- 唯一命名: 默认使用 "{书名}_{时间戳}.wav" 格式

**临时文件处理**：
- 临时目录: 使用系统临时目录 (tempfile.mkdtemp)
- 清理机制: 处理完成后自动删除临时文件
- 异常清理: 程序异常退出时清理临时文件 (atexit 注册)

### 7.3 API 通信安全

**本地服务优先**：
- GPT-SoVITS: 优先使用本地部署 (localhost:9880)
- LLM: 优先使用本地模型 (Ollama/llama.cpp)

**远程 API 配置**：
- 强制 HTTPS: 所有远程 API 调用使用 HTTPS
- 证书验证: 启用 SSL 证书验证 (不跳过)
- 超时设置: 连接超时 10s，读取超时 60s

---

## 八、音色一致性控制器 ★

### 8.1 设计目标

确保同一角色在不同场景中保持声音特质连贯性，这是核心差异化的关键。

### 8.2 架构设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         音色一致性控制器                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 存储层: 角色音色特质档案                                                      │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ {                                                                       │ │
│ │   "角色名": "张三",                                                      │ │
│ │   "基准音色参数": {                                                       │ │
│ │     "音色ID": "voice_001",                                              │ │
│ │     "基准语速": 1.0,                                                     │ │
│ │     "基准音调": "中性",                                                  │ │
│ │     "特质锚点": [                                                        │ │
│ │       {"位置": "句尾", "特征": "微下沉"},                                │ │
│ │       {"位置": "强调词", "特征": "力度增强"}                             │ │
│ │     ]                                                                   │ │
│ │   },                                                                    │ │
│ │   "历史片段样本": ["片段1_hash", "片段2_hash"],                          │ │
│ │   "一致性得分": 0.85                                                     │ │
│ │ }                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│ 一致性约束算法:                                                              │
│ 1. 情绪偏移量 = 当前情绪强度 × 情绪类型基准偏移表                              │
│ 2. 最终参数 = 基准参数 × (1 + 情绪偏移量) × 一致性权重                         │
│ 3. 一致性权重 = min(历史一致性得分, 0.9)                                     │ │
│                                                                              │
│ 偏差检测机制:                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ 合成后片段 vs 历史样本                                                   │ │
│ │         ↓                                                               │ │
│ │ 特征提取 (音调、语速、能量分布)                                          │ │
│ │         ↓                                                               │ │
│ │ 相似度计算                                                               │ │
│ │         ↓                                                               │ │
│ │ 相似度 < 0.75 → 标记"一致性警告" → 加入人工确认队列                       │ │
│ │ 相似度 ≥ 0.75 → 更新历史样本库 → 继续处理                                │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 九、场景音效匹配引擎 ★

### 9.1 输入输出规范

**输入规范**：
```json
{
  "场景文本": "窗外大雨倾盆，张三独自坐在昏暗的房间里...",
  "场景位置": {"章节": 3, "段落": 15},
  "角色状态": [{"角色": "张三", "情绪": "悲伤-中度"}]
}
```

**场景识别输出**：
```json
{
  "场景类型": "室内-夜晚",
  "环境要素": ["大雨", "昏暗", "独处"],
  "氛围": "压抑-悲伤",
  "推荐音效": {
    "环境音": {"id": "rain_heavy_01", "volume": 0.3},
    "背景音乐": {"id": "melancholy_ambient_01", "volume": 0.15},
    "叠加时机": "语音开始前2秒淡入",
    "持续模式": "贯穿场景"
  }
}
```

### 9.2 混音参数规范

| 音频层 | 音量 | 淡入/淡出 | 动态调节 |
|--------|------|----------|---------|
| 语音层 | 1.0 (基准) | - | - |
| 环境音层 | 0.2-0.4 | 淡入2s, 淡出1s | 情绪高潮时-0.1 |
| 背景音乐 | 0.1-0.2 | 淡入3s | 情绪高潮时+0.05 |
| 对话片段 | 环境音-0.15 | - | 避免干扰对话 |

### 9.3 音效库结构

```
/音效库/
  /环境音/
    /天气/ (雨声/风声/雷声...)
    /场所/ (室内/街道/森林...)
  /背景音乐/
    /情绪类/ (悲伤/紧张/欢快...)
    /场景类/ (战斗/日常/回忆...)
  元数据索引: SQLite (场景类型→音效ID映射表)
```

---

## 十、音频完整性校验 ★

### 10.1 校验时机

GPT-SoVITS 返回音频后、缓存存储前

### 10.2 校验流程

```
1. 文件头检查
   - 格式验证: WAV/MP3/OGG 魔数
   - 不匹配 → raise CorruptedAudioError("invalid_format")

2. 时长检查
   - 预期时长: 输入文本长度 × 平均语速系数 (约 0.8-1.2秒/字)
   - 实际时长: 从音频元数据提取
   - 偏差 > 50% → raise CorruptedAudioError("duration_mismatch")

3. 采样率/声道检查
   - 采样率: 16000/22050/44100 Hz (允许范围)
   - 声道: 单声道/立体声
   - 异常 → raise CorruptedAudioError("invalid_audio_params")

4. 波形静默检查
   - 全静默 (能量 < 阈值) → raise CorruptedAudioError("silent_audio")
   - 截断静默 > 30% → 警告日志，继续处理
```

### 10.3 损坏音频处理流程

```
CorruptedAudioError 捕获
        ↓
重试计数 < 3?
   ├── YES → 重新合成 (增加随机种子)
   └── NO  → 标记片段为 "待人工处理"
                ↓
           记录到异常报告:
           {片段ID, 原文位置, 错误类型, 预览链接}
                ↓
           继续处理下一片段
```

---

## 十一、阴影路径处理策略 ★

### 11.1 空文件输入处理

```
检测时机: 小说解析引擎初始化时
处理策略:
  if 文件大小 == 0:
    raise EmptyFileError("文件为空，请检查文件内容")
    exit(1)
用户消息: "错误: 输入文件为空，请检查文件路径和内容"
```

### 11.2 零角色识别处理 (纯旁白文本)

```
检测时机: 角色识别引擎完成扫描后
处理策略:
  if len(角色列表) == 0:
    提示用户: "未识别到对话角色，检测为纯旁白文本"
    选项:
      A) 继续处理 (使用旁白音色全程朗读)
      B) 退出 (取消处理)
用户消息: "未检测到角色对话。选择: [A] 作为纯旁白处理 [B] 取消"
默认行为: 用户不响应时默认选择 A
```

### 11.3 用户拒绝所有候选音色

```
检测时机: 主角音色确认阶段
处理策略:
  while True:
    候选 = 获取候选音色()
    用户选择 = 展示候选并等待确认()
    if 用户选择 == "全部拒绝":
      提供选项:
        A) 重新生成候选 (调整匹配参数)
        B) 手动选择音色 (打开音色库浏览)
        C) 使用默认音色 (警告可能影响体验)
      if 选择 C:
        确认提示: "使用默认音色可能导致角色声音与内容不匹配，确认？(y/N)"
        break
    else:
      break
用户消息: "所有候选被拒绝。请选择: [A] 重新匹配 [B] 手动选择 [C] 使用默认"
```

### 11.4 用户中断处理 (Ctrl+C)

```
检测时机: 全局信号处理
处理策略:
  signal(SIGINT, 优雅中断处理器)

  def 优雅中断处理器():
    print("\n检测到中断请求，正在保存进度...")
    保存当前状态到: .进度文件.json
    清理临时文件
    print("进度已保存。使用 --resume 参数继续处理")
    exit(0)

恢复机制:
  python audiobook.py --resume .进度文件.json
  # 从上次中断的位置继续处理
```

---

## 十二、测试策略 ★

### 12.1 测试金字塔

```
                  /\
                 /  \
                / E2E\          端到端测试: 5个核心流程
               /______\
              /        \
             / 集成测试 \       集成测试: 15个模块交互场景
            /____________\
           /              \
          /    单元测试    \     单元测试: 50+个函数/方法
         /__________________\
```

### 12.2 测试矩阵

| 模块 | 单元测试 | 集成测试 | E2E测试 | 测试优先级 |
|------|---------|---------|--------|-----------|
| 小说解析引擎 | 10+ | 3 | 1 | P1 - 核心入口 |
| 角色识别引擎 | 15+ | 5 | 1 | P1 - 核心差异化 |
| 音色匹配引擎 | 10+ | 3 | 1 | P1 - 核心差异化 |
| 语音合成引擎 | 8+ | 3 | 1 | P1 - 核心输出 |
| 场景音效引擎★ | 8+ | 2 | - | P2 - 扩展功能 |
| 一致性控制器★ | 5+ | 2 | - | P1 - 核心差异化 |
| 音色库管理 | 5+ | 2 | 1 | P2 - 支撑功能 |
| 进度追踪器★ | 5+ | 2 | - | P2 - 体验功能 |
| 预览播放器★ | 3+ | 2 | 1 | P2 - 体验功能 |
| 异常处理 | 10+ | 5 | 1 | P1 - 稳定性保障 |
| **总计** | **79+** | **29** | **7** | |

### 12.3 关键测试场景

**混沌测试**：
1. 随机删除音色库中的音色 → 验证降级处理
2. 随机中断 GPT-SoVITS 服务 → 验证重试和降级
3. 随机注入乱码文本 → 验证编码容错
4. 随机删除缓存片段 → 验证重新合成
5. 模拟内存不足 → 验证缓存清理

**边界测试**：
1. 空文件
2. 单字符文件
3. 最大文件 (50MB)
4. 超长章节 (>10000字)
5. 超多角色 (>50个)
6. 超多章节 (>1000章)

---

## 十三、性能优化策略 ★

### 13.1 性能瓶颈分析

| 处理阶段 | 瓶颈原因 | 预估耗时/章 |
|---------|---------|-----------|
| 小说解析 | 文件I/O | ~1秒 |
| 角色识别 (LLM调用) | API响应时间 | ~10-30秒 |
| 音色匹配 (语义嵌入) | 向量计算 | ~5秒 |
| **语音合成 (GPT-SoVITS)** | **模型推理 ★★★** | **~2-5分钟** |
| 场景音效匹配★ | 音效检索+加载 | ~5秒 |
| 混音处理★ | 音频处理 | ~10秒 |
| 音频拼接 | 文件I/O | ~5秒 |
| **总计 (每章)** | | **~3-6分钟** |
| **20万字小说 (~50章)** | | **~2.5-5小时** |

★★★ = 主要瓶颈 (占90%+时间)

### 13.2 优化策略

**语音合成并行化**：
- GPU批处理: 多个片段合并为batch提交GPT-SoVITS
- 多GPU并行: 不同GPU处理不同片段
- 多服务实例: 部署多个GPT-SoVITS实例，负载均衡
- 预期提升: 2-4x (取决于GPU数量)

**缓存优化**：
- L1: 内存缓存 (当前处理章节的角色状态、音色匹配结果)
- L2: 本地磁盘缓存 (已合成音频片段)
- L3: 音色预计算缓存 (音色+情绪组合的预设参数)

**内存管理**：
- 流式处理: 逐章加载处理，不一次性加载全部
- 及时释放: 合成完成的音频片段写入磁盘后释放内存
- 状态压缩: 角色状态仅保留最近N章摘要

### 13.3 性能指标目标

| 场景 | 目标 | 可接受范围 |
|------|------|-----------|
| 单章处理时间 | <3分钟 | 3-6分钟 |
| 20万字小说总处理时间 | <2小时 | 2-5小时 |
| 音色匹配响应时间 | <3秒 | 3-10秒 |
| 预览播放响应时间★ | <1秒 | 1-3秒 |
| 内存峰值 | <500MB | 500MB-1GB |

---

## 十四、可观测性设计 ★

### 14.1 日志系统

**日志级别**：
- DEBUG: 详细处理信息 (开发调试)
- INFO: 关键处理节点 (正常运维)
- WARNING: 可恢复异常 (需关注)
- ERROR: 严重错误 (需处理)

**结构化日志格式 (JSON)**：
```json
{
  "timestamp": "2026-03-29T14:30:00.123Z",
  "level": "INFO",
  "module": "voice_synthesis",
  "chapter": 3,
  "fragment": 15,
  "character": "张三",
  "emotion": "愤怒-中度",
  "voice_id": "voice_001",
  "duration_ms": 2345,
  "message": "语音合成完成"
}
```

### 14.2 进度追踪

**进度状态对象**：
```json
{
  "job_id": "job_20260329_143000",
  "novel_name": "示例小说",
  "total_chapters": 50,
  "current_chapter": 15,
  "total_fragments": 2500,
  "processed_fragments": 750,
  "failed_fragments": 3,
  "start_time": "2026-03-29T14:30:00Z",
  "elapsed_seconds": 3600,
  "estimated_remaining_seconds": 7200,
  "status": "processing",
  "current_stage": "语音合成"
}
```

**进度仪表盘输出**：
```
[████████████░░░░░░░░░░░░░░░░] 30%  第15章/共50章
当前: 语音合成 - 张三(愤怒-中度)
已处理: 750片段 | 失败: 3片段
已用时: 1小时0分 | 预计剩余: 2小时0分
```

### 14.3 异常报告

**异常报告结构**：
```json
{
  "report_time": "2026-03-29T15:30:00Z",
  "job_id": "job_20260329_143000",
  "summary": {
    "total_processed": 2497,
    "total_failed": 3,
    "success_rate": "99.88%"
  },
  "failed_fragments": [
    {
      "fragment_id": "frag_0123",
      "chapter": 5,
      "position": "第5章第3段",
      "original_text": "张三愤怒地拍桌而起...",
      "error_type": "CorruptedAudioError",
      "action_required": "需人工确认或重新合成",
      "original_location": "第5章第3段第2句"
    }
  ]
}
```

---

## 十五、部署策略 ★

### 15.1 系统要求

**最低配置**：
- 操作系统: Windows 10+, macOS 10.15+, Ubuntu 20.04+
- Python: 3.9 - 3.11
- 内存: 8GB RAM
- 磁盘: 10GB 可用空间 (含音色库)
- GPU: 可选 (无GPU可使用CPU，速度较慢)

**推荐配置**：
- 内存: 16GB+ RAM
- GPU: NVIDIA RTX 3060+ (6GB VRAM)
- 磁盘: SSD, 50GB+ 可用空间

### 15.2 安装方式

**方式一: pip 安装 (推荐)**
```bash
pip install audiobook-converter
audiobook --init  # 初始化配置
```

**方式二: 源码安装**
```bash
git clone https://github.com/xxx/audiobook-converter.git
cd audiobook-converter
pip install -e .
python -m audiobook --init
```

### 15.3 配置管理

**配置文件位置**：
- 全局配置: ~/.audiobook-converter/config.yaml
- 项目配置: ./.audiobook.yaml (优先级更高)

**配置结构**：
```yaml
tts:
  engine: "gpt-sovits"
  endpoint: "http://localhost:9880"
  timeout: 60
  retry: 3

llm:
  provider: "openai"
  model: "gpt-4"
  api_key: "${OPENAI_API_KEY}"

voice_library:
  path: "~/.audiobook-converter/voices"
  max_size_gb: 1

sound_library:
  path: "~/.audiobook-converter/sounds"
  enabled: true

output:
  format: "wav"
  sample_rate: 44100
  max_file_size_mb: 500

performance:
  parallel_synthesis: 1
  cache_size_mb: 500
  memory_limit_mb: 1000
```

---

## 十六、UI演进路径

### 16.1 MVP阶段（个人使用验证）

**命令行工具**：
```
$ audiobook convert novel.txt --output ./output

[████████████░░░░░░░░░░░░░░░░] 30%  第15章/共50章
当前: 语音合成 - 张三(愤怒-中度)
已处理: 750片段 | 失败: 3片段
已用时: 1小时0分 | 预计剩余: 2小时0分

[INFO] 第15章处理完成
[WARNING] 片段 frag_0123 一致性得分低 (0.72)
[INFO] 开始处理第16章...
```

**Web界面（音色库管理）**：
- 音色库增删改查
- 标签编辑界面
- 音色预览播放
- 批量导入导出
- 自然语言搜索★

### 16.2 工具化阶段

**扩展Web界面**：
- 处理进度可视化
- 角色列表展示
- 音色确认交互界面
- 异常片段处理界面
- 预览播放器★
- 进度仪表盘★
- 角色关系可视化★
- 音色预览对比★

### 16.3 平台化阶段

**桌面应用/Web平台**：
- 完整用户体验
- 多用户支持
- 任务队列管理
- 云端部署
- 音色克隆功能 (后续迭代)
- 协作音色确认

---

## 十七、技术选型

### 17.1 语音合成

- **当前**：本地GPT-SoVITS
- **扩展**：云服务器部署模型，保持API接口一致

### 17.2 AI模型选择

- **角色识别/情绪识别**：大语言模型（根据成本/能力选择）
- **语义匹配**：文本嵌入模型（语义相似度计算）

### 17.3 数据存储

- **音色库**：SQLite + 文件目录
- **处理状态**：内存/临时文件
- **输出缓存**：文件目录

---

## 十八、后续迭代方向

### 18.1 功能增强
- 音色克隆：用户上传参考音频克隆音色
- 多语言支持：扩展到其他语言小说
- 批量处理：多本小说队列处理

### 18.2 体验优化
- 预览功能：片段预览确认后再继续
- 实时调整：处理中调整音色选择
- 协作功能：多人协作音色确认

### 18.3 技术优化
- 性能优化：并行处理加速
- 模型优化：更精准的情绪识别
- 缓存优化：更高效的音频缓存管理

---

## 十九、MVP阶段划分 ★★

### 19.1 阶段划分

| 阶段 | 模块 | 范围 | 预计工作量 |
|------|------|------|-----------|
| **MVP Phase 1** | 小说解析引擎 | 文件读取、分块、角色名扫描 | M |
| | 角色识别引擎 | 角色识别、情绪识别、状态传递 | M |
| | 音色匹配引擎 | 三层筛选、置信度计算 | M |
| | 语音合成引擎 | 提示词生成、GPT-SoVITS调用、异常重试 | L |
| | 音色库管理 | SQLite存储、基本CRUD | S |
| **Phase 2** | 场景音效引擎★ | 场景识别、音效匹配、混音 | M |
| | 一致性控制器★ | 音色特质档案、偏差检测 | M |
| **Phase 3** | 预览播放器★ | 片段预览、对比播放 | S |
| | 进度追踪器★ | 实时进度、仪表盘 | S |
| | 异常定位报告★ | 原文高亮、链接报告 | S |
| | 角色关系可视化★ | 关系图谱 | S |

### 19.2 MVP Phase 1 验收标准

- 能够处理标准格式小说文件（.txt）
- 正确识别主要角色和情绪
- 自动匹配合适音色
- 生成完整有声书输出
- 处理时间满足性能指标

---

## 二十、核心引擎API接口定义 ★★

### 20.1 小说解析引擎接口

```python
class NovelParserEngine:
    """小说解析引擎 - 文本预处理与分块"""

    def parse_novel(file_path: str) -> ParseResult:
        """
        解析小说文件

        Args:
            file_path: 小说文件路径

        Returns:
            ParseResult: {
                "novel_id": str,           # 唯一标识
                "title": str,              # 小说标题
                "total_chapters": int,     # 总章节数
                "total_characters": int,   # 总字符数
                "blocks": [Block],         # 分块列表
                "character_names": [str],  # 角色名列表
                "encoding": str            # 文件编码
            }

        Raises:
            FileNotFoundError: 文件不存在
            EmptyFileError: 文件为空
            EncodingError: 编码无法识别
            UnsupportedFormatError: 不支持的文件格式
        """

    def split_into_blocks(text: str, config: SplitConfig) -> [Block]:
        """
        将文本分割成处理块

        Args:
            text: 原始文本
            config: 分割配置 {
                "chapter_pattern": str,    # 章节正则
                "paragraph_min_lines": int # 最小段落行数
            }

        Returns:
            [Block]: [{
                "block_id": str,
                "chapter": int,
                "position": {"start": int, "end": int},
                "text": str,
                "type": "dialogue" | "narration" | "description"
            }]
        """

    def scan_character_names(text: str) -> [str]:
        """
        扫描角色名

        Args:
            text: 原始文本

        Returns:
            [str]: 角色名列表，已去重
        """
```

### 20.2 角色识别引擎接口

```python
class CharacterRecognitionEngine:
    """角色识别引擎 - 识别角色及其状态"""

    def identify_characters(block: Block, known_characters: [str]) -> CharacterResult:
        """
        识别分块中的角色

        Args:
            block: 文本分块
            known_characters: 已知角色列表

        Returns:
            CharacterResult: {
                "characters": [Character],  # 识别到的角色
                "new_characters": [str],    # 新发现的角色名
                "confidence": float         # 整体置信度
            }

        Raises:
            LLMTimeoutError: LLM调用超时
            LLMResponseFormatError: 响应格式错误
        """

    def analyze_emotion(text: str, character: str, context: dict) -> EmotionResult:
        """
        分析角色情绪

        Args:
            text: 文本片段
            character: 角色名
            context: 上下文 {
                "previous_emotion": Emotion,
                "scene_context": str,
                "relationships": [str]
            }

        Returns:
            EmotionResult: {
                "emotion_type": str,        # 情绪类型 (如"愤怒+隐忍")
                "emotion_intensity": str,   # 强度 (轻度/中度/强烈)
                "scene_context": str,       # 场景上下文描述
                "suggested_adjustment": str # 建议音色调整
            }
        """

    def update_character_state(character: Character, block_result: BlockResult) -> Character:
        """
        更新角色状态

        Args:
            character: 当前角色状态
            block_result: 分块处理结果

        Returns:
            Character: 更新后的角色状态
        """
```

### 20.3 音色匹配引擎接口

```python
class VoiceMatchEngine:
    """音色匹配引擎 - 匹配合适音色"""

    def match_voice(character: Character, emotion: Emotion) -> MatchResult:
        """
        匹配音色

        Args:
            character: 角色信息
            emotion: 情绪信息

        Returns:
            MatchResult: {
                "candidates": [VoiceCandidate],  # 候选音色列表
                "best_match": VoiceCandidate,    # 最佳匹配
                "confidence": float              # 置信度
            }

        Raises:
            EmptyVoiceLibraryError: 音色库为空
            NoMatchError: 无匹配候选
        """

    def filter_by_tags(tags: [str]) -> [Voice]:
        """标签初筛"""

    def semantic_match(character_desc: str, candidates: [Voice]) -> [VoiceCandidate]:
        """语义匹配"""

    def confirm_voice(character: Character, voice: Voice, is_protagonist: bool) -> ConfirmResult:
        """
        确认音色选择

        Args:
            character: 角色信息
            voice: 选择的音色
            is_protagonist: 是否为主角

        Returns:
            ConfirmResult: {
                "confirmed": bool,
                "alternative_suggestions": [Voice]
            }

        Raises:
            AllCandidatesRejectedError: 用户拒绝所有候选
        """
```

### 20.4 语音合成引擎接口

```python
class VoiceSynthesisEngine:
    """语音合成引擎 - 生成情绪化语音"""

    def generate_prompt(voice: Voice, emotion: Emotion, text: str) -> str:
        """
        生成提示词

        Args:
            voice: 音色信息
            emotion: 情绪信息
            text: 待合成文本

        Returns:
            str: GPT-SoVITS提示词
        """

    def synthesize(prompt: str, text: str, voice_id: str) -> AudioFragment:
        """
        合成语音

        Args:
            prompt: 提示词
            text: 文本
            voice_id: 音色ID

        Returns:
            AudioFragment: {
                "fragment_id": str,
                "audio_data": bytes,
                "duration": float,
                "sample_rate": int,
                "format": str
            }

        Raises:
            TTSServiceUnavailableError: 服务不可用
            TTSAPITimeoutError: 合成超时
            CorruptedAudioError: 音频损坏
        """

    def validate_audio(fragment: AudioFragment, expected_duration: float) -> ValidationResult:
        """
        验证音频完整性

        Args:
            fragment: 音频片段
            expected_duration: 预期时长

        Returns:
            ValidationResult: {
                "valid": bool,
                "issues": [str],
                "actual_duration": float
            }
        """
```

---

## 二十一、并发模型设计 ★★

### 21.1 处理流程模型

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         并发处理模型                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MVP Phase 1 (单线程顺序处理):                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Main Thread                                                              │ │
│  │   │                                                                      │ │
│  │   ├──▶ 解析小说                                                          │ │
│  │   │     ↓                                                                │ │
│  │   ├──▶ 扫描角色名                                                        │ │
│  │   │     ↓                                                                │ │
│  │   ├──▶ 分块处理 (for each block):                                        │ │
│  │   │     ├──▶ 角色识别 (LLM调用, 阻塞)                                    │ │
│  │   │     ├──▶ 情绪分析 (LLM调用, 阻塞)                                    │ │
│  │   │     ├──▶ 音色匹配                                                    │ │
│  │   │     ├──▶ 语音合成 (GPT-SoVITS调用, 阻塞) ★ 主要瓶颈                  │ │
│  │   │     └──▶ 缓存片段                                                    │ │
│  │   │     ↓                                                                │ │
│  │   ├──▶ 音频拼接                                                          │ │
│  │   └──▶ 输出有声书                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Phase 2 (异步并发处理):                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Main Thread                    │ Worker Pool (合成任务)                 │ │
│  │   │                            │                                        │ │
│  │   ├──▶ 解析小说                │  ┌─────────────────────────────────┐   │ │
│  │   │     ↓                      │  │ Task Queue (asyncio.Queue)      │   │ │
│  │   ├──▶ 扫描角色名              │  │   ┌─────┐ ┌─────┐ ┌─────┐     │   │ │
│  │   │     ↓                      │  │   │ T1  │ │ T2  │ │ T3  │ ... │   │ │
│  │   ├──▶ 分块处理 (async for):   │  │   └─────┘ └─────┘ └─────┘     │   │ │
│  │   │     ├──▶ 角色识别          │  └─────────────────────────────────┘   │ │
│  │   │     ├──▶ 情绪分析          │             ↓                          │ │
│  │   │     ├──▶ 音色匹配          │  ┌─────────────────────────────────┐   │ │
│  │   │     └──▶ 提交合成任务 ────▶│  │ Worker 1 │ Worker 2 │ Worker N │   │ │
│  │   │           (非阻塞)         │  │   ↓        │   ↓      │   ↓     │   │ │
│  │   │                            │  │ 合成     合成      合成        │   │ │
│  │   ├──▶ 收集结果 (await)        │  └─────────────────────────────────┘   │ │
│  │   │     ↓                      │                                        │ │
│  │   ├──▶ 音频拼接                │                                        │ │
│  │   └──▶ 输出有声书              │                                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 21.2 MVP Phase 1 实现

```python
# 单线程顺序处理，简单可靠
class AudiobookProcessor:
    def process_novel(self, novel_path: str) -> AudiobookResult:
        # 1. 解析
        parse_result = self.parser.parse_novel(novel_path)

        # 2. 扫描角色
        characters = self.parser.scan_character_names(parse_result.text)

        # 3. 分块处理
        fragments = []
        for block in parse_result.blocks:
            # 角色识别 (阻塞)
            char_result = self.character_engine.identify_characters(block, characters)

            # 情绪分析 (阻塞)
            emotion_result = self.character_engine.analyze_emotion(
                block.text, char_result.primary_character
            )

            # 音色匹配
            voice_match = self.voice_engine.match_voice(
                char_result.primary_character, emotion_result
            )

            # 语音合成 (阻塞，主要瓶颈)
            fragment = self.synthesis_engine.synthesize(
                voice_match.best_match, block.text, emotion_result
            )
            fragments.append(fragment)

        # 4. 拼接输出
        return self.stitch_fragments(fragments)
```

### 21.3 Phase 2 异步实现

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncAudiobookProcessor:
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers)  # 控制并发数

    async def process_novel(self, novel_path: str) -> AudiobookResult:
        # 1. 解析 (同步)
        parse_result = self.parser.parse_novel(novel_path)

        # 2. 创建合成任务
        tasks = []
        for block in parse_result.blocks:
            task = asyncio.create_task(
                self.process_block_async(block)
            )
            tasks.append(task)

        # 3. 并发处理所有块
        fragments = await asyncio.gather(*tasks, return_exceptions=True)

        # 4. 处理异常和拼接
        valid_fragments = [f for f in fragments if not isinstance(f, Exception)]
        return self.stitch_fragments(valid_fragments)

    async def process_block_async(self, block: Block) -> AudioFragment:
        async with self.semaphore:  # 限制并发数
            # 角色识别
            char_result = await asyncio.to_thread(
                self.character_engine.identify_characters, block
            )

            # 语音合成
            fragment = await asyncio.to_thread(
                self.synthesis_engine.synthesize, ...
            )
            return fragment
```

### 21.4 进度回调机制

```python
from typing import Callable
from dataclasses import dataclass

@dataclass
class ProgressInfo:
    total_blocks: int
    processed_blocks: int
    current_stage: str
    current_character: str
    failed_blocks: int

class ProgressCallback:
    def __init__(self, callback: Callable[[ProgressInfo], None], interval: float = 1.0):
        self.callback = callback
        self.interval = interval
        self.last_call = 0

    def update(self, info: ProgressInfo):
        import time
        now = time.time()
        if now - self.last_call >= self.interval:
            self.callback(info)
            self.last_call = now
```

---

## 二十二、核心数据类定义 ★★

### 22.1 数据类图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Novel       │     │    Character    │     │     Voice       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ novel_id: str   │────▶│ name: str       │────▶│ voice_id: str   │
│ title: str      │     │ voice_id: str   │     │ name: str       │
│ file_path: str  │     │ emotion: Emotion│     │ gender: str     │
│ encoding: str   │     │ importance: str │     │ age_range: str  │
│ blocks: [Block] │     │ relationships:  │     │ tags: [str]     │
│ characters: [str]│    │   [Relation]    │     │ description: str│
└─────────────────┘     │ state: Character│     │ embedding: [float]│
                        │   State         │     │ audio_path: str │
                        └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │ CharacterState  │
                        ├─────────────────┤
                        │ character_id: str│
                        │ current_emotion: │
                        │   Emotion       │
                        │ key_relations:  │
                        │   [str]         │
                        │ history_summary:│
                        │   str           │
                        │ base_params:    │
                        │   VoiceParams   │
                        │ consistency: float│
                        └─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     Block       │     │    Fragment     │     │    Emotion      │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ block_id: str   │────▶│ fragment_id: str│     │ emotion_type: str│
│ chapter: int    │     │ block_id: str   │     │ intensity: str  │
│ position: Range │     │ character: str  │     │ components: [str]│
│ text: str       │     │ voice_id: str   │     │ scene_context: str│
│ type: BlockType │     │ emotion: Emotion│     │ suggested_adj: str│
│ dialogues: [Dia]│     │ audio_path: str │     └─────────────────┘
└─────────────────┘     │ duration: float │
                        │ status: Fragment│
                        │   Status        │
                        └─────────────────┘
```

### 22.2 核心数据类定义

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Literal
from enum import Enum

# ===== 枚举定义 =====

class BlockType(Enum):
    DIALOGUE = "dialogue"
    NARRATION = "narration"
    DESCRIPTION = "description"

class EmotionIntensity(Enum):
    LIGHT = "轻度"
    MODERATE = "中度"
    STRONG = "强烈"

class CharacterImportance(Enum):
    PROTAGONIST = "主角"
    SUPPORTING = "配角"
    MINOR = "次要"

class FragmentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# ===== 核心数据类 =====

@dataclass
class Range:
    """位置范围"""
    start: int
    end: int

@dataclass
class Emotion:
    """情绪"""
    emotion_type: str           # 如 "愤怒+隐忍"
    intensity: EmotionIntensity
    components: List[str]       # 情绪组成部分
    scene_context: str          # 场景上下文
    suggested_adjustment: str   # 建议音色调整

@dataclass
class VoiceParams:
    """音色参数"""
    base_speed: float = 1.0
    base_pitch: str = "中性"
    feature_anchors: List[Dict] = field(default_factory=list)

@dataclass
class CharacterState:
    """角色状态"""
    character_id: str
    current_emotion: Optional[Emotion] = None
    key_relations: List[str] = field(default_factory=list)
    history_summary: str = ""
    base_params: Optional[VoiceParams] = None
    consistency_score: float = 1.0

@dataclass
class Character:
    """角色"""
    name: str
    voice_id: Optional[str] = None
    emotion: Optional[Emotion] = None
    importance: CharacterImportance = CharacterImportance.SUPPORTING
    relationships: List[str] = field(default_factory=list)
    state: Optional[CharacterState] = None

@dataclass
class Voice:
    """音色"""
    voice_id: str
    name: str
    gender: Literal["男", "女", "中性"]
    age_range: str              # 如 "青年", "中年"
    tags: List[str] = field(default_factory=list)
    description: str = ""
    embedding: Optional[List[float]] = None
    audio_path: str = ""

@dataclass
class Dialogue:
    """对话"""
    speaker: str
    content: str
    emotion_hint: Optional[str] = None

@dataclass
class Block:
    """文本分块"""
    block_id: str
    chapter: int
    position: Range
    text: str
    type: BlockType = BlockType.NARRATION
    dialogues: List[Dialogue] = field(default_factory=list)

@dataclass
class Fragment:
    """音频片段"""
    fragment_id: str
    block_id: str
    character: str
    voice_id: str
    emotion: Emotion
    audio_path: str
    duration: float
    status: FragmentStatus = FragmentStatus.PENDING

@dataclass
class Novel:
    """小说"""
    novel_id: str
    title: str
    file_path: str
    encoding: str = "utf-8"
    blocks: List[Block] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
```

---

## 二十三、配置验证规范 ★★

### 23.1 配置项定义

| 配置项 | 类型 | 必需 | 默认值 | 验证规则 |
|--------|------|------|--------|----------|
| tts.engine | str | 否 | "gpt-sovits" | 枚举值 |
| tts.endpoint | str | 是 | - | 有效URL格式 |
| tts.timeout | int | 否 | 60 | 范围: 10-300 |
| tts.retry | int | 否 | 3 | 范围: 0-10 |
| llm.provider | str | 否 | "none" | 枚举值 |
| llm.model | str | 条件 | - | provider非none时必需 |
| llm.api_key | str | 条件 | - | provider为openai时必需 |
| voice_library.path | str | 是 | - | 有效路径，可创建 |
| voice_library.max_size_gb | int | 否 | 1 | 范围: 0.1-100 |
| sound_library.path | str | 否 | - | 有效路径 |
| sound_library.enabled | bool | 否 | false | - |
| output.format | str | 否 | "wav" | 枚举: wav/mp3/ogg |
| output.sample_rate | int | 否 | 44100 | 枚举: 16000/22050/44100 |
| output.max_file_size_mb | int | 否 | 500 | 范围: 1-2000 |
| performance.parallel_synthesis | int | 否 | 1 | 范围: 1-8 |
| performance.cache_size_mb | int | 否 | 500 | 范围: 100-10000 |
| performance.memory_limit_mb | int | 否 | 1000 | 范围: 500-16000 |

### 23.2 配置验证实现

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from pathlib import Path

class TTSConfig(BaseModel):
    engine: Literal["gpt-sovits"] = "gpt-sovits"
    endpoint: str  # 必需
    timeout: int = Field(default=60, ge=10, le=300)
    retry: int = Field(default=3, ge=0, le=10)

    @validator('endpoint')
    def validate_endpoint(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('endpoint must be a valid URL')
        return v

class LLMConfig(BaseModel):
    provider: Literal["openai", "ollama", "none"] = "none"
    model: Optional[str] = None
    api_key: Optional[str] = None

    @validator('model', always=True)
    def validate_model(cls, v, values):
        if values.get('provider') != 'none' and not v:
            raise ValueError('model is required when provider is not "none"')
        return v

    @validator('api_key', always=True)
    def validate_api_key(cls, v, values):
        if values.get('provider') == 'openai' and not v:
            raise ValueError('api_key is required when provider is "openai"')
        return v

class VoiceLibraryConfig(BaseModel):
    path: str  # 必需
    max_size_gb: int = Field(default=1, ge=0.1, le=100)

    @validator('path')
    def validate_path(cls, v):
        path = Path(v).expanduser()
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception:
                raise ValueError(f'Cannot create directory: {v}')
        return v

class AppConfig(BaseModel):
    tts: TTSConfig
    llm: LLMConfig = LLMConfig()
    voice_library: VoiceLibraryConfig
    output: OutputConfig = OutputConfig()
    performance: PerformanceConfig = PerformanceConfig()

    class Config:
        extra = "forbid"  # 禁止未知配置项

def load_config(config_path: str) -> AppConfig:
    """加载并验证配置"""
    import yaml
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)  # 验证并填充默认值
```

### 23.3 配置错误处理

| 错误场景 | 处理方式 | 用户消息 |
|---------|---------|---------|
| 配置文件不存在 | 生成默认配置模板 | "配置文件不存在，已生成默认配置: {path}" |
| 缺少必需项 | 列出缺失项 | "配置错误: 缺少必需项 {item}" |
| 值类型错误 | 显示期望类型 | "配置错误: {item} 应为 {type}, 实际为 {actual}" |
| 值范围错误 | 显示有效范围 | "配置错误: {item} 应在 {min}-{max} 范围内" |
| 路径不存在 | 提示创建或检查 | "配置错误: 路径 {path} 不存在，是否创建?" |
| API密钥未配置 | 提示设置环境变量 | "配置错误: 请设置 {env_var} 环境变量" |

---

## 二十四、测试文件结构 ★★

### 24.1 目录结构

```
audiobook-converter/
├── src/
│   └── audiobook/
│       ├── engines/
│       │   ├── parser.py
│       │   ├── character.py
│       │   ├── voice_match.py
│       │   └── synthesis.py
│       └── models/
│           ├── novel.py
│           ├── character.py
│           └── voice.py
├── tests/
│   ├── conftest.py              # 共享fixtures
│   ├── unit/
│   │   ├── engines/
│   │   │   ├── test_parser.py
│   │   │   ├── test_character.py
│   │   │   ├── test_voice_match.py
│   │   │   └── test_synthesis.py
│   │   └── models/
│   │       ├── test_novel.py
│   │       ├── test_character.py
│   │       └── test_voice.py
│   ├── integration/
│   │   ├── test_parser_to_character.py
│   │   ├── test_character_to_voice.py
│   │   ├── test_voice_to_synthesis.py
│   │   └── test_full_pipeline.py
│   ├── e2e/
│   │   ├── test_complete_conversion.py
│   │   └── fixtures/
│   │       └── sample_novel.txt
│   └── performance/
│       └── test_benchmarks.py
├── pytest.ini
└── requirements-test.txt
```

### 24.2 pytest 配置

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: 单元测试
    integration: 集成测试
    e2e: 端到端测试
    slow: 慢速测试 (跳过: pytest -m "not slow")
    requires_gpu: 需要GPU的测试
filterwarnings =
    ignore::DeprecationWarning
```

### 24.3 共享 Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path
from audiobook.models import Novel, Character, Voice, Emotion, Block

@pytest.fixture
def sample_novel_path(tmp_path):
    """创建测试用小说文件"""
    novel_path = tmp_path / "test_novel.txt"
    novel_path.write_text("""第一章 开始

"你好，我是张三。"张三说道。
"你好，我是李四。"李四回答道。

张三看着李四，心中涌起一股愤怒。
""")
    return novel_path

@pytest.fixture
def sample_character():
    """测试用角色"""
    return Character(
        name="张三",
        importance="主角",
        emotion=Emotion(
            emotion_type="愤怒",
            intensity="中度",
            components=["愤怒"],
            scene_context="与李四对峙",
            suggested_adjustment="语速略快，语气带压抑感"
        )
    )

@pytest.fixture
def sample_voice():
    """测试用音色"""
    return Voice(
        voice_id="voice_001",
        name="青年男声-温和",
        gender="男",
        age_range="青年",
        tags=["温和", "适合主角"],
        description="声音温润有磁性",
        audio_path="/path/to/voice.wav"
    )

@pytest.fixture
def mock_gptsovitis(monkeypatch):
    """模拟GPT-SoVITS服务"""
    def mock_synthesize(*args, **kwargs):
        return b"fake_audio_data"
    monkeypatch.setattr("audiobook.engines.synthesis.synthesize", mock_synthesize)
```

### 24.4 测试示例

```python
# tests/unit/engines/test_parser.py
import pytest
from audiobook.engines.parser import NovelParserEngine

class TestNovelParserEngine:
    @pytest.mark.unit
    def test_parse_novel_success(self, sample_novel_path):
        """测试正常解析"""
        engine = NovelParserEngine()
        result = engine.parse_novel(str(sample_novel_path))

        assert result.title == "test_novel"
        assert result.total_chapters == 1
        assert len(result.character_names) == 2

    @pytest.mark.unit
    def test_parse_novel_file_not_found(self):
        """测试文件不存在"""
        engine = NovelParserEngine()
        with pytest.raises(FileNotFoundError):
            engine.parse_novel("/nonexistent/path.txt")

    @pytest.mark.unit
    def test_parse_novel_empty_file(self, tmp_path):
        """测试空文件"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        engine = NovelParserEngine()
        with pytest.raises(EmptyFileError):
            engine.parse_novel(str(empty_file))

    @pytest.mark.unit
    def test_scan_character_names(self):
        """测试角色名扫描"""
        engine = NovelParserEngine()
        text = '"我是张三。"张三说道。"我是李四。"李四回答。'
        names = engine.scan_character_names(text)
        assert "张三" in names
        assert "李四" in names
```

---

## 二十五、性能基准定义 ★★

### 25.1 基准测试方法

```python
# tests/performance/test_benchmarks.py
import pytest
import time
from audiobook.engines.parser import NovelParserEngine
from audiobook.engines.voice_match import VoiceMatchEngine

class PerformanceBenchmark:
    """性能基准测试"""

    @pytest.mark.slow
    @pytest.mark.benchmark
    def test_parse_benchmark(self, large_novel_path):
        """小说解析性能基准"""
        engine = NovelParserEngine()

        start = time.time()
        result = engine.parse_novel(str(large_novel_path))
        elapsed = time.time() - start

        # 基准: 50MB文件 < 5秒
        assert elapsed < 5.0, f"Parsing took {elapsed:.2f}s, expected < 5s"

        # 记录结果
        print(f"Parsed {result.total_characters} chars in {elapsed:.2f}s")
        print(f"Throughput: {result.total_characters / elapsed:.0f} chars/s")

    @pytest.mark.benchmark
    def test_voice_match_benchmark(self, sample_character, populated_voice_library):
        """音色匹配性能基准"""
        engine = VoiceMatchEngine()

        start = time.time()
        result = engine.match_voice(sample_character, sample_character.emotion)
        elapsed = time.time() - start

        # 基准: < 3秒
        assert elapsed < 3.0, f"Matching took {elapsed:.2f}s, expected < 3s"
```

### 25.2 关键操作基准

| 操作 | 输入规模 | 预期耗时 | 可接受范围 | 测试方法 |
|------|---------|---------|-----------|---------|
| 小说解析 | 10MB | < 1s | 1-3s | 基准测试 |
| 小说解析 | 50MB | < 5s | 5-10s | 基准测试 |
| 角色名扫描 | 100万字 | < 2s | 2-5s | 基准测试 |
| 音色匹配 | 100候选 | < 3s | 3-10s | 基准测试 |
| 语音合成 (单片段) | 100字 | < 10s | 10-30s | 依赖GPT-SoVITS |
| 音频拼接 | 100片段 | < 5s | 5-15s | 基准测试 |
| 内存占用 | 处理中 | < 500MB | 500MB-1GB | 资源监控 |

### 25.3 性能回归检测

```yaml
# .github/workflows/performance.yml
name: Performance Regression

on:
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -e .[test]

      - name: Run benchmarks
        run: pytest tests/performance/ -v --benchmark-only

      - name: Compare with baseline
        run: |
          python scripts/compare_benchmarks.py \
            --current .benchmarks/current.json \
            --baseline .benchmarks/baseline.json \
            --threshold 1.5  # 允许1.5x回归

      - name: Fail on regression
        run: |
          if [ -f .benchmarks/regression_detected ]; then
            echo "Performance regression detected!"
            exit 1
          fi
```

---

## 二十六、UI设计规范 ★★

### 26.1 设计原则

**产品定位**: 工具型应用，而非营销型页面
- **核心价值**: 高效完成有声书转换任务
- **设计哲学**: 功能优先、减少干扰、清晰反馈
- **避免**: AI生成的通用SaaS模板风格

### 26.2 信息层次架构

#### 26.2.1 CLI界面层次

```
第一层 (最重要): 进度条 + 百分比 + 当前章节
第二层: 当前处理状态 (角色+情绪)
第三层: 统计信息 (已处理/失败/时间)
第四层: 日志信息 (INFO/WARNING)
```

**视觉权重分布**:
```
[████████████░░░░░░░░░░░░░░░░] 30%  第15章/共50章  ← 高对比度，最大字号
当前: 语音合成 - 张三(愤怒-中度)                    ← 中等强调
已处理: 750片段 | 失败: 3片段                        ← 常规
已用时: 1h0m | 预计剩余: 2h0m                       ← 常规
[INFO] 第15章处理完成                               ← 低对比度
```

#### 26.2.2 Web界面 - 音色库管理

**屏幕布局层次**:
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: 音色库管理                          [+ 导入音色]   │ 第一层
├─────────────────────────────────────────────────────────────┤
│ SEARCH: [🔍 搜索音色...                    ] [高级筛选 ▾]  │ 第一层
├──────────────┬──────────────────────────────────────────────┤
│ SIDEBAR      │ MAIN CONTENT                                │
│ ┌──────────┐ │ ┌────────────────────────────────────────┐   │
│ │ 全部 (128)│ │ │ 音色卡片网格                           │   │ 第二层
│ │ 男声 (56) │ │ │ ┌──────┐ ┌──────┐ ┌──────┐           │   │
│ │ 女声 (68) │ │ │ │ 青年 │ │ 温和 │ │ 激昂 │ ...       │   │
│ │ 中性 (4)  │ │ │ └──────┘ └──────┘ └──────┘           │   │
│ │ 标签筛选  │ │ └────────────────────────────────────────┘   │
│ └──────────┘ │                                              │
│              │ PAGINATION: [< 1 2 3 ... 10 >]               │ 第三层
└──────────────┴──────────────────────────────────────────────┘
```

**信息优先级**:
| 层级 | 元素 | 设计处理 |
|------|------|----------|
| P1 | 搜索框 | 全宽，明显位置，默认焦点 |
| P1 | 导入按钮 | 主要行动按钮样式 |
| P2 | 音色卡片 | 可点击，悬停高亮 |
| P3 | 筛选侧栏 | 可折叠，不影响主流程 |
| P3 | 分页 | 小型，非干扰性 |

#### 26.2.3 Web界面 - 音色确认

**场景**: 主角音色选择，需要用户确认

**屏幕布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: 为角色"张三"选择音色                                 │ 第一层
│        主角 · 已出场 23 次 · 性格: 沉稳内敛                   │ 第二层
├─────────────────────────────────────────────────────────────┤
│ CANDIDATES SECTION                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 推荐: 基于角色特征匹配的候选音色                          │ │ 第一层
│ │                                                         │ │
│ │ ┌──────────────────┐ ┌──────────────────┐              │ │
│ │ │ ○ voice_001      │ │ ○ voice_002      │              │ │ 第二层
│ │ │ 青年男声-温和     │ │ 青年男声-沉稳     │              │ │
│ │ │ 匹配度: 92%      │ │ 匹配度: 87%      │              │ │
│ │ │ [▶ 试听]         │ │ [▶ 试听]         │              │ │
│ │ └──────────────────┘ └──────────────────┘              │ │
│ │                                                         │ │
│ │ [显示更多候选...]                                       │ │ 第三层
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ PREVIEW SECTION                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 预览对比: 选择音色朗读角色台词                           │ │ 第二层
│ │                                                         │ │
│ │ 原文: "我是张三，这件事我必须说清楚。"                   │ │
│ │                                                         │ │
│ │ voice_001: [▶ 播放] voice_002: [▶ 播放]               │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ACTIONS:                                                    │
│ [确认选择] [重新匹配] [手动选择]                             │ 第一层
└─────────────────────────────────────────────────────────────┘
```

#### 26.2.4 预览播放器

**屏幕布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: 音频预览                                    [关闭 ×] │ 第一层
├─────────────────────────────────────────────────────────────┤
│ WAVEFORM DISPLAY                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │ 第一层
│ │              ▲ 当前位置                                  │ │
│ │ 00:23 / 01:45                                           │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ CONTROLS                                                    │
│     [⏮] [⏪] [▶/⏸] [⏩] [⏭]     音量: [●────────] 1.0x    │ 第一层
├─────────────────────────────────────────────────────────────┤
│ FRAGMENT INFO                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 角色: 张三 | 情绪: 愤怒-中度 | 章节: 5 | 片段: 23       │ │ 第二层
│ │ 原文: "我再也不想见到你了！"                             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 26.2.5 进度仪表盘

**屏幕布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: 《示例小说》转换进度                                 │ 第一层
│        开始时间: 14:30 | 任务ID: job_20260329_143000        │ 第三层
├─────────────────────────────────────────────────────────────┤
│ MAIN PROGRESS                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │
│ │           ████████████████░░░░░░░░░░░░░                 │ │ 第一层
│ │                        45%                              │ │
│ │                                                         │ │
│ │         第 23 章 / 共 50 章                              │ │ 第一层
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ STATS ROW                                                   │
│ ┌────────────┬────────────┬────────────┬────────────────┐   │
│ │ 已完成     │ 进行中     │ 待处理     │ 失败           │   │ 第二层
│ │ 1,125      │ 1          │ 1,374      │ 2              │   │
│ │ 片段       │ 片段       │ 片段       │ 片段           │   │
│ └────────────┴────────────┴────────────┴────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ TIME ESTIMATES                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 已用时: 1小时30分 | 预计剩余: 1小时50分                 │ │ 第二层
│ │ 处理速度: ~12.5 片段/分钟                               │ │ 第三层
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ CURRENT ACTIVITY                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 当前: 语音合成 - 第23章                                 │ │ 第二层
│ │ 角色: 李四 | 情绪: 悲伤-中度                            │ │ 第三层
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 26.2.6 异常报告

**屏幕布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: 处理异常报告                                        │ 第一层
│        成功率: 99.88% | 失败片段: 3 / 2,500                 │ 第二层
├─────────────────────────────────────────────────────────────┤
│ EXCEPTION LIST                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ #1 [一致性警告] frag_0123                               │ │ 第二层
│ │    章节: 5 | 位置: 第3段第2句                            │ │ 第三层
│ │    原文: "张三愤怒地拍桌而起..."                         │ │
│ │    问题: 一致性得分 0.72 < 阈值 0.75                     │ │
│ │    [查看原文 →] [重新合成] [标记忽略]                    │ │ 第一层(操作)
│ │                                                         │ │
│ │ #2 [合成失败] frag_0456                                 │ │
│ │    章节: 12 | 位置: 第8段                                │ │
│ │    原文: "..."                                          │ │
│ │    问题: GPT-SoVITS 返回损坏音频                        │ │
│ │    [查看原文 →] [重新合成] [标记忽略]                    │ │
│ │                                                         │ │
│ │ #3 [音色匹配失败] frag_0789                             │ │
│ │    章节: 18 | 位置: 第2段                                │ │
│ │    原文: "..."                                          │ │
│ │    问题: 无匹配候选，已使用默认音色                      │ │
│ │    [查看原文 →] [重新匹配] [标记忽略]                    │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ BATCH ACTIONS                                               │
│ [全部重新合成] [全部忽略] [导出报告]                         │ 第一层
└─────────────────────────────────────────────────────────────┘
```

### 26.3 交互状态覆盖

#### 26.3.1 交互状态矩阵

| 界面 | 功能 | LOADING | EMPTY | ERROR | SUCCESS | PARTIAL |
|------|------|---------|-------|-------|---------|---------|
| 音色库 | 列表加载 | 骨架屏+加载动画 | "暂无音色，点击导入" | 加载失败提示 | 正常显示 | - |
| 音色库 | 搜索 | 搜索中动画 | "未找到匹配音色" | - | 结果列表 | "找到 N/总M 个" |
| 音色库 | 导入 | 上传进度条 | - | 格式错误/大小超限 | "导入成功" | 部分成功警告 |
| 音色确认 | 匹配 | "正在匹配..." | 无候选→手动选择 | 匹配失败→重试 | 候选列表 | 低置信度警告 |
| 预览播放 | 加载 | 波形加载动画 | - | 播放失败→重试 | 播放中 | - |
| 进度仪表盘 | 刷新 | 数据刷新中 | 无任务→新建 | 数据异常→重试 | 实时更新 | - |
| 异常报告 | 加载 | 加载中 | "无异常，一切正常✓" | 加载失败→重试 | 异常列表 | - |

#### 26.3.2 空状态设计

**音色库空状态**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ┌─────────────┐                        │
│                      │   🎙️       │                        │
│                      └─────────────┘                        │
│                                                             │
│              音色库为空                                      │
│              导入音色开始创建有声书                          │
│                                                             │
│              [导入音色]  [下载示例音色包]                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**搜索无结果**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    未找到匹配的音色                          │
│                    尝试调整搜索词或筛选条件                  │
│                                                             │
│                    [清除筛选] [导入新音色]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**无异常报告**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ┌─────────────┐                        │
│                      │    ✓       │                        │
│                      └─────────────┘                        │
│                                                             │
│              一切正常                                        │
│              所有片段处理成功                                │
│                                                             │
│              [下载有声书]                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 26.3.3 错误状态设计

**网络错误**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ⚠️ 网络连接失败                        │
│                      请检查网络连接后重试                    │
│                                                             │
│                      [重试]                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**API服务不可用**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                      ⚠️ 语音合成服务不可用                  │
│                      请确认 GPT-SoVITS 服务正在运行          │
│                      服务地址: http://localhost:9880        │
│                                                             │
│                      [重试] [检查服务状态]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 26.4 用户旅程设计

#### 26.4.1 首次使用流程

```
STEP | 用户操作              | 用户感受          | 界面支持
-----|----------------------|-------------------|------------------
1    | 安装软件              | 期待/好奇         | 安装成功提示
2    | 运行首次命令          | 不确定            | 引导式帮助
3    | 导入小说文件          | 期待              | 文件选择器
4    | 看到角色识别结果      | 惊喜/验证         | 角色列表展示
5    | 确认主角音色          | 参与感            | 音色确认界面
6    | 等待处理              | 等待/好奇         | 进度仪表盘
7    | 处理完成              | 成就感            | 成功提示+下载
8    | 试听结果              | 满足/自豪         | 播放器界面
```

#### 26.4.2 情感弧线设计

```
情感强度
    ^
    │           ┌─────┐                    ┌─────┐
    │          /       \                  /       \
    │         /         \                /         \
    │        /           \              /           \
    │   ┌───┘             \    ┌───────┘             \
    │   │                  \  /                       \
    │───┴────────────────────┴─────────────────────────┴───→ 时间
        安装   导入   确认音色   处理中   完成   试听
        好奇   期待   参与感     等待    成就   满足
```

**关键情感触点**:
1. **角色识别展示** → "它真的读懂了这本书！"
2. **音色匹配推荐** → "它理解这个角色的性格！"
3. **处理进度可视化** → "一切在掌控中"
4. **试听对比** → "效果超出预期！"

### 26.5 AI生成内容检测与规避

#### 26.5.1 需规避的模式

| 模式 | 风险 | 替代方案 |
|------|------|----------|
| 紫色渐变背景 | AI模板感 | 使用中性色(深灰/深蓝)或品牌色 |
| 3列功能卡片网格 | SaaS模板感 | 列表视图优先，紧凑布局 |
| 居中布局+大标题 | 营销页面感 | 左对齐，信息密度优先 |
| 圆角卡片+阴影 | 通用设计 | 扁平设计，边框区分 |
| emoji作为设计元素 | 不专业感 | 仅在空状态使用，谨慎 |
| "解锁"、"赋能"等词汇 | AI文案感 | 使用工具性语言 |

#### 26.5.2 设计意图声明

**我们不是**:
- 一个SaaS营销页面
- 一个需要"吸引用户"的产品
- 一个需要展示"特性"的工具

**我们是**:
- 一个高效的任务完成工具
- 一个专业创作者的辅助工具
- 一个追求效率的实用程序

**设计决策**:
- 功能性 > 美观性
- 效率 > 娱乐性
- 清晰 > 印象

### 26.6 响应式设计规范

#### 26.6.1 断点定义

| 断点 | 宽度范围 | 典型设备 | 布局调整 |
|------|----------|----------|----------|
| xs | <576px | 手机竖屏 | 单列，隐藏侧栏 |
| sm | 576-768px | 手机横屏/小平板 | 单列，可折叠侧栏 |
| md | 768-992px | 平板竖屏 | 两列，侧栏折叠 |
| lg | 992-1200px | 平板横屏/小笔记本 | 两列，侧栏展开 |
| xl | >1200px | 桌面 | 三列/全功能 |

#### 26.6.2 关键界面响应式适配

**音色库管理 - 移动端**:
```
┌─────────────────────┐
│ 音色库    [+] [⚙]  │  Header简化
├─────────────────────┤
│ [🔍 搜索...]        │  搜索全宽
├─────────────────────┤
│ [筛选 ▾]            │  筛选变为下拉
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ 音色卡片        │ │  单列卡片
│ │ (全宽)          │ │
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ 音色卡片        │ │
│ └─────────────────┘ │
│ ...                 │
└─────────────────────┘
```

**进度仪表盘 - 移动端**:
```
┌─────────────────────┐
│ 《小说名》          │
│ 转换进度            │
├─────────────────────┤
│    ████████░░       │
│        45%          │
│    23/50 章         │
├─────────────────────┤
│ 完成: 1125          │
│ 失败: 2             │
├─────────────────────┤
│ 已用: 1h30m         │
│ 剩余: ~1h50m        │
└─────────────────────┘
```

### 26.7 无障碍设计规范

#### 26.7.1 键盘导航

| 界面 | 导航模式 | 快捷键 |
|------|----------|--------|
| 音色库列表 | Tab顺序导航 | Tab/Shift+Tab |
| 音色卡片 | 焦点可选中 | Enter确认, Space播放 |
| 音色确认 | 选项组导航 | ↑↓切换, Enter确认 |
| 播放器 | 媒体控制 | Space播放/暂停, ←→跳转 |
| 进度仪表盘 | 只读展示 | Tab切换信息区域 |

#### 26.7.2 屏幕阅读器支持

**ARIA标签规范**:
```html
<!-- 音色卡片 -->
<div role="article" aria-label="音色: 青年男声-温和">
  <button aria-label="播放预览">▶</button>
  <button aria-label="选择此音色">选择</button>
</div>

<!-- 进度条 -->
<div role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" aria-label="转换进度: 45%">
  <div style="width: 45%"></div>
</div>

<!-- 状态提示 -->
<div role="status" aria-live="polite">
  正在处理第23章...
</div>
```

#### 26.7.3 视觉无障碍

| 要求 | 规范 |
|------|------|
| 颜色对比度 | 正文 ≥4.5:1, 大标题 ≥3:1 |
| 焦点指示 | 2px轮廓, 高对比色 |
| 字体大小 | 最小14px, 推荐16px |
| 行高 | ≥1.5倍 |
| 交互区域 | 最小44×44px |

#### 26.7.4 色彩对比方案

**推荐配色** (WCAG AA 级别):
```
背景: #FFFFFF (白)
正文: #1A1A1A (深灰) → 对比度 16.1:1 ✓
次要文字: #666666 → 对比度 5.7:1 ✓
链接: #0066CC → 对比度 5.9:1 ✓
成功: #1A7F37 → 对比度 4.7:1 ✓
警告: #9A6700 → 对比度 4.6:1 ✓
错误: #CF222E → 对比度 4.8:1 ✓
```

### 26.8 设计系统建议

#### 26.8.1 设计令牌

**色彩系统**:
```css
:root {
  /* 主色调 - 中性专业 */
  --color-primary: #2563EB;
  --color-primary-hover: #1D4ED8;

  /* 背景 */
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: #F6F8FA;
  --color-bg-tertiary: #EAEEF2;

  /* 文字 */
  --color-text-primary: #1A1A1A;
  --color-text-secondary: #666666;
  --color-text-tertiary: #999999;

  /* 状态色 */
  --color-success: #1A7F37;
  --color-warning: #9A6700;
  --color-error: #CF222E;
  --color-info: #0969DA;

  /* 边框 */
  --color-border: #D0D7DE;
  --color-border-focus: #2563EB;
}
```

**间距系统** (4px基准):
```css
:root {
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
}
```

**字体系统**:
```css
:root {
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "SF Mono", Monaco, "Cascadia Code", monospace;

  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;
  --font-size-2xl: 32px;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 600;
}
```

#### 26.8.2 组件规范

**按钮**:
```css
/* 主要按钮 */
.btn-primary {
  background: var(--color-primary);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: var(--font-weight-medium);
}
.btn-primary:hover { background: var(--color-primary-hover); }
.btn-primary:focus { outline: 2px solid var(--color-border-focus); }

/* 次要按钮 */
.btn-secondary {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

/* 危险操作 */
.btn-danger {
  background: var(--color-error);
  color: white;
}
```

**卡片**:
```css
.card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: var(--space-md);
}
.card:hover {
  border-color: var(--color-border-focus);
}
```

**输入框**:
```css
.input {
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: var(--font-size-md);
}
.input:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
```

### 26.9 待定设计决策

| 决策项 | 当前状态 | 影响 | 建议 |
|--------|----------|------|------|
| Web框架选型 | 未确定 | 影响组件库选择 | 推荐: React + Tailwind CSS |
| 图表库选型 | 未确定 | 影响进度可视化 | 推荐: Recharts 或 Chart.js |
| 音频播放器 | 未确定 | 影响预览功能 | 推荐: Wavesurfer.js |
| 国际化 | 未确定 | 影响文案管理 | MVP可暂缓，预留接口 |

---

## 附录：CEO Review 记录

**审查日期**: 2026-03-29
**审查模式**: SCOPE EXPANSION
**审查结果**: 通过，已补充10个设计缺失

**扩展决策**:

| # | 提案 | Effort | 决策 | 原因 |
|---|------|--------|------|------|
| 1 | 背景音乐/环境音效自动匹配 | M | ACCEPTED | 将"有声书"升级为"音频剧" |
| 2 | 用户音色克隆 | M | DEFERRED | 平台化阶段功能 |
| 3 | 实时预览系统 | M | ACCEPTED | 用户控制感关键体验 |
| 4 | 角色声音一致性强化 | S | ACCEPTED | 核心差异化关键 |
| D1 | 音色预览对比 | S | ACCEPTED | 增强用户选择体验 |
| D2 | 进度仪表盘 | S | ACCEPTED | 可视化进度反馈 |
| D3 | 异常片段高亮 | S | ACCEPTED | 原文定位增强 |
| D4 | 音色库自然语言搜索 | S | ACCEPTED | 直接搜索入口 |
| D5 | 角色关系可视化 | S | ACCEPTED | 辅助匹配决策 |

**补充设计章节**:
1. 模块依赖关系图
2. 音色一致性控制器
3. 场景音效匹配引擎规范
4. 音频完整性校验
5. 安全设计
6. 阴影路径处理策略
7. 测试策略
8. 性能优化策略
9. 可观测性设计
10. 部署策略

---

## 附录：Design Review 记录

**审查日期**: 2026-03-29
**审查模式**: Full Review (7 passes)
**初始评分**: 3/10
**最终评分**: 8/10

**补充设计章节**:
- 26. UI设计规范

**发现的设计缺失**:

| # | 问题 | 严重度 | 状态 |
|---|------|--------|------|
| 1 | 无信息层次定义 | CRITICAL | ✓ 已补充 (26.2) |
| 2 | 无交互状态覆盖 | CRITICAL | ✓ 已补充 (26.3) |
| 3 | 无用户旅程设计 | HIGH | ✓ 已补充 (26.4) |
| 4 | AI生成内容风险未评估 | MEDIUM | ✓ 已补充 (26.5) |
| 5 | 无响应式设计规范 | HIGH | ✓ 已补充 (26.6) |
| 6 | 无障碍设计未定义 | HIGH | ✓ 已补充 (26.7) |
| 7 | 无设计系统/令牌 | MEDIUM | ✓ 已补充 (26.8) |
| 8 | 待定设计决策未记录 | LOW | ✓ 已补充 (26.9) |

**设计原则确立**:
- 产品定位: 工具型应用 (非营销型)
- 设计哲学: 功能优先、减少干扰、清晰反馈
- 避免: AI生成的通用SaaS模板风格

**待定决策**:
1. Web框架选型 (建议: React + Tailwind CSS)
2. 图表库选型 (建议: Recharts 或 Chart.js)
3. 音频播放器选型 (建议: Wavesurfer.js)
4. 国际化策略 (MVP可暂缓)

---

★ = CEO Review 扩展/补充功能
◆ = Design Review 补充功能