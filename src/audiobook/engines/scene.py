"""Scene sound engine for ambient sounds and background music.

This module provides scene recognition, sound matching, and audio mixing
to enhance audiobooks with immersive background sounds and music.

Core components:
- SceneAnalysis: Analysis result of a scene
- SoundConfig: Configuration for sound mixing
- SceneRecognizer: Recognize scene types and atmospheres
- SoundEngine: Main engine for scene-based sound management
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SceneType(Enum):
    """Types of scenes for sound matching."""

    INDOOR_DAILY = "室内-日常"
    INDOOR_TENSE = "室内-紧张"
    OUTDOOR_DAY = "室外-白天"
    OUTDOOR_NIGHT = "室外-夜晚"
    NATURE_FOREST = "自然-森林"
    NATURE_WATER = "自然-水域"
    WEATHER_RAIN = "天气-雨天"
    WEATHER_SNOW = "天气-雪天"
    BATTLE = "战斗场景"
    MEMORY = "回忆场景"
    UNKNOWN = "未知"


class AtmosphereType(Enum):
    """Atmosphere/mood types for music matching."""

    TENSE = "压抑"
    SAD = "悲伤"
    HAPPY = "欢快"
    ROMANTIC = "浪漫"
    MYSTERIOUS = "神秘"
    NEUTRAL = "平静"


# Scene type recognition keywords
SCENE_KEYWORDS = {
    SceneType.INDOOR_DAILY: ["房间", "客厅", "卧室", "屋内", "室内"],
    SceneType.INDOOR_TENSE: ["审讯室", "密室", "囚室", "地下室"],
    SceneType.OUTDOOR_DAY: ["街道", "广场", "公园", "大街", "路上"],
    SceneType.OUTDOOR_NIGHT: ["夜晚", "月光", "黑夜", "深夜", "夜色"],
    SceneType.NATURE_FOREST: ["森林", "树林", "山林", "树林", "山间"],
    SceneType.NATURE_WATER: ["河边", "湖边", "海边", "江边", "水边"],
    SceneType.WEATHER_RAIN: ["下雨", "暴雨", "雨声", "雨点", "雨水"],
    SceneType.WEATHER_SNOW: ["下雪", "雪花", "白雪", "飘雪", "雪地"],
    SceneType.BATTLE: ["打斗", "战斗", "厮杀", "激战", "交战"],
    SceneType.MEMORY: ["回忆", "想起", "当年", "曾经", "往事"],
}

# Atmosphere recognition keywords
ATMOSPHERE_KEYWORDS = {
    AtmosphereType.TENSE: ["沉默", "压抑", "沉重", "窒息", "紧张"],
    AtmosphereType.SAD: ["哭", "泪", "悲伤", "痛苦", "心碎"],
    AtmosphereType.HAPPY: ["笑", "开心", "快乐", "喜悦", "欢笑"],
    AtmosphereType.ROMANTIC: ["温柔", "甜蜜", "爱情", "浪漫", "深情"],
    AtmosphereType.MYSTERIOUS: ["神秘", "诡异", "未知", "谜", "奇怪"],
}


@dataclass
class SceneAnalysis:
    """Result of scene analysis.

    Attributes:
        scene_type: Detected scene type.
        atmosphere: Detected atmosphere/mood.
        confidence: Confidence score for the detection.
        keywords_matched: Keywords that matched for detection.
        suggested_sounds: Suggested sound IDs for this scene.
    """

    scene_type: SceneType = SceneType.UNKNOWN
    atmosphere: AtmosphereType = AtmosphereType.NEUTRAL
    confidence: float = 0.0
    keywords_matched: list[str] = field(default_factory=list)
    suggested_sounds: list[str] = field(default_factory=list)


@dataclass
class SoundConfig:
    """Configuration for sound mixing.

    Attributes:
        ambient_sound: ID of ambient sound to play.
        background_music: ID of background music to play.
        ambient_volume: Volume for ambient sound (0.0 to 1.0).
        music_volume: Volume for background music (0.0 to 1.0).
        fade_in: Fade in duration in seconds.
        fade_out: Fade out duration in seconds.
        crossfade: Crossfade duration for scene transitions.
    """

    ambient_sound: Optional[str] = None
    background_music: Optional[str] = None
    ambient_volume: float = 0.3
    music_volume: float = 0.15
    fade_in: float = 2.0
    fade_out: float = 1.0
    crossfade: float = 1.0


@dataclass
class AmbientSound:
    """Represents an ambient sound in the library.

    Attributes:
        sound_id: Unique identifier for the sound.
        name: Human-readable name.
        category: Category (indoor, outdoor, nature, weather).
        file_path: Path to the audio file.
        duration: Duration in seconds.
        tags: Tags for searching.
    """

    sound_id: str
    name: str
    category: str
    file_path: str
    duration: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class BackgroundMusic:
    """Represents background music in the library.

    Attributes:
        music_id: Unique identifier for the music.
        name: Human-readable name.
        category: Category (emotional, atmospheric, action).
        file_path: Path to the audio file.
        duration: Duration in seconds.
        bpm: Beats per minute (for matching).
        atmosphere: Associated atmosphere type.
    """

    music_id: str
    name: str
    category: str
    file_path: str
    duration: float = 0.0
    bpm: int = 120
    atmosphere: AtmosphereType = AtmosphereType.NEUTRAL


class SceneRecognizer:
    """Recognizes scene types and atmospheres from text.

    Uses keyword matching to identify scene characteristics
    that influence sound selection.
    """

    def __init__(self) -> None:
        """Initialize the scene recognizer."""
        self.scene_keywords = SCENE_KEYWORDS
        self.atmosphere_keywords = ATMOSPHERE_KEYWORDS

    def analyze(self, text: str, character_states: Optional[dict] = None) -> SceneAnalysis:
        """Analyze a text segment to determine scene type and atmosphere.

        Args:
            text: Text to analyze.
            character_states: Optional character states for context.

        Returns:
            SceneAnalysis with detected scene characteristics.
        """
        text_lower = text.lower()

        # Detect scene type
        scene_type = SceneType.UNKNOWN
        scene_confidence = 0.0
        scene_keywords_matched: list[str] = []

        for stype, keywords in self.scene_keywords.items():
            matches = [kw for kw in keywords if kw in text]
            if matches:
                match_ratio = len(matches) / len(keywords)
                if match_ratio > scene_confidence:
                    scene_type = stype
                    scene_confidence = match_ratio
                    scene_keywords_matched = matches

        # Detect atmosphere
        atmosphere = AtmosphereType.NEUTRAL
        atmosphere_confidence = 0.0

        for atype, keywords in self.atmosphere_keywords.items():
            matches = [kw for kw in keywords if kw in text]
            if matches:
                match_ratio = len(matches) / len(keywords)
                if match_ratio > atmosphere_confidence:
                    atmosphere = atype
                    atmosphere_confidence = match_ratio

        # Check character states for additional atmosphere hints
        if character_states:
            for char_id, state in character_states.items():
                if hasattr(state, "current_emotion"):
                    emotion = state.current_emotion
                    if hasattr(emotion, "emotion_type"):
                        # Map emotions to atmospheres
                        emotion_atmosphere_map = {
                            "愤怒": AtmosphereType.TENSE,
                            "悲伤": AtmosphereType.SAD,
                            "喜悦": AtmosphereType.HAPPY,
                            "恐惧": AtmosphereType.TENSE,
                            "紧张": AtmosphereType.TENSE,
                        }
                        mapped = emotion_atmosphere_map.get(str(emotion.emotion_type))
                        if mapped:
                            atmosphere = mapped
                            atmosphere_confidence = 0.8

        overall_confidence = (scene_confidence + atmosphere_confidence) / 2

        return SceneAnalysis(
            scene_type=scene_type,
            atmosphere=atmosphere,
            confidence=overall_confidence,
            keywords_matched=scene_keywords_matched,
        )


class SoundLibrary:
    """Manages a library of ambient sounds and background music."""

    # Sound recommendations by scene type
    SCENE_SOUND_MAP = {
        SceneType.INDOOR_DAILY: ("indoor_room_01", None),
        SceneType.INDOOR_TENSE: ("indoor_silent_01", "music_suspense_01"),
        SceneType.OUTDOOR_DAY: ("outdoor_street_day_01", "music_peaceful_01"),
        SceneType.OUTDOOR_NIGHT: ("outdoor_night_01", "music_low_01"),
        SceneType.NATURE_FOREST: ("nature_forest_01", "music_nature_01"),
        SceneType.NATURE_WATER: ("nature_water_01", "music_peaceful_01"),
        SceneType.WEATHER_RAIN: ("weather_rain_01", "music_sad_01"),
        SceneType.WEATHER_SNOW: ("weather_wind_01", "music_pure_01"),
        SceneType.BATTLE: ("ambient_battle_01", "music_battle_01"),
        SceneType.MEMORY: (None, "music_nostalgic_01"),
        SceneType.UNKNOWN: (None, None),
    }

    # Music recommendations by atmosphere
    ATMOSPHERE_MUSIC_MAP = {
        AtmosphereType.TENSE: "music_suspense_01",
        AtmosphereType.SAD: "music_sad_01",
        AtmosphereType.HAPPY: "music_happy_01",
        AtmosphereType.ROMANTIC: "music_romantic_01",
        AtmosphereType.MYSTERIOUS: "music_mysterious_01",
        AtmosphereType.NEUTRAL: "music_peaceful_01",
    }

    def __init__(self, library_path: Optional[str] = None) -> None:
        """Initialize the sound library.

        Args:
            library_path: Path to the sound library directory.
        """
        self.library_path = library_path
        self.ambient_sounds: dict[str, AmbientSound] = {}
        self.background_music: dict[str, BackgroundMusic] = {}

    def add_ambient_sound(self, sound: AmbientSound) -> None:
        """Add an ambient sound to the library.

        Args:
            sound: AmbientSound to add.
        """
        self.ambient_sounds[sound.sound_id] = sound

    def add_background_music(self, music: BackgroundMusic) -> None:
        """Add background music to the library.

        Args:
            music: BackgroundMusic to add.
        """
        self.background_music[music.music_id] = music

    def get_ambient_sound(self, sound_id: str) -> Optional[AmbientSound]:
        """Get an ambient sound by ID.

        Args:
            sound_id: Sound identifier.

        Returns:
            AmbientSound if found, None otherwise.
        """
        return self.ambient_sounds.get(sound_id)

    def get_background_music(self, music_id: str) -> Optional[BackgroundMusic]:
        """Get background music by ID.

        Args:
            music_id: Music identifier.

        Returns:
            BackgroundMusic if found, None otherwise.
        """
        return self.background_music.get(music_id)

    def get_recommended_sound(self, analysis: SceneAnalysis) -> SoundConfig:
        """Get recommended sound configuration for a scene analysis.

        Args:
            analysis: Scene analysis result.

        Returns:
            SoundConfig with recommended sounds.
        """
        # Get scene-based recommendations
        ambient_id, music_id = self.SCENE_SOUND_MAP.get(
            analysis.scene_type, (None, None)
        )

        # Override music with atmosphere-based recommendation if available
        if analysis.atmosphere != AtmosphereType.NEUTRAL:
            music_id = self.ATMOSPHERE_MUSIC_MAP.get(analysis.atmosphere, music_id)

        return SoundConfig(
            ambient_sound=ambient_id,
            background_music=music_id,
            ambient_volume=0.3,
            music_volume=0.15,
        )


class SoundEngine:
    """Main engine for scene-based sound management.

    Coordinates scene recognition, sound matching, and audio mixing
    to provide immersive audio experiences.

    Example usage:
        engine = SoundEngine(library_path="/path/to/sounds")
        analysis = engine.analyze_scene(text, character_states)
        config = engine.match_sound(analysis)
        mixed_audio = engine.mix_audio(voice_audio, config, duration)
    """

    # Default mixing parameters
    DEFAULT_AMBIENT_VOLUME = 0.3
    DEFAULT_MUSIC_VOLUME = 0.15
    DIALOGUE_VOLUME_DUCK = 0.85  # Reduce ambient by 15% during dialogue

    def __init__(self, library_path: Optional[str] = None) -> None:
        """Initialize the sound engine.

        Args:
            library_path: Path to the sound library directory.
        """
        self.recognizer = SceneRecognizer()
        self.library = SoundLibrary(library_path)

    def analyze_scene(
        self,
        text: str,
        character_states: Optional[dict] = None,
    ) -> SceneAnalysis:
        """Analyze a scene to determine its characteristics.

        Args:
            text: Scene text to analyze.
            character_states: Optional character states for context.

        Returns:
            SceneAnalysis with detected characteristics.
        """
        analysis = self.recognizer.analyze(text, character_states)
        config = self.library.get_recommended_sound(analysis)
        analysis.suggested_sounds = [
            s for s in [config.ambient_sound, config.background_music] if s
        ]
        return analysis

    def match_sound(self, analysis: SceneAnalysis) -> SoundConfig:
        """Match sounds to a scene analysis.

        Args:
            analysis: Scene analysis result.

        Returns:
            SoundConfig with matched sounds.
        """
        return self.library.get_recommended_sound(analysis)

    def mix_audio(
        self,
        voice_audio: bytes,
        sound_config: SoundConfig,
        duration: float,
    ) -> bytes:
        """Mix voice audio with background sounds.

        Args:
            voice_audio: Voice audio data.
            sound_config: Sound configuration for mixing.
            duration: Duration of the voice audio in seconds.

        Returns:
            Mixed audio data.
        """
        # For MVP, return the voice audio unchanged
        # In production, would use pydub to mix audio layers:
        # 1. Load voice audio
        # 2. Load ambient sound (if configured)
        # 3. Load background music (if configured)
        # 4. Apply volume levels
        # 5. Apply fade in/out
        # 6. Detect dialogue and duck ambient volume
        # 7. Mix and export

        # Placeholder: just return voice audio
        return voice_audio

    def get_sound_config_for_scene(
        self,
        text: str,
        character_states: Optional[dict] = None,
    ) -> SoundConfig:
        """Convenience method to get sound config for text.

        Combines analyze_scene and match_sound into one call.

        Args:
            text: Scene text to analyze.
            character_states: Optional character states for context.

        Returns:
            SoundConfig for the scene.
        """
        analysis = self.analyze_scene(text, character_states)
        return self.match_sound(analysis)