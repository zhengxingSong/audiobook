"""音色匹配引擎 - 三层筛选策略."""

from dataclasses import dataclass, field
from typing import Optional

from audiobook.models import Character, CharacterImportance, EmotionProfile
from audiobook.models.voice import Voice, VoiceCandidate
from audiobook.storage.voice_library import VoiceLibrary


@dataclass
class MatchResult:
    candidates: list[VoiceCandidate] = field(default_factory=list)
    best_match: Optional[VoiceCandidate] = None
    confidence: float = 0.0


class VoiceMatchEngine:
    GENDER_KEYWORDS = {
        "female": ["female", "woman", "girl", "she", "lady", "feminine"],
        "male": ["male", "man", "boy", "he", "gentleman", "masculine"],
        "neutral": ["neutral", "child", "kid"]
    }
    AGE_KEYWORDS = {"young": ["young", "youth"], "middle": ["middle", "middle-aged"], "old": ["old", "elderly"]}

    def __init__(self, library: VoiceLibrary):
        self.library = library

    def match_voice(self, character: Character, emotion: Optional[EmotionProfile]=None) -> MatchResult:
        candidates = self._filter_candidates(character)
        if not candidates:
            return MatchResult(candidates=[], best_match=None, confidence=0.0)
        voice_candidates = []
        for voice in candidates:
            confidence = self.calculate_confidence(character, voice, emotion)
            reasons = self._get_match_reasons(character, voice)
            voice_candidates.append(VoiceCandidate(voice=voice, confidence=confidence, match_reasons=reasons))
        voice_candidates.sort(key=lambda x: x.confidence, reverse=True)
        best_match = voice_candidates[0] if voice_candidates else None
        overall_confidence = best_match.confidence if best_match else 0.0
        if character.importance == CharacterImportance.PROTAGONIST:
            result_candidates = voice_candidates[:3]
        else:
            result_candidates = [voice_candidates[0]] if voice_candidates else []
        return MatchResult(candidates=result_candidates, best_match=best_match, confidence=overall_confidence)

    def filter_by_tags(self, tags: list[str]) -> list[Voice]:
        if not tags:
            return self.library.list()
        return self.library.search_by_tags(tags)

    def calculate_confidence(self, character: Character, voice: Voice, emotion: Optional[EmotionProfile]=None) -> float:
        total = 0.0
        total += self._calculate_gender_score(character, voice) * 0.30
        total += self._calculate_tag_score(character, voice) * 0.40
        total += self._calculate_description_score(character, voice) * 0.30
        return min(1.0, total)

    def _filter_candidates(self, character: Character) -> list[Voice]:
        search_tags = list(character.traits)
        inferred = self._infer_gender_from_description(character.description)
        if inferred:
            search_tags.append(inferred)
        candidates = self.filter_by_tags(search_tags)
        if not candidates and inferred:
            candidates = self.library.list(gender=inferred)
        if not candidates:
            candidates = self.library.list()
        return candidates

    def _get_match_reasons(self, character: Character, voice: Voice) -> list[str]:
        reasons = []
        inferred = self._infer_gender_from_description(character.description)
        if inferred and voice.gender == inferred:
            reasons.append(f"性别匹配: {voice.gender}")
        matching_tags = set(character.traits) & set(voice.tags)
        if matching_tags:
            reasons.append(f"标签匹配: {','.join(matching_tags)}")
        return reasons

    def _calculate_gender_score(self, character: Character, voice: Voice) -> float:
        inferred = self._infer_gender_from_description(character.description)
        if inferred:
            return 1.0 if voice.gender == inferred else 0.0
        return 0.5

    def _calculate_tag_score(self, character: Character, voice: Voice) -> float:
        if not character.traits:
            return 0.5
        matching = set(character.traits) & set(voice.tags)
        if not voice.tags:
            return 0.0
        return len(matching) / max(len(character.traits), 1)

    def _calculate_description_score(self, character: Character, voice: Voice) -> float:
        if not character.description or not voice.description:
            return 0.5
        common = self._find_common_words(character.description, voice.description)
        if not common:
            return 0.0
        return min(1.0, len(common) * 0.2)

    def _infer_gender_from_description(self, description: str) -> Optional[str]:
        if not description:
            return None
        for gender, keywords in self.GENDER_KEYWORDS.items():
            if any(kw in description for kw in keywords):
                return gender
        return None

    def _find_common_words(self, text1: str, text2: str, min_length: int=2) -> list[str]:
        stop_words = {"的","了","是","在","有","和","与","或","这","那","我","你","他","她","它"}
        def extract(text):
            words = []
            current = ""
            for char in text.lower():
                if char.isalnum():
                    current += char
                else:
                    if current:
                        words.append(current)
                        current = ""
            if current:
                words.append(current)
            return set(w for w in words if len(w) >= min_length and w not in stop_words)
        return list(extract(text1) & extract(text2))
