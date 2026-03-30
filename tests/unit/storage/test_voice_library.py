"""Unit tests for VoiceLibrary storage."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from audiobook.models.voice import Voice
from audiobook.storage.voice_library import VoiceLibrary


@pytest.fixture
def library(temp_dir: Path) -> Generator[VoiceLibrary, None, None]:
    """Create a VoiceLibrary instance for testing with proper cleanup."""
    lib = VoiceLibrary(str(temp_dir / "voice_lib"))
    yield lib
    lib.close()


class TestVoiceLibraryInit:
    """Tests for VoiceLibrary initialization."""

    def test_creates_directory(self, temp_dir: Path) -> None:
        """Test that initialization creates the directory."""
        lib_path = temp_dir / "voice_lib"
        lib = VoiceLibrary(str(lib_path))
        lib.close()

        assert lib_path.exists()
        assert lib_path.is_dir()

    def test_creates_database(self, temp_dir: Path) -> None:
        """Test that initialization creates the database file."""
        lib_path = temp_dir / "voice_lib"
        library = VoiceLibrary(str(lib_path))

        assert library.db_path.exists()
        assert library.db_path.name == "voice_library.db"
        library.close()

    def test_creates_table_and_indexes(self, temp_dir: Path) -> None:
        """Test that initialization creates voices table with indexes."""
        lib_path = temp_dir / "voice_lib"
        library = VoiceLibrary(str(lib_path))
        db_path = library.db_path

        # Check using library's own connection first
        conn = library._get_connection()
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='voices'"
        )
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_voices_gender'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_voices_age_range'"
        )
        assert cursor.fetchone() is not None

        library.close()


class TestVoiceLibraryAdd:
    """Tests for VoiceLibrary.add method."""

    def test_add_voice(self, library: VoiceLibrary) -> None:
        """Test adding a voice to the library."""
        voice = Voice(
            voice_id="v001",
            name="小明",
            gender="男",
            age_range="青年",
        )
        library.add(voice)

        assert library.count() == 1
        retrieved = library.get("v001")
        assert retrieved is not None
        assert retrieved.voice_id == "v001"
        assert retrieved.name == "小明"

    def test_add_voice_with_all_fields(self, library: VoiceLibrary) -> None:
        """Test adding a voice with all fields populated."""
        voice = Voice(
            voice_id="v002",
            name="小红",
            gender="女",
            age_range="少年",
            tags=["温柔", "活泼"],
            description="适合青春小说",
            embedding=[0.1, 0.2, 0.3],
            audio_path="/voices/v002.wav",
        )
        library.add(voice)

        retrieved = library.get("v002")
        assert retrieved is not None
        assert retrieved.tags == ["温柔", "活泼"]
        assert retrieved.description == "适合青春小说"
        assert retrieved.embedding == [0.1, 0.2, 0.3]
        assert retrieved.audio_path == "/voices/v002.wav"

    def test_add_replaces_existing(self, library: VoiceLibrary) -> None:
        """Test that adding a voice with existing ID replaces it."""
        voice1 = Voice(
            voice_id="v001",
            name="小明",
            gender="男",
            age_range="青年",
        )
        library.add(voice1)

        voice2 = Voice(
            voice_id="v001",
            name="小明更新",
            gender="男",
            age_range="中年",
        )
        library.add(voice2)

        assert library.count() == 1
        retrieved = library.get("v001")
        assert retrieved is not None
        assert retrieved.name == "小明更新"
        assert retrieved.age_range == "中年"


class TestVoiceLibraryGet:
    """Tests for VoiceLibrary.get method."""

    def test_get_existing_voice(self, library: VoiceLibrary) -> None:
        """Test retrieving an existing voice."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))

        voice = library.get("v001")

        assert voice is not None
        assert voice.voice_id == "v001"
        assert voice.name == "小明"

    def test_get_nonexistent_voice(self, library: VoiceLibrary) -> None:
        """Test retrieving a non-existent voice returns None."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))

        voice = library.get("nonexistent")

        assert voice is None


class TestVoiceLibraryList:
    """Tests for VoiceLibrary.list method."""

    def test_list_all_voices(self, library: VoiceLibrary) -> None:
        """Test listing all voices without filter."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))
        library.add(Voice(voice_id="v003", name="老张", gender="男", age_range="中年"))
        library.add(Voice(voice_id="v004", name="小芳", gender="女", age_range="青年"))

        voices = library.list()

        assert len(voices) == 4

    def test_list_filter_by_gender(self, library: VoiceLibrary) -> None:
        """Test filtering by gender."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))
        library.add(Voice(voice_id="v003", name="老张", gender="男", age_range="中年"))
        library.add(Voice(voice_id="v004", name="小芳", gender="女", age_range="青年"))

        voices = library.list(gender="男")

        assert len(voices) == 2
        for voice in voices:
            assert voice.gender == "男"

    def test_list_filter_by_age_range(self, library: VoiceLibrary) -> None:
        """Test filtering by age range."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))
        library.add(Voice(voice_id="v003", name="老张", gender="男", age_range="中年"))
        library.add(Voice(voice_id="v004", name="小芳", gender="女", age_range="青年"))

        voices = library.list(age_range="青年")

        assert len(voices) == 2
        for voice in voices:
            assert voice.age_range == "青年"

    def test_list_filter_by_both(self, library: VoiceLibrary) -> None:
        """Test filtering by both gender and age range."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))
        library.add(Voice(voice_id="v003", name="老张", gender="男", age_range="中年"))
        library.add(Voice(voice_id="v004", name="小芳", gender="女", age_range="青年"))

        voices = library.list(gender="女", age_range="青年")

        assert len(voices) == 1
        assert voices[0].voice_id == "v004"

    def test_list_empty_result(self, library: VoiceLibrary) -> None:
        """Test filtering with no matches."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))

        voices = library.list(gender="中性")

        assert len(voices) == 0


class TestVoiceLibrarySearchByTags:
    """Tests for VoiceLibrary.search_by_tags method."""

    def test_search_single_tag(self, library: VoiceLibrary) -> None:
        """Test searching with a single tag."""
        library.add(Voice(
            voice_id="v001",
            name="温柔男声",
            gender="男",
            age_range="青年",
            tags=["温柔", "知性"],
        ))
        library.add(Voice(
            voice_id="v002",
            name="活泼女声",
            gender="女",
            age_range="少年",
            tags=["活泼", "可爱"],
        ))
        library.add(Voice(
            voice_id="v003",
            name="沉稳男声",
            gender="男",
            age_range="中年",
            tags=["沉稳", "知性", "成熟"],
        ))

        voices = library.search_by_tags(["温柔"])

        assert len(voices) == 1
        assert voices[0].voice_id == "v001"

    def test_search_multiple_tags_or_logic(self, library: VoiceLibrary) -> None:
        """Test searching with multiple tags uses OR logic."""
        library.add(Voice(
            voice_id="v001",
            name="温柔男声",
            gender="男",
            age_range="青年",
            tags=["温柔", "知性"],
        ))
        library.add(Voice(
            voice_id="v002",
            name="活泼女声",
            gender="女",
            age_range="少年",
            tags=["活泼", "可爱"],
        ))
        library.add(Voice(
            voice_id="v003",
            name="沉稳男声",
            gender="男",
            age_range="中年",
            tags=["沉稳", "知性", "成熟"],
        ))

        voices = library.search_by_tags(["温柔", "活泼"])

        assert len(voices) == 2
        voice_ids = {v.voice_id for v in voices}
        assert voice_ids == {"v001", "v002"}

    def test_search_matching_multiple_tags(self, library: VoiceLibrary) -> None:
        """Test that a voice with any matching tag is returned."""
        library.add(Voice(
            voice_id="v001",
            name="温柔男声",
            gender="男",
            age_range="青年",
            tags=["温柔", "知性"],
        ))
        library.add(Voice(
            voice_id="v002",
            name="活泼女声",
            gender="女",
            age_range="少年",
            tags=["活泼", "可爱"],
        ))
        library.add(Voice(
            voice_id="v003",
            name="沉稳男声",
            gender="男",
            age_range="中年",
            tags=["沉稳", "知性", "成熟"],
        ))

        voices = library.search_by_tags(["知性"])

        assert len(voices) == 2
        voice_ids = {v.voice_id for v in voices}
        assert voice_ids == {"v001", "v003"}

    def test_search_no_matches(self, library: VoiceLibrary) -> None:
        """Test searching with no matching tags."""
        library.add(Voice(
            voice_id="v001",
            name="温柔男声",
            gender="男",
            age_range="青年",
            tags=["温柔", "知性"],
        ))

        voices = library.search_by_tags(["不存在的标签"])

        assert len(voices) == 0

    def test_search_empty_tags(self, library: VoiceLibrary) -> None:
        """Test searching with empty tag list returns empty."""
        library.add(Voice(
            voice_id="v001",
            name="温柔男声",
            gender="男",
            age_range="青年",
            tags=["温柔", "知性"],
        ))

        voices = library.search_by_tags([])

        assert len(voices) == 0


class TestVoiceLibraryDelete:
    """Tests for VoiceLibrary.delete method."""

    def test_delete_existing_voice(self, library: VoiceLibrary) -> None:
        """Test deleting an existing voice."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))

        assert library.count() == 1

        library.delete("v001")

        assert library.count() == 0
        assert library.get("v001") is None

    def test_delete_nonexistent_voice(self, library: VoiceLibrary) -> None:
        """Test deleting a non-existent voice does not raise."""
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))

        # Should not raise
        library.delete("nonexistent")

        assert library.count() == 1


class TestVoiceLibraryUpdate:
    """Tests for VoiceLibrary.update method."""

    def test_update_existing_voice(self, library: VoiceLibrary) -> None:
        """Test updating an existing voice."""
        library.add(Voice(
            voice_id="v001",
            name="小明",
            gender="男",
            age_range="青年",
            tags=["活泼"],
        ))

        updated = Voice(
            voice_id="v001",
            name="小明更新",
            gender="男",
            age_range="中年",
            tags=["沉稳"],
        )

        library.update(updated)

        retrieved = library.get("v001")
        assert retrieved is not None
        assert retrieved.name == "小明更新"
        assert retrieved.age_range == "中年"
        assert retrieved.tags == ["沉稳"]

    def test_update_nonexistent_voice_adds_it(self, library: VoiceLibrary) -> None:
        """Test updating non-existent voice adds it (UPSERT behavior)."""
        library.add(Voice(
            voice_id="v001",
            name="小明",
            gender="男",
            age_range="青年",
            tags=["活泼"],
        ))

        new_voice = Voice(
            voice_id="v002",
            name="新音色",
            gender="女",
            age_range="青年",
        )

        library.update(new_voice)

        assert library.count() == 2
        retrieved = library.get("v002")
        assert retrieved is not None
        assert retrieved.name == "新音色"


class TestVoiceLibraryCount:
    """Tests for VoiceLibrary.count method."""

    def test_count_empty_library(self, temp_dir: Path) -> None:
        """Test counting empty library."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))

        assert library.count() == 0
        library.close()

    def test_count_with_voices(self, temp_dir: Path) -> None:
        """Test counting voices in library."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))

        assert library.count() == 2
        library.close()

    def test_count_after_delete(self, temp_dir: Path) -> None:
        """Test count after deletion."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        library.add(Voice(voice_id="v001", name="小明", gender="男", age_range="青年"))
        library.add(Voice(voice_id="v002", name="小红", gender="女", age_range="少年"))
        library.delete("v001")

        assert library.count() == 1
        library.close()


class TestVoiceLibraryEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_voice_with_empty_tags(self, temp_dir: Path) -> None:
        """Test voice with empty tags list."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        voice = Voice(
            voice_id="v001",
            name="无标签",
            gender="中性",
            age_range="成年",
            tags=[],
        )

        library.add(voice)

        retrieved = library.get("v001")
        assert retrieved is not None
        assert retrieved.tags == []
        library.close()

    def test_voice_with_special_characters(self, temp_dir: Path) -> None:
        """Test voice with special characters in fields."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        voice = Voice(
            voice_id="v001",
            name="测试'引号\"和特殊字符",
            gender="男",
            age_range="青年",
            description="包含\n换行和\t制表符",
        )

        library.add(voice)

        retrieved = library.get("v001")
        assert retrieved is not None
        assert "引号" in retrieved.name
        assert "换行" in retrieved.description
        library.close()

    def test_voice_with_unicode(self, temp_dir: Path) -> None:
        """Test voice with unicode characters."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        voice = Voice(
            voice_id="v001",
            name="🎵音乐之声🎭",
            gender="女",
            age_range="青年",
            tags=["🎵", "动感"],
        )

        library.add(voice)

        retrieved = library.get("v001")
        assert retrieved is not None
        assert "🎵" in retrieved.name
        assert "🎵" in retrieved.tags
        library.close()

    def test_voice_with_none_embedding(self, temp_dir: Path) -> None:
        """Test voice with None embedding."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        voice = Voice(
            voice_id="v001",
            name="无embedding",
            gender="男",
            age_range="成年",
            embedding=None,
        )

        library.add(voice)

        retrieved = library.get("v001")
        assert retrieved is not None
        assert retrieved.embedding is None
        library.close()

    def test_voice_with_large_embedding(self, temp_dir: Path) -> None:
        """Test voice with large embedding vector."""
        library = VoiceLibrary(str(temp_dir / "voice_lib"))
        # Simulate a realistic embedding size (e.g., 256 dimensions)
        embedding = [0.1] * 256
        voice = Voice(
            voice_id="v001",
            name="大向量",
            gender="女",
            age_range="成年",
            embedding=embedding,
        )

        library.add(voice)

        retrieved = library.get("v001")
        assert retrieved is not None
        assert len(retrieved.embedding) == 256
        assert all(v == 0.1 for v in retrieved.embedding)
        library.close()