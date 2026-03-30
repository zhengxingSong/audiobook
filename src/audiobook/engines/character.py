"""Character recognition engine for audiobook TTS system.

This module provides character identification, emotion analysis,
and character state tracking functionality.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from audiobook.models import (
    Block,
    Character,
    CharacterImportance,
    CharacterState,
    Emotion,
    EmotionIntensity,
    EmotionProfile,
)


@dataclass
class CharacterResult:
    """Result of character identification from a block.

    Attributes:
        characters: List of identified character names.
        new_characters: List of newly discovered character names.
        confidence: Confidence score for the identification (0.0 to 1.0).
    """

    characters: list[str] = field(default_factory=list)
    new_characters: list[str] = field(default_factory=list)
    confidence: float = 1.0


class CharacterRecognitionEngine:
    """Engine for recognizing characters and analyzing their emotional states.

    This engine identifies characters in text blocks, analyzes emotions
    using keyword detection, classifies character importance, and tracks
    character states throughout the narrative.
    """

    # Emotion keywords mapping (Chinese)
    EMOTION_KEYWORDS: dict[str, list[str]] = {
        "愤怒": ["愤怒", "生气", "怒", "火", "气愤", "暴怒", "恼怒", "发火", "火大"],
        "悲伤": ["悲伤", "难过", "哭", "泪", "伤心", "痛苦", "哀伤", "凄凉", "心碎"],
        "喜悦": ["喜悦", "高兴", "开心", "笑", "快乐", "欢喜", "欣喜", "愉悦", "兴奋"],
        "恐惧": ["恐惧", "害怕", "惊恐", "颤抖", "战栗", "怕", "惶恐", "畏惧", "胆寒"],
        "惊讶": ["惊讶", "吃惊", "意外", "震惊", "愕然", "惊愕", "诧异", "目瞪口呆"],
        "平静": ["平静", "冷静", "淡然", "从容", "镇定", "安宁", "祥和", "沉稳"],
        "厌恶": ["厌恶", "恶心", "厌烦", "讨厌", "反感", "憎恶", "嫌弃"],
        "紧张": ["紧张", "焦虑", "不安", "忐忑", "焦躁", "急切", "心急"],
    }

    # Intensity modifiers - keys match EmotionIntensity enum values
    INTENSITY_MODIFIERS: dict[str, list[str]] = {
        "strong": ["暴怒", "狂怒", "痛哭", "崩溃", "狂笑", "极度", "彻底", "完全",
                   "愤怒", "悲伤", "高兴", "恐惧", "震惊", "非常", "十分", "极其"],
        "moderate": ["有些", "颇为", "相当", "比较"],
        "light": ["微微", "稍微", "略感", "有点", "略微"],
    }

    # Chinese name patterns for character identification
    NAME_PATTERNS = [
        # Quote-based dialogue patterns: "XXX说" or "XXX道"
        r'"([^"]+?)"[，,]?\s*([^\s，。！？""\'\'」」]{1,4})[说道回答喊叫吼道]',
        # Name followed by action/speech verb
        r'([^\s，。！？""\'\'」」]{2,4})(说道|问道|答道|喊道|叫道|怒道|笑道|叹道)',
        # Explicit name mention with quotes
        r'([^\s，。！？""\'\'」」]{2,4})[说道]：["\']([^"\']+)["\']',
        # Subject position patterns
        r'^([^\s，。！？""\'\'」」]{2,4})[的地得]',
        # Name with title/honorific
        r'([^\s，。！？""\'\'」」]{1,2})(先生|女士|小姐|老师|大夫|将军|王爷|公主|皇后)',
    ]

    # Invalid name patterns (common words that should not be treated as names)
    INVALID_NAMES = {
        # Pronouns and common words
        "他", "她", "它", "我", "你", "您", "自己", "大家", "别人",
        # Common verbs
        "说道", "问道", "答道", "想到", "看到", "听到", "知道", "觉得",
        # Common adjectives/adverbs
        "突然", "忽然", "终于", "渐渐", "慢慢", "一直", "正在",
        # Common nouns that might be mistaken
        "时候", "地方", "东西", "事情", "问题", "办法", "样子",
        # Numbers and time
        "一", "二", "三", "今天", "明天", "昨天", "现在", "以后",
    }

    def __init__(self) -> None:
        """Initialize the character recognition engine."""
        self._known_characters: set[str] = set()
        self._character_counts: dict[str, int] = {}

    def identify_characters(
        self,
        block: Block,
        known_characters: Optional[list[str]] = None
    ) -> CharacterResult:
        """Identify characters in a text block.

        Args:
            block: The text block to analyze.
            known_characters: List of previously identified character names.

        Returns:
            CharacterResult with identified and new characters.
        """
        if known_characters is None:
            known_characters = list(self._known_characters)
        else:
            self._known_characters.update(known_characters)

        text = block.text
        identified: set[str] = set()
        new_characters: set[str] = set()

        # Apply each pattern to find potential names
        for pattern in self.NAME_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                # Handle tuple results (multiple capture groups)
                name = match[0] if isinstance(match, tuple) else match

                if self._is_valid_name(name):
                    identified.add(name)

                    # Check if this is a new character
                    if name not in known_characters and name not in self._known_characters:
                        new_characters.add(name)
                        self._known_characters.add(name)

        # Also check dialogues for speakers
        for dialogue in block.dialogues:
            if dialogue.speaker and self._is_valid_name(dialogue.speaker):
                identified.add(dialogue.speaker)
                if dialogue.speaker not in known_characters:
                    new_characters.add(dialogue.speaker)
                    self._known_characters.add(dialogue.speaker)

        # Update character counts
        for name in identified:
            self._character_counts[name] = self._character_counts.get(name, 0) + 1

        # Calculate confidence based on pattern matches
        confidence = min(1.0, len(identified) * 0.3 + 0.5) if identified else 0.5

        return CharacterResult(
            characters=list(identified),
            new_characters=list(new_characters),
            confidence=confidence,
        )

    def analyze_emotion(
        self,
        text: str,
        character: Optional[str] = None,
        context: Optional[dict] = None
    ) -> EmotionProfile:
        """Analyze the emotion in text using keyword detection.

        Args:
            text: The text to analyze for emotions.
            character: Optional character name for context.
            context: Optional context dictionary with additional information.

        Returns:
            EmotionProfile with detected emotion type and intensity.
        """
        detected_emotions: dict[str, int] = {}
        intensity_hints: list[str] = []

        # Check for emotion keywords
        for emotion_type, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    detected_emotions[emotion_type] = detected_emotions.get(emotion_type, 0) + 1
                    intensity_hints.append(keyword)

        # Also check for intensity modifiers in the full text
        for intensity_level, modifiers in self.INTENSITY_MODIFIERS.items():
            for modifier in modifiers:
                if modifier in text:
                    intensity_hints.append(modifier)
                    break  # Only add one modifier per intensity level

        # Determine primary emotion
        if detected_emotions:
            primary_emotion = max(detected_emotions, key=detected_emotions.get)
        else:
            primary_emotion = "平静"

        # Map to Emotion enum
        emotion_mapping = {
            "愤怒": Emotion.ANGRY,
            "悲伤": Emotion.SAD,
            "喜悦": Emotion.HAPPY,
            "恐惧": Emotion.FEARFUL,
            "惊讶": Emotion.SURPRISED,
            "平静": Emotion.CALM,
            "厌恶": Emotion.DISGUSTED,
            "紧张": Emotion.NERVOUS,
        }

        emotion_type = emotion_mapping.get(primary_emotion, Emotion.NEUTRAL)

        # Determine intensity
        intensity = self._detect_intensity(intensity_hints)

        # Generate suggested adjustment
        suggested_adjustment = self._generate_adjustment(primary_emotion, intensity)

        # Build scene context
        scene_context = ""
        if character:
            scene_context = f"Character '{character}' experiencing {primary_emotion}"
        if context:
            scene_context += f" (context: {context.get('scene', 'unknown')})"

        return EmotionProfile(
            emotion_type=emotion_type.value if isinstance(emotion_type, Emotion) else emotion_type,
            intensity=intensity,
            components=list(detected_emotions.keys()),
            scene_context=scene_context,
            suggested_adjustment=suggested_adjustment,
        )

    def classify_importance(
        self,
        character_counts: dict[str, int]
    ) -> dict[str, CharacterImportance]:
        """Classify character importance based on appearance frequency (TF-IDF concept).

        Uses statistical distribution to classify characters into importance levels:
        - Main: Top 10% most frequent characters
        - Supporting: Next 30% of characters
        - Minor: Next 40% of characters
        - Cameo: Bottom 20% least frequent characters

        Args:
            character_counts: Dictionary mapping character names to their appearance counts.

        Returns:
            Dictionary mapping character names to their importance classification.
        """
        if not character_counts:
            return {}

        # Sort characters by count (descending)
        sorted_characters = sorted(
            character_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        total_characters = len(sorted_characters)
        total_appearances = sum(character_counts.values())

        result: dict[str, CharacterImportance] = {}

        for i, (name, count) in enumerate(sorted_characters):
            # Calculate position percentage
            position_pct = i / total_characters

            # Calculate frequency relative to average
            avg_count = total_appearances / total_characters
            frequency_ratio = count / avg_count if avg_count > 0 else 1.0

            # Classify based on position and frequency
            if position_pct < 0.1 or frequency_ratio > 2.0:
                importance = CharacterImportance.PROTAGONIST
            elif position_pct < 0.4 or frequency_ratio > 1.2:
                importance = CharacterImportance.SUPPORTING
            else:
                importance = CharacterImportance.MINOR

            result[name] = importance

        return result

    def update_character_state(
        self,
        character: Character,
        emotion: EmotionProfile,
        event: str
    ) -> Character:
        """Update a character's state based on new emotion and event.

        Args:
            character: The character to update.
            emotion: The new emotion profile.
            event: Description of the event causing the state change.

        Returns:
            Updated Character instance with new state.
        """
        # Create or update character state
        if character.state is None:
            character.state = CharacterState(
                character_id=character.character_id,
                current_emotion=emotion,
            )

        # Update state
        character.state.current_emotion = emotion
        character.emotion = emotion

        # Update history summary
        history_entry = f"{emotion.emotion_type}({event})"
        if character.state.history_summary:
            character.state.history_summary = f"{character.state.history_summary}; {history_entry}"
        else:
            character.state.history_summary = history_entry

        # Adjust consistency score based on emotional continuity
        if character.state.consistency_score > 0:
            # Slight decrease in consistency for each state change
            character.state.consistency_score = max(0.5, character.state.consistency_score - 0.02)

        return character

    def _is_valid_name(self, name: str) -> bool:
        """Check if a string is a valid character name.

        Args:
            name: The string to validate.

        Returns:
            True if the string appears to be a valid character name.
        """
        if not name:
            return False

        # Check length (Chinese names are typically 2-4 characters)
        if len(name) < 1 or len(name) > 6:
            return False

        # Check against invalid names
        if name in self.INVALID_NAMES:
            return False

        # Check if it's only punctuation or numbers
        if re.match(r'^[\d\s\W]+$', name):
            return False

        # Check for common words that are not names
        if name in ['什么', '怎么', '为什么', '哪里', '谁', '哪个']:
            return False

        return True

    def _detect_intensity(self, keywords: list[str]) -> EmotionIntensity:
        """Detect emotion intensity from keywords.

        Scans all keywords and returns the lowest intensity found.
        Low intensity modifiers should take precedence over higher ones.

        Args:
            keywords: List of detected emotion keywords.

        Returns:
            EmotionIntensity level.
        """
        # Check all keywords and find the lowest intensity
        intensity_level = None

        intensity_order = [
            ("light", EmotionIntensity.LIGHT),
            ("moderate", EmotionIntensity.MODERATE),
            ("strong", EmotionIntensity.STRONG),
        ]

        for keyword in keywords:
            for intensity_key, intensity_value in intensity_order:
                if keyword in self.INTENSITY_MODIFIERS.get(intensity_key, []):
                    # Keep the lowest intensity found
                    if intensity_level is None:
                        intensity_level = intensity_value
                    elif intensity_value == EmotionIntensity.LIGHT:
                        # LIGHT always takes precedence
                        intensity_level = EmotionIntensity.LIGHT
                    break  # Break inner loop, continue checking keywords

        return intensity_level if intensity_level else EmotionIntensity.LIGHT

    def _generate_adjustment(
        self,
        emotion_type: str,
        intensity: EmotionIntensity
    ) -> str:
        """Generate voice adjustment suggestion based on emotion and intensity.

        Args:
            emotion_type: The type of emotion detected.
            intensity: The intensity level.

        Returns:
            Suggested voice adjustment string.
        """
        base_adjustments = {
            "愤怒": "speak louder, faster, with harsh tone",
            "悲伤": "speak slower, softer, with melancholic tone",
            "喜悦": "speak with cheerful, upbeat tone",
            "恐惧": "speak with trembling, hesitant voice",
            "惊讶": "speak with raised pitch, sudden bursts",
            "平静": "speak normally, composed tone",
            "厌恶": "speak with dismissive, cold tone",
            "紧张": "speak with rushed, anxious pace",
        }

        base = base_adjustments.get(emotion_type, "normal speaking tone")

        intensity_modifiers = {
            EmotionIntensity.LIGHT: "slightly ",
            EmotionIntensity.MODERATE: "",
            EmotionIntensity.STRONG: "strongly ",
        }

        modifier = intensity_modifiers.get(intensity, "")

        # Apply intensity to the adjustment
        if intensity == EmotionIntensity.LIGHT:
            return f"lightly {base}"
        elif intensity == EmotionIntensity.STRONG:
            return f"strongly {base}"
        else:
            return base

    def reset(self) -> None:
        """Reset the engine state, clearing known characters and counts."""
        self._known_characters.clear()
        self._character_counts.clear()