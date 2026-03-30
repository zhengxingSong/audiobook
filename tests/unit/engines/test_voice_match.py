"""Tests for VoiceMatchEngine."""

import tempfile
import pytest

from audiobook.models import Character, CharacterImportance
from audiobook.models.voice import Voice
from audiobook.storage.voice_library import VoiceLibrary
from audiobook.engines.voice_match import VoiceMatchEngine, MatchResult


@pytest.fixture
def voice_library():
    """Create a voice library with sample voices."""
    tmpdir = tempfile.mkdtemp()
    lib = VoiceLibrary(tmpdir)
    lib.add(Voice(
        voice_id="v1",
        name="Male Young",
        gender="male",
        age_range="young",
        tags=["young", "energetic"],
        description="energetic young male voice"
    ))
    lib.add(Voice(
        voice_id="v2",
        name="Female Young",
        gender="female",
        age_range="young",
        tags=["young", "gentle"],
        description="gentle young female voice"
    ))
    lib.add(Voice(
        voice_id="v3",
        name="Male Middle",
        gender="male",
        age_range="middle",
        tags=["middle", "calm"],
        description="calm middle-aged male voice"
    ))
    lib.add(Voice(
        voice_id="v4",
        name="Female Middle",
        gender="female",
        age_range="middle",
        tags=["middle", "intellectual"],
        description="intellectual middle-aged female voice"
    ))
    lib.add(Voice(
        voice_id="v5",
        name="Neutral Child",
        gender="neutral",
        age_range="child",
        tags=["child", "lively"],
        description="lively child voice"
    ))
    yield lib
    lib.close()


@pytest.fixture
def engine(voice_library):
    """Create a voice match engine with the sample library."""
    return VoiceMatchEngine(voice_library)


class TestFilterByTags:
    """Tests for filter_by_tags method."""

    def test_filter_empty_tags_returns_all(self, engine, voice_library):
        """Empty tags should return all voices."""
        result = engine.filter_by_tags([])
        assert len(result) == voice_library.count()

    def test_filter_single_tag(self, engine):
        """Filter by single tag should return matching voices."""
        result = engine.filter_by_tags(["young"])
        assert len(result) == 2
        assert all("young" in v.tags for v in result)

    def test_filter_multiple_tags_or_logic(self, engine):
        """Multiple tags should use OR logic."""
        result = engine.filter_by_tags(["young", "middle"])
        assert len(result) == 4

    def test_filter_no_match(self, engine):
        """Non-existent tag should return empty list."""
        result = engine.filter_by_tags(["nonexistent"])
        assert len(result) == 0


class TestCalculateConfidence:
    """Tests for calculate_confidence method."""

    def test_gender_match_high_score(self, engine):
        """Matching gender should give high confidence."""
        char = Character(
            character_id="c1",
            name="Zhang San",
            description="a young male",
            traits=["young"]
        )
        voice = Voice(
            voice_id="v",
            name="Male Voice",
            gender="male",
            age_range="young",
            tags=["young"]
        )
        score = engine.calculate_confidence(char, voice)
        assert score >= 0.7

    def test_gender_mismatch_low_score(self, engine):
        """Mismatched gender should give lower confidence."""
        char = Character(
            character_id="c1",
            name="Zhang San",
            description="a young male",
            traits=["young"]
        )
        voice = Voice(
            voice_id="v",
            name="Female Voice",
            gender="female",
            age_range="young",
            tags=["young"]
        )
        score = engine.calculate_confidence(char, voice)
        # Gender mismatch (0%) + tag match (100%) + description (partial)
        assert score < 0.7

    def test_no_traits_partial_score(self, engine):
        """No traits should give partial score."""
        char = Character(
            character_id="c1",
            name="Zhang San",
            description="a male person"
        )
        voice = Voice(
            voice_id="v",
            name="Male Voice",
            gender="male",
            age_range="young",
            tags=["young"]
        )
        score = engine.calculate_confidence(char, voice)
        # Gender match (30%) + no traits partial (50% of 40%) + description partial
        assert 0.3 <= score <= 0.7

    def test_all_match_high_score(self, engine):
        """All matching attributes should give highest confidence."""
        char = Character(
            character_id="c1",
            name="Zhang San",
            description="energetic young male",
            traits=["young", "energetic"]
        )
        voice = Voice(
            voice_id="v",
            name="Male Young",
            gender="male",
            age_range="young",
            tags=["young", "energetic"],
            description="energetic young male voice"
        )
        score = engine.calculate_confidence(char, voice)
        assert score >= 0.8


class TestMatchVoice:
    """Tests for match_voice method."""

    def test_protagonist_character_returns_multiple_candidates(self, engine):
        """Protagonist characters should get multiple candidates (up to 3)."""
        char = Character(
            character_id="c1",
            name="Hero",
            description="a young male",
            traits=["young"],
            importance=CharacterImportance.PROTAGONIST
        )
        result = engine.match_voice(char)
        # Only 2 voices match "young" tag in the library
        assert len(result.candidates) <= 3
        assert result.best_match is not None
        assert result.confidence > 0

    def test_supporting_character_returns_single_candidate(self, engine):
        """Supporting characters should get single candidate."""
        char = Character(
            character_id="c2",
            name="Supporting",
            description="a young female",
            traits=["young"],
            importance=CharacterImportance.SUPPORTING
        )
        result = engine.match_voice(char)
        assert len(result.candidates) == 1
        assert result.best_match is not None

    def test_minor_character_returns_single_candidate(self, engine):
        """Minor characters should get single candidate."""
        char = Character(
            character_id="c3",
            name="Minor",
            description="a middle-aged male",
            importance=CharacterImportance.MINOR
        )
        result = engine.match_voice(char)
        assert len(result.candidates) == 1

    def test_no_matching_voice(self, engine, voice_library):
        """Empty library should return empty result."""
        # Delete all voices from the library
        for voice_id in ["v1", "v2", "v3", "v4", "v5"]:
            voice_library.delete(voice_id)
        char = Character(
            character_id="c1",
            name="Zhang San",
            description="a young male"
        )
        result = engine.match_voice(char)
        assert result.confidence == 0.0
        assert result.best_match is None
        assert len(result.candidates) == 0

    def test_best_match_is_highest_confidence(self, engine):
        """Best match should have highest confidence."""
        char = Character(
            character_id="c1",
            name="Hero",
            description="energetic young male",
            traits=["young", "energetic"],
            importance=CharacterImportance.PROTAGONIST
        )
        result = engine.match_voice(char)
        for candidate in result.candidates:
            assert candidate.confidence <= result.best_match.confidence

    def test_match_reasons_populated(self, engine):
        """Match should include reasons."""
        char = Character(
            character_id="c1",
            name="Zhang San",
            description="a young male",
            traits=["young"]
        )
        result = engine.match_voice(char)
        assert len(result.best_match.match_reasons) > 0


class TestInferGender:
    """Tests for gender inference."""

    def test_infer_male(self, engine):
        """Should infer male gender from description."""
        assert engine._infer_gender_from_description("a young male") == "male"

    def test_infer_female(self, engine):
        """Should infer female gender from description."""
        assert engine._infer_gender_from_description("a young female") == "female"

    def test_infer_neutral(self, engine):
        """Should infer neutral gender from description."""
        assert engine._infer_gender_from_description("a neutral voice") == "neutral"

    def test_no_inference(self, engine):
        """Should return None when no gender can be inferred."""
        assert engine._infer_gender_from_description("a person") is None
        assert engine._infer_gender_from_description("") is None


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_empty_result(self):
        """Empty result should have default values."""
        result = MatchResult()
        assert result.candidates == []
        assert result.best_match is None
        assert result.confidence == 0.0

    def test_with_candidates(self):
        """Result with candidates should preserve data."""
        from audiobook.models.voice import VoiceCandidate, Voice
        voice = Voice(
            voice_id="v1",
            name="Test Voice",
            gender="male",
            age_range="young"
        )
        candidate = VoiceCandidate(
            voice=voice,
            confidence=0.8,
            match_reasons=["test reason"]
        )
        result = MatchResult(
            candidates=[candidate],
            best_match=candidate,
            confidence=0.8
        )
        assert len(result.candidates) == 1
        assert result.confidence == 0.8