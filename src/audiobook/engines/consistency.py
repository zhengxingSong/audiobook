"""Voice consistency controller for maintaining uniform voice characteristics.

This module provides consistency tracking and enforcement to ensure
that the same character maintains similar voice characteristics across
different fragments throughout the audiobook.

Core components:
- VoiceProfile: Character voice characteristics profile
- ConsistencyController: Profile management and consistency checking
- Audio feature extraction for voice comparison
- Emotion offset calculation for synthesis parameter adjustment
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import numpy as np

from audiobook.models.character import Character, CharacterState, EmotionProfile, EmotionType
from audiobook.models.fragment import AudioFragment
from audiobook.models.voice import VoiceParams


# Emotion offset table for synthesis parameter adjustment
EMOTION_OFFSETS = {
    "愤怒": {"语速": 0.2, "音调": 0.15, "力度": 0.3},
    "悲伤": {"语速": -0.15, "音调": -0.1, "力度": -0.2},
    "喜悦": {"语速": 0.1, "音调": 0.1, "力度": 0.1},
    "恐惧": {"语速": -0.1, "音调": 0.05, "力度": -0.1},
    "平静": {"语速": 0.0, "音调": 0.0, "力度": 0.0},
    "紧张": {"语速": 0.15, "音调": 0.05, "力度": 0.1},
    "neutral": {"语速": 0.0, "音调": 0.0, "力度": 0.0},
    "happy": {"语速": 0.1, "音调": 0.1, "力度": 0.1},
    "sad": {"语速": -0.15, "音调": -0.1, "力度": -0.2},
    "angry": {"语速": 0.2, "音调": 0.15, "力度": 0.3},
    "fearful": {"语速": -0.1, "音调": 0.05, "力度": -0.1},
    "surprised": {"语速": 0.05, "音调": 0.1, "力度": 0.05},
    "excited": {"语速": 0.15, "音调": 0.1, "力度": 0.15},
    "calm": {"语速": -0.05, "音调": -0.05, "力度": -0.05},
    "nervous": {"语速": 0.1, "音调": 0.05, "力度": 0.05},
}


@dataclass
class VoiceFeatureAnchors:
    """Voice feature anchors for consistency tracking.

    These are characteristic patterns that define a character's voice.

    Attributes:
        sentence_end_pattern: Pattern at sentence endings (e.g., "微下沉").
        emphasis_pattern: How emphasized words are spoken.
        pause_pattern: Typical pause patterns.
        tone_pattern: Overall tone characteristics.
    """

    sentence_end_pattern: str = ""
    emphasis_pattern: str = ""
    pause_pattern: str = ""
    tone_pattern: str = ""


@dataclass
class VoiceProfile:
    """Character voice characteristics profile for consistency control.

    Maintains a profile of voice characteristics to ensure the same character
    maintains similar voice qualities across different fragments.

    Attributes:
        character_id: Unique identifier for the character.
        base_voice_id: Reference voice ID from the voice library.
        base_speed: Base speaking speed (1.0 = normal).
        base_pitch: Pitch category ("高", "中", "低", "中性").
        feature_anchors: Characteristic voice patterns.
        history_samples: List of audio fragment IDs used as reference.
        consistency_score: Current consistency score (0.0 to 1.0).
        created_at: When this profile was created.
        updated_at: When this profile was last updated.
    """

    character_id: str
    base_voice_id: str
    base_speed: float = 1.0
    base_pitch: str = "中性"
    feature_anchors: VoiceFeatureAnchors = field(default_factory=VoiceFeatureAnchors)
    history_samples: list[str] = field(default_factory=list)
    consistency_score: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_sample(self, fragment_id: str) -> None:
        """Add a new audio fragment as a reference sample.

        Args:
            fragment_id: ID of the audio fragment to add.
        """
        if fragment_id not in self.history_samples:
            self.history_samples.append(fragment_id)
            # Keep only the last 5 samples for efficiency
            if len(self.history_samples) > 5:
                self.history_samples = self.history_samples[-5:]
            self.updated_at = datetime.now()

    def update_score(self, new_score: float) -> None:
        """Update the consistency score.

        Args:
            new_score: New consistency score (0.0 to 1.0).
        """
        self.consistency_score = max(0.0, min(1.0, new_score))
        self.updated_at = datetime.now()


@dataclass
class SynthesisParams:
    """Synthesis parameters adjusted for consistency.

    These parameters are passed to the TTS engine for voice synthesis.

    Attributes:
        speed: Speaking speed multiplier.
        pitch: Pitch adjustment value.
        volume: Volume/power multiplier.
        emotion_type: Emotion type for synthesis.
        reference_audio: Path to reference audio for voice cloning.
    """

    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    emotion_type: str = "neutral"
    reference_audio: Optional[str] = None


@dataclass
class ConsistencyResult:
    """Result of a consistency check between two audio fragments.

    Attributes:
        is_consistent: Whether the fragments are considered consistent.
        similarity_score: Similarity score (0.0 to 1.0).
        threshold: Threshold used for the check.
        warnings: List of consistency warnings.
        features_compared: Features that were compared.
    """

    is_consistent: bool
    similarity_score: float
    threshold: float = 0.75
    warnings: list[str] = field(default_factory=list)
    features_compared: list[str] = field(default_factory=list)


class ConsistencyController:
    """Controller for maintaining voice consistency across fragments.

    This class manages voice profiles for characters and ensures that
    the same character maintains similar voice characteristics throughout
    the audiobook.

    Core functionality:
    - Create and manage voice profiles for characters
    - Calculate adjusted synthesis parameters based on emotion
    - Check consistency between new fragments and historical samples
    - Select appropriate reference audio for GPT-SoVITS

    Example usage:
        controller = ConsistencyController(storage_path="/path/to/profiles")
        profile = controller.get_profile("char_zhangsan")
        params = controller.calculate_adjusted_params("char_zhangsan", emotion)
        result = controller.check_consistency("char_zhangsan", new_fragment)
    """

    # Minimum similarity threshold for consistency
    MIN_SIMILARITY_THRESHOLD = 0.75

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the consistency controller.

        Args:
            storage_path: Path to store voice profiles. If None, profiles
                          are only kept in memory.
        """
        self.profiles: dict[str, VoiceProfile] = {}
        self.audio_samples: dict[str, AudioFragment] = {}
        self.storage_path = Path(storage_path) if storage_path else None

        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    def get_profile(self, character_id: str) -> Optional[VoiceProfile]:
        """Get the voice profile for a character.

        Args:
            character_id: Unique identifier for the character.

        Returns:
            VoiceProfile if exists, None otherwise.
        """
        return self.profiles.get(character_id)

    def create_profile(
        self,
        character_id: str,
        base_voice_id: str,
        base_speed: float = 1.0,
        base_pitch: str = "中性",
    ) -> VoiceProfile:
        """Create a new voice profile for a character.

        Args:
            character_id: Unique identifier for the character.
            base_voice_id: Reference voice ID from the voice library.
            base_speed: Base speaking speed.
            base_pitch: Pitch category.

        Returns:
            The newly created VoiceProfile.
        """
        profile = VoiceProfile(
            character_id=character_id,
            base_voice_id=base_voice_id,
            base_speed=base_speed,
            base_pitch=base_pitch,
        )
        self.profiles[character_id] = profile
        return profile

    def update_profile(
        self,
        character_id: str,
        fragment: AudioFragment,
        similarity_score: float = 1.0,
    ) -> None:
        """Update a character's voice profile with a new sample.

        Args:
            character_id: Unique identifier for the character.
            fragment: Audio fragment to add as reference.
            similarity_score: How similar this fragment is to existing samples.
        """
        profile = self.get_profile(character_id)
        if profile is None:
            return

        # Add fragment to samples
        self.audio_samples[fragment.fragment_id] = fragment
        profile.add_sample(fragment.fragment_id)

        # Update consistency score based on similarity
        if similarity_score < self.MIN_SIMILARITY_THRESHOLD:
            new_score = profile.consistency_score * 0.95  # Decrease slightly
        else:
            # Increase score slightly if high similarity
            new_score = min(1.0, profile.consistency_score + 0.02)
        profile.update_score(new_score)

    def calculate_adjusted_params(
        self,
        character_id: str,
        emotion: Union[EmotionProfile, EmotionType, str],
    ) -> SynthesisParams:
        """Calculate synthesis parameters adjusted for emotion and consistency.

        Uses the emotion offset table and consistency constraints to
        determine final synthesis parameters.

        Args:
            character_id: Unique identifier for the character.
            emotion: Current emotional state (EmotionProfile, EmotionType, or str).

        Returns:
            SynthesisParams for TTS synthesis.
        """
        profile = self.get_profile(character_id)

        # Get base parameters
        if profile:
            base_speed = profile.base_speed
            consistency_weight = min(profile.consistency_score, 0.9)
        else:
            base_speed = 1.0
            consistency_weight = 0.9

        # Determine emotion type
        if isinstance(emotion, EmotionProfile):
            emotion_type = emotion.emotion_type
            intensity = emotion.intensity
        elif isinstance(emotion, EmotionType):
            emotion_type = emotion.value
            intensity = 1.0  # Default moderate intensity
        else:
            emotion_type = str(emotion)
            intensity = 1.0

        # Get emotion offsets
        offsets = EMOTION_OFFSETS.get(emotion_type, EMOTION_OFFSETS["neutral"])

        # Calculate intensity multiplier
        intensity_map = {"轻度": 0.5, "中度": 1.0, "强烈": 1.5}
        if hasattr(intensity, "value"):
            intensity_value = intensity_map.get(intensity.value, 1.0)
        else:
            intensity_value = 1.0

        # Calculate final parameters with consistency constraint
        speed = base_speed * (1 + offsets["语速"] * intensity_value) * consistency_weight
        pitch = offsets["音调"] * intensity_value * consistency_weight
        volume = 1.0 * (1 + offsets["力度"] * intensity_value) * consistency_weight

        # Clamp values to reasonable ranges
        speed = max(0.5, min(2.0, speed))
        pitch = max(-0.5, min(0.5, pitch))
        volume = max(0.5, min(1.5, volume))

        # Get reference audio if available
        reference_audio = self.get_reference_audio(character_id)

        return SynthesisParams(
            speed=speed,
            pitch=pitch,
            volume=volume,
            emotion_type=emotion_type,
            reference_audio=reference_audio,
        )

    def check_consistency(
        self,
        character_id: str,
        new_fragment: AudioFragment,
        threshold: float = 0.75,
    ) -> ConsistencyResult:
        """Check if a new fragment is consistent with historical samples.

        Compares audio features of the new fragment with historical samples
        for the character to detect potential consistency issues.

        Args:
            character_id: Unique identifier for the character.
            new_fragment: The new audio fragment to check.
            threshold: Minimum similarity score required.

        Returns:
            ConsistencyResult with similarity score and warnings.
        """
        profile = self.get_profile(character_id)
        if profile is None or len(profile.history_samples) == 0:
            return ConsistencyResult(
                is_consistent=True,
                similarity_score=1.0,
                threshold=threshold,
                warnings=["No historical samples to compare"],
                features_compared=[],
            )

        # Store the fragment for comparison
        self.audio_samples[new_fragment.fragment_id] = new_fragment

        # Extract features from new fragment
        new_features = self._extract_features(new_fragment)

        # Compare with historical samples
        similarities = []
        for sample_id in profile.history_samples[-3:]:  # Compare with last 3 samples
            sample = self.audio_samples.get(sample_id)
            if sample:
                sample_features = self._extract_features(sample)
                similarity = self._calculate_similarity(new_features, sample_features)
                similarities.append(similarity)

        # Calculate average similarity
        avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0

        # Determine consistency
        is_consistent = avg_similarity >= threshold

        # Generate warnings if not consistent
        warnings = []
        if not is_consistent:
            warnings.append(
                f"一致性得分 {avg_similarity:.2f} < 阈值 {threshold}"
            )
            if avg_similarity < 0.5:
                warnings.append("严重偏离历史样本，建议人工确认")

        return ConsistencyResult(
            is_consistent=is_consistent,
            similarity_score=avg_similarity,
            threshold=threshold,
            warnings=warnings,
            features_compared=["pitch", "energy", "tempo"],
        )

    def get_reference_audio(self, character_id: str) -> Optional[str]:
        """Get the best reference audio for a character.

        Selects the most representative sample from historical samples
        for use with GPT-SoVITS voice cloning.

        Args:
            character_id: Unique identifier for the character.

        Returns:
            Path to the reference audio file, or None if no samples available.
        """
        profile = self.get_profile(character_id)
        if profile is None or len(profile.history_samples) == 0:
            return None

        # Get the most recent high-quality sample
        # For now, just return the last sample
        last_sample_id = profile.history_samples[-1]
        sample = self.audio_samples.get(last_sample_id)

        if sample and sample.audio_path:
            return sample.audio_path

        return None

    def _extract_features(self, fragment: AudioFragment) -> dict:
        """Extract audio features from a fragment for comparison.

        Args:
            fragment: Audio fragment to extract features from.

        Returns:
            Dictionary of extracted features.
        """
        # For MVP, use simple feature extraction
        # In production, would use librosa for actual audio analysis

        features = {
            "pitch_mean": fragment.pitch or 0.0,
            "pitch_std": 0.1,  # Placeholder
            "energy_mean": fragment.volume or 1.0,
            "tempo": 120.0,  # Placeholder BPM
            "duration": fragment.duration or 0.0,
        }

        # If we have actual audio data, we could extract real features
        # using librosa here in production

        return features

    def _calculate_similarity(
        self,
        features1: dict,
        features2: dict,
    ) -> float:
        """Calculate similarity between two feature sets.

        Uses weighted Euclidean distance to compare features.

        Args:
            features1: First feature set.
            features2: Second feature set.

        Returns:
            Similarity score (0.0 to 1.0).
        """
        # Define weights for each feature
        weights = {
            "pitch_mean": 0.3,
            "energy_mean": 0.3,
            "tempo": 0.2,
            "pitch_std": 0.1,
            "duration": 0.1,
        }

        total_distance = 0.0
        for key, weight in weights.items():
            v1 = features1.get(key, 0.0)
            v2 = features2.get(key, 0.0)

            # Normalize and calculate distance
            # Use relative difference for most features
            if v1 + v2 > 0:
                diff = abs(v1 - v2) / (v1 + v2)
            else:
                diff = 0.0

            total_distance += weight * diff

        # Convert distance to similarity (inverse relationship)
        similarity = 1.0 - min(1.0, total_distance)

        return similarity

    def reset(self) -> None:
        """Reset all profiles and samples."""
        self.profiles.clear()
        self.audio_samples.clear()


def extract_voice_features(audio_path: str) -> dict:
    """Extract voice features from an audio file.

    Production implementation would use librosa for actual feature extraction.

    Args:
        audio_path: Path to the audio file.

    Returns:
        Dictionary of extracted features including:
        - pitch_mean: Mean pitch value
        - pitch_std: Pitch standard deviation
        - energy_mean: Mean energy/RMS
        - tempo: Estimated tempo
        - mfcc_mean: MFCC coefficients mean
    """
    # Placeholder for MVP - returns mock features
    # In production, would use:
    # import librosa
    # y, sr = librosa.load(audio_path)
    # return {
    #     "pitch_mean": float(np.mean(librosa.yin(y, fmin=80, fmax=400))),
    #     "pitch_std": float(np.std(librosa.yin(y, fmin=80, fmax=400))),
    #     "energy_mean": float(np.mean(librosa.feature.rms(y=y))),
    #     "tempo": float(librosa.beat.tempo(y=y, sr=sr)[0]),
    #     "mfcc_mean": librosa.feature.mfcc(y=y, sr=sr).mean(axis=1).tolist(),
    # }

    return {
        "pitch_mean": 150.0,
        "pitch_std": 20.0,
        "energy_mean": 0.5,
        "tempo": 120.0,
        "mfcc_mean": [0.0] * 13,
    }