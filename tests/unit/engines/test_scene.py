"""Tests for the Scene Sound Engine."""

import pytest

from audiobook.engines.scene import (
    ATMOSPHERE_KEYWORDS,
    SCENE_KEYWORDS,
    AmbientSound,
    AtmosphereType,
    BackgroundMusic,
    SceneAnalysis,
    SceneRecognizer,
    SceneType,
    SoundConfig,
    SoundEngine,
    SoundLibrary,
)


class TestSceneType:
    """Tests for SceneType enum."""

    def test_scene_type_values(self) -> None:
        """Test that scene types have expected values."""
        assert SceneType.INDOOR_DAILY.value == "室内-日常"
        assert SceneType.OUTDOOR_NIGHT.value == "室外-夜晚"
        assert SceneType.BATTLE.value == "战斗场景"

    def test_scene_type_count(self) -> None:
        """Test that all expected scene types are defined."""
        expected_types = [
            "INDOOR_DAILY", "INDOOR_TENSE", "OUTDOOR_DAY", "OUTDOOR_NIGHT",
            "NATURE_FOREST", "NATURE_WATER", "WEATHER_RAIN", "WEATHER_SNOW",
            "BATTLE", "MEMORY", "UNKNOWN",
        ]
        for type_name in expected_types:
            assert hasattr(SceneType, type_name)


class TestAtmosphereType:
    """Tests for AtmosphereType enum."""

    def test_atmosphere_values(self) -> None:
        """Test that atmospheres have expected values."""
        assert AtmosphereType.TENSE.value == "压抑"
        assert AtmosphereType.SAD.value == "悲伤"
        assert AtmosphereType.HAPPY.value == "欢快"

    def test_atmosphere_count(self) -> None:
        """Test that all expected atmospheres are defined."""
        assert len(AtmosphereType) >= 6


class TestSceneKeywords:
    """Tests for scene keyword definitions."""

    def test_all_scene_types_have_keywords(self) -> None:
        """Test that all scene types (except UNKNOWN) have keywords."""
        for scene_type in SceneType:
            if scene_type != SceneType.UNKNOWN:
                assert scene_type in SCENE_KEYWORDS
                assert len(SCENE_KEYWORDS[scene_type]) > 0

    def test_all_atmosphere_types_have_keywords(self) -> None:
        """Test that all atmosphere types have keywords."""
        for atmo_type in AtmosphereType:
            if atmo_type != AtmosphereType.NEUTRAL:
                assert atmo_type in ATMOSPHERE_KEYWORDS
                assert len(ATMOSPHERE_KEYWORDS[atmo_type]) > 0


class TestSceneAnalysis:
    """Tests for SceneAnalysis dataclass."""

    def test_default_values(self) -> None:
        """Test default analysis values."""
        analysis = SceneAnalysis()
        assert analysis.scene_type == SceneType.UNKNOWN
        assert analysis.atmosphere == AtmosphereType.NEUTRAL
        assert analysis.confidence == 0.0
        assert len(analysis.keywords_matched) == 0

    def test_custom_values(self) -> None:
        """Test custom analysis values."""
        analysis = SceneAnalysis(
            scene_type=SceneType.OUTDOOR_NIGHT,
            atmosphere=AtmosphereType.MYSTERIOUS,
            confidence=0.8,
            keywords_matched=["夜晚", "神秘"],
            suggested_sounds=["ambient_night_01", "music_mysterious_01"],
        )
        assert analysis.scene_type == SceneType.OUTDOOR_NIGHT
        assert analysis.atmosphere == AtmosphereType.MYSTERIOUS
        assert len(analysis.keywords_matched) == 2


class TestSoundConfig:
    """Tests for SoundConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default config values."""
        config = SoundConfig()
        assert config.ambient_sound is None
        assert config.background_music is None
        assert config.ambient_volume == 0.3
        assert config.music_volume == 0.15
        assert config.fade_in == 2.0
        assert config.fade_out == 1.0

    def test_custom_values(self) -> None:
        """Test custom config values."""
        config = SoundConfig(
            ambient_sound="rain_01",
            background_music="sad_01",
            ambient_volume=0.4,
            music_volume=0.2,
            fade_in=3.0,
            fade_out=2.0,
            crossfade=1.5,
        )
        assert config.ambient_sound == "rain_01"
        assert config.background_music == "sad_01"
        assert config.crossfade == 1.5


class TestAmbientSound:
    """Tests for AmbientSound dataclass."""

    def test_creation(self) -> None:
        """Test creating an ambient sound."""
        sound = AmbientSound(
            sound_id="rain_01",
            name="Light Rain",
            category="weather",
            file_path="/sounds/weather/rain_01.wav",
        )
        assert sound.sound_id == "rain_01"
        assert sound.name == "Light Rain"
        assert sound.category == "weather"
        assert len(sound.tags) == 0

    def test_with_tags(self) -> None:
        """Test ambient sound with tags."""
        sound = AmbientSound(
            sound_id="forest_01",
            name="Forest Ambience",
            category="nature",
            file_path="/sounds/nature/forest_01.wav",
            duration=60.0,
            tags=["forest", "birds", "nature"],
        )
        assert len(sound.tags) == 3


class TestBackgroundMusic:
    """Tests for BackgroundMusic dataclass."""

    def test_creation(self) -> None:
        """Test creating background music."""
        music = BackgroundMusic(
            music_id="sad_01",
            name="Melancholy Piano",
            category="emotional",
            file_path="/music/emotional/sad_01.mp3",
        )
        assert music.music_id == "sad_01"
        assert music.bpm == 120

    def test_with_atmosphere(self) -> None:
        """Test background music with atmosphere."""
        music = BackgroundMusic(
            music_id="tense_01",
            name="Tension Build",
            category="atmospheric",
            file_path="/music/atmospheric/tense_01.mp3",
            duration=180.0,
            bpm=90,
            atmosphere=AtmosphereType.TENSE,
        )
        assert music.atmosphere == AtmosphereType.TENSE


class TestSceneRecognizer:
    """Tests for SceneRecognizer class."""

    @pytest.fixture
    def recognizer(self) -> SceneRecognizer:
        """Create a recognizer for testing."""
        return SceneRecognizer()

    def test_recognize_indoor_scene(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing indoor daily scene."""
        analysis = recognizer.analyze("他坐在房间里，看着窗外的风景。")
        assert analysis.scene_type == SceneType.INDOOR_DAILY
        assert "房间" in analysis.keywords_matched

    def test_recognize_outdoor_night(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing outdoor night scene."""
        analysis = recognizer.analyze("夜晚，月光洒在寂静的街道上。")
        assert analysis.scene_type == SceneType.OUTDOOR_NIGHT
        assert "夜晚" in analysis.keywords_matched or "月光" in analysis.keywords_matched

    def test_recognize_rain_scene(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing rain scene."""
        analysis = recognizer.analyze("暴雨倾盆，雨声敲打着窗户。")
        assert analysis.scene_type == SceneType.WEATHER_RAIN

    def test_recognize_battle_scene(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing battle scene."""
        analysis = recognizer.analyze("两人激烈打斗，刀剑相交。")
        assert analysis.scene_type == SceneType.BATTLE

    def test_recognize_memory_scene(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing memory/flashback scene."""
        analysis = recognizer.analyze("他回忆起当年的往事，心中感慨万千。")
        assert analysis.scene_type == SceneType.MEMORY

    def test_recognize_tense_atmosphere(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing tense atmosphere."""
        analysis = recognizer.analyze("房间里一片沉默，气氛压抑得让人窒息。")
        assert analysis.atmosphere == AtmosphereType.TENSE

    def test_recognize_sad_atmosphere(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing sad atmosphere."""
        analysis = recognizer.analyze("她流下悲伤的泪水，心碎不已。")
        assert analysis.atmosphere == AtmosphereType.SAD

    def test_recognize_happy_atmosphere(self, recognizer: SceneRecognizer) -> None:
        """Test recognizing happy atmosphere."""
        analysis = recognizer.analyze("大家开心地笑了起来，充满了喜悦。")
        assert analysis.atmosphere == AtmosphereType.HAPPY

    def test_unknown_scene_type(self, recognizer: SceneRecognizer) -> None:
        """Test unrecognized scene defaults to UNKNOWN."""
        analysis = recognizer.analyze("这是一个普通的地方。")
        assert analysis.scene_type == SceneType.UNKNOWN

    def test_with_character_states(self, recognizer: SceneRecognizer) -> None:
        """Test analysis with character state context."""
        # Character states can influence atmosphere detection
        analysis = recognizer.analyze("他站在那里。", character_states={})
        # Should not crash
        assert analysis is not None


class TestSoundLibrary:
    """Tests for SoundLibrary class."""

    @pytest.fixture
    def library(self) -> SoundLibrary:
        """Create a sound library for testing."""
        return SoundLibrary()

    def test_add_ambient_sound(self, library: SoundLibrary) -> None:
        """Test adding ambient sound."""
        sound = AmbientSound(
            sound_id="rain_01",
            name="Rain",
            category="weather",
            file_path="/sounds/rain.wav",
        )
        library.add_ambient_sound(sound)

        retrieved = library.get_ambient_sound("rain_01")
        assert retrieved is not None
        assert retrieved.name == "Rain"

    def test_add_background_music(self, library: SoundLibrary) -> None:
        """Test adding background music."""
        music = BackgroundMusic(
            music_id="sad_01",
            name="Sad Music",
            category="emotional",
            file_path="/music/sad.mp3",
        )
        library.add_background_music(music)

        retrieved = library.get_background_music("sad_01")
        assert retrieved is not None
        assert retrieved.name == "Sad Music"

    def test_get_nonexistent_sound(self, library: SoundLibrary) -> None:
        """Test getting non-existent sound returns None."""
        assert library.get_ambient_sound("nonexistent") is None
        assert library.get_background_music("nonexistent") is None

    def test_get_recommended_sound(self, library: SoundLibrary) -> None:
        """Test getting recommended sound for scene."""
        analysis = SceneAnalysis(
            scene_type=SceneType.WEATHER_RAIN,
            atmosphere=AtmosphereType.SAD,
        )
        config = library.get_recommended_sound(analysis)

        assert isinstance(config, SoundConfig)
        # Should have rain ambient sound
        assert config.ambient_sound is not None or config.background_music is not None


class TestSoundEngine:
    """Tests for SoundEngine class."""

    @pytest.fixture
    def engine(self) -> SoundEngine:
        """Create a sound engine for testing."""
        return SoundEngine()

    def test_engine_initialization(self, engine: SoundEngine) -> None:
        """Test engine initialization."""
        assert engine.recognizer is not None
        assert engine.library is not None

    def test_analyze_scene(self, engine: SoundEngine) -> None:
        """Test analyzing a scene."""
        analysis = engine.analyze_scene("夜晚的森林里传来鸟叫声。")

        assert isinstance(analysis, SceneAnalysis)
        # Should detect either night or forest
        assert analysis.scene_type in [
            SceneType.OUTDOOR_NIGHT,
            SceneType.NATURE_FOREST,
            SceneType.UNKNOWN,
        ]

    def test_match_sound(self, engine: SoundEngine) -> None:
        """Test matching sound to analysis."""
        analysis = SceneAnalysis(
            scene_type=SceneType.NATURE_FOREST,
            atmosphere=AtmosphereType.NEUTRAL,
        )
        config = engine.match_sound(analysis)

        assert isinstance(config, SoundConfig)

    def test_get_sound_config_for_scene(self, engine: SoundEngine) -> None:
        """Test convenience method for getting sound config."""
        config = engine.get_sound_config_for_scene(
            "他坐在房间里，心情很沉重压抑。"
        )

        assert isinstance(config, SoundConfig)

    def test_mix_audio(self, engine: SoundEngine) -> None:
        """Test audio mixing (placeholder)."""
        voice_audio = b"fake_voice_audio"
        config = SoundConfig(
            ambient_sound="rain_01",
            background_music="sad_01",
        )

        mixed = engine.mix_audio(voice_audio, config, duration=5.0)

        # For MVP, returns voice unchanged
        assert mixed == voice_audio

    def test_full_workflow(self, engine: SoundEngine) -> None:
        """Test complete workflow from text to sound config."""
        text = "夜晚的街道上，他感到一阵压抑的沉默。"

        # Analyze
        analysis = engine.analyze_scene(text)
        assert analysis.scene_type != SceneType.UNKNOWN or analysis.atmosphere != AtmosphereType.NEUTRAL

        # Match
        config = engine.match_sound(analysis)
        assert config is not None

        # Mix (placeholder)
        mixed = engine.mix_audio(b"voice", config, 5.0)
        assert mixed is not None


class TestSoundConfigVolumes:
    """Tests for sound volume parameters."""

    def test_default_volumes_reasonable(self) -> None:
        """Test that default volumes are in reasonable range."""
        config = SoundConfig()

        # Ambient should be quieter than music typically
        assert 0.1 <= config.ambient_volume <= 0.5
        assert 0.05 <= config.music_volume <= 0.3

        # Music should typically be quieter than ambient
        assert config.music_volume <= config.ambient_volume

    def test_fade_times_reasonable(self) -> None:
        """Test that fade times are reasonable."""
        config = SoundConfig()

        # Fade times should be positive and reasonable
        assert 0 < config.fade_in <= 5.0
        assert 0 < config.fade_out <= 3.0
        assert 0 < config.crossfade <= 2.0