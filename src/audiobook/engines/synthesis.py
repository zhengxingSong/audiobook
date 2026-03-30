"""Voice synthesis engine - GPT-SoVITS integration."""

import time
from dataclasses import dataclass, field
from typing import Optional

import requests

from audiobook.models import AudioFragment, EmotionProfile, EmotionIntensity, Voice, Fragment


class SynthesisError(Exception):
    """Base exception for synthesis errors."""

    pass


class SynthesisTimeoutError(SynthesisError):
    """Raised when synthesis request times out."""

    pass


class SynthesisConnectionError(SynthesisError):
    """Raised when connection to synthesis service fails."""

    pass


class SynthesisValidationError(SynthesisError):
    """Raised when audio validation fails."""

    pass


@dataclass
class SynthesisResult:
    """Result of a synthesis operation.

    Attributes:
        success: Whether the synthesis was successful.
        audio_fragment: The generated audio fragment (if successful).
        error_message: Error message (if failed).
        retry_count: Number of retries attempted.
        processing_time: Total processing time in seconds.
    """

    success: bool
    audio_fragment: Optional[AudioFragment] = None
    error_message: str = ""
    retry_count: int = 0
    processing_time: float = 0.0


@dataclass
class AudioQuality:
    """Quality metrics for synthesized audio.

    Attributes:
        is_valid: Whether the audio passes quality checks.
        is_silent: Whether the audio is silent.
        duration_match: Whether duration matches expected.
        expected_duration: Expected duration in seconds.
        actual_duration: Actual duration in seconds.
        deviation_percent: Deviation from expected duration.
        issues: List of quality issues found.
    """

    is_valid: bool = True
    is_silent: bool = False
    duration_match: bool = True
    expected_duration: float = 0.0
    actual_duration: float = 0.0
    deviation_percent: float = 0.0
    issues: list[str] = field(default_factory=list)


class VoiceSynthesisEngine:
    """Voice synthesis engine using GPT-SoVITS API.

    This engine provides high-quality text-to-speech synthesis with
    emotion-aware voice modulation using GPT-SoVITS backend.

    Attributes:
        EMOTION_TEMPLATES: Mapping of emotion types to prompt templates.
        endpoint: GPT-SoVITS API endpoint URL.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.

    Example:
        >>> engine = VoiceSynthesisEngine()
        >>> voice = Voice(voice_id="v1", name="Narrator", gender="中性", age_range="成年")
        >>> emotion = EmotionProfile(emotion_type="喜悦", intensity=EmotionIntensity.MODERATE)
        >>> result = engine.synthesize_text(voice, emotion, "你好世界")
    """

    EMOTION_TEMPLATES = {
        "愤怒": "用愤怒的语气说话，语速较快，声音有力，情绪强烈。",
        "悲伤": "用悲伤的语气说话，语速较慢，声音低沉，带有哽咽感。",
        "喜悦": "用喜悦的语气说话，语速轻快，声音明亮，情绪愉悦。",
        "恐惧": "用恐惧的语气说话，语速不稳，声音颤抖，带有紧张感。",
        "惊讶": "用惊讶的语气说话，语速突然变化，声音提高。",
        "平静": "用平静的语气说话，语速平稳，声音自然，情绪稳定。",
        "neutral": "用平静的语气说话，语速平稳，声音自然，情绪稳定。",
        "happy": "用喜悦的语气说话，语速轻快，声音明亮，情绪愉悦。",
        "sad": "用悲伤的语气说话，语速较慢，声音低沉，带有哽咽感。",
        "angry": "用愤怒的语气说话，语速较快，声音有力，情绪强烈。",
        "fearful": "用恐惧的语气说话，语速不稳，声音颤抖，带有紧张感。",
        "surprised": "用惊讶的语气说话，语速突然变化，声音提高。",
    }

    INTENSITY_MODIFIERS = {
        EmotionIntensity.LIGHT: "轻微",
        EmotionIntensity.MODERATE: "中等",
        EmotionIntensity.STRONG: "强烈",
    }

    # Audio analysis constants
    SILENCE_THRESHOLD = 0.01  # RMS threshold for silence detection
    DURATION_TOLERANCE = 0.3  # 30% deviation allowed
    CHARS_PER_SECOND = 4.0  # Average speaking rate

    def __init__(
        self,
        endpoint: str = "http://localhost:9880",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """Initialize the voice synthesis engine.

        Args:
            endpoint: GPT-SoVITS API endpoint URL.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
        """
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def generate_prompt(self, voice: Voice, emotion: EmotionProfile, text: str) -> str:
        """Generate synthesis prompt from voice and emotion parameters.

        Creates a detailed prompt string that instructs the TTS engine
        on how to render the text with appropriate emotion and voice style.

        Args:
            voice: Voice configuration to use.
            emotion: Emotion profile for the synthesis.
            text: Text content to synthesize.

        Returns:
            Generated prompt string for TTS synthesis.
        """
        parts = []

        # Add emotion template
        emotion_template = self.get_emotion_template(emotion.emotion_type)
        if emotion_template:
            parts.append(emotion_template)

        # Add intensity modifier
        intensity_mod = self.INTENSITY_MODIFIERS.get(emotion.intensity, "")
        if intensity_mod and emotion_template:
            parts[0] = f"{intensity_mod}{parts[0]}"

        # Add voice characteristics
        if voice.description:
            parts.append(voice.description)

        # Add scene context if available
        if emotion.scene_context:
            parts.append(f"场景：{emotion.scene_context}")

        # Add suggested adjustment
        if emotion.suggested_adjustment:
            parts.append(emotion.suggested_adjustment)

        # Add components
        for component in emotion.components:
            parts.append(component)

        # Combine all parts
        prompt = " ".join(parts) if parts else ""

        # Add text preview for context
        text_preview = text[:50] if len(text) > 50 else text
        if prompt:
            prompt = f"{prompt} 文本内容：{text_preview}"

        return prompt

    def get_emotion_template(self, emotion_type: str) -> Optional[str]:
        """Get emotion template for the specified emotion type.

        Args:
            emotion_type: Type of emotion (e.g., '喜悦', 'happy').

        Returns:
            Emotion template string or None if not found.
        """
        return self.EMOTION_TEMPLATES.get(emotion_type)

    def build_synthesis_params(
        self, voice: Voice, emotion: EmotionProfile, text: str
    ) -> dict:
        """Build API parameters for synthesis request.

        Constructs the parameter dictionary required for GPT-SoVITS API calls,
        including voice reference, emotion prompt, and synthesis settings.

        Args:
            voice: Voice configuration to use.
            emotion: Emotion profile for synthesis.
            text: Text content to synthesize.

        Returns:
            Dictionary of API parameters.
        """
        prompt = self.generate_prompt(voice, emotion, text)

        params = {
            "text": text,
            "text_lang": "zh",
            "prompt_text": prompt,
            "prompt_lang": "zh",
            "top_k": 5,
            "top_p": 1.0,
            "temperature": 1.0,
            "text_split_method": "cut5",
            "batch_size": 1,
            "speed_factor": 1.0,
            "split_bucket": True,
        }

        # Add reference audio if available
        if voice.audio_path:
            params["ref_audio_path"] = voice.audio_path

        # Add voice embedding if available
        if voice.embedding:
            params["refer_prompt"] = voice.embedding

        return params

    def synthesize(
        self,
        prompt: str,
        text: str,
        voice_id: str,
        reference_audio: str,
        fragment_id: Optional[str] = None,
    ) -> AudioFragment:
        """Synthesize audio using GPT-SoVITS API with retry logic.

        Args:
            prompt: Prompt/instruction for synthesis.
            text: Text content to synthesize.
            voice_id: Identifier for the voice to use.
            reference_audio: Path to reference audio file.
            fragment_id: Optional fragment identifier (generated if not provided).

        Returns:
            AudioFragment containing the synthesized audio.

        Raises:
            SynthesisTimeoutError: If request times out.
            SynthesisConnectionError: If connection fails.
            SynthesisError: If synthesis fails after all retries.
        """
        if fragment_id is None:
            fragment_id = f"frag_{int(time.time() * 1000)}"

        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = self._make_api_request(
                    prompt, text, voice_id, reference_audio
                )
                return self._process_response(response, fragment_id)
            except requests.Timeout as e:
                last_error = SynthesisTimeoutError(
                    f"Synthesis timeout after {self.timeout}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
            except requests.ConnectionError as e:
                last_error = SynthesisConnectionError(
                    f"Connection failed: {str(e)} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
            except requests.RequestException as e:
                last_error = SynthesisError(
                    f"Synthesis request failed: {str(e)} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)

        raise last_error or SynthesisError("Synthesis failed")

    def _make_api_request(
        self,
        prompt: str,
        text: str,
        voice_id: str,
        reference_audio: str,
    ) -> requests.Response:
        """Make API request to GPT-SoVITS endpoint.

        Args:
            prompt: Prompt for synthesis.
            text: Text to synthesize.
            voice_id: Voice identifier.
            reference_audio: Reference audio path.

        Returns:
            API response object.

        Raises:
            requests.RequestException: If request fails.
        """
        payload = {
            "text": text,
            "prompt_text": prompt,
            "prompt_lang": "zh",
            "text_lang": "zh",
            "ref_audio_path": reference_audio,
        }

        url = f"{self.endpoint}/synthesize"
        response = requests.post(
            url,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def _process_response(
        self, response: requests.Response, fragment_id: str
    ) -> AudioFragment:
        """Process API response and create AudioFragment.

        Args:
            response: API response object.
            fragment_id: Fragment identifier.

        Returns:
            AudioFragment with synthesized audio.
        """
        audio_data = response.content

        # Estimate duration from audio data size
        # WAV format: 44100 Hz, 16-bit, mono = 88200 bytes/second
        duration = len(audio_data) / 88200.0

        return AudioFragment(
            fragment_id=fragment_id,
            audio_data=audio_data,
            duration=duration,
            sample_rate=44100,
            format="wav",
        )

    def synthesize_text(
        self,
        voice: Voice,
        emotion: EmotionProfile,
        text: str,
        fragment_id: Optional[str] = None,
    ) -> SynthesisResult:
        """Synthesize text with voice and emotion (convenience method).

        This is the main entry point for text-to-speech synthesis,
        combining parameter building, API calling, and validation.

        Args:
            voice: Voice configuration to use.
            emotion: Emotion profile for synthesis.
            text: Text content to synthesize.
            fragment_id: Optional fragment identifier.

        Returns:
            SynthesisResult containing success status and audio fragment.
        """
        start_time = time.time()

        try:
            params = self.build_synthesis_params(voice, emotion, text)
            fragment = self.synthesize(
                prompt=params["prompt_text"],
                text=text,
                voice_id=voice.voice_id,
                reference_audio=params.get("ref_audio_path", voice.audio_path),
                fragment_id=fragment_id,
            )

            # Validate the result
            expected_duration = self._estimate_duration(text)
            quality = self.validate_audio(fragment, expected_duration)

            if not quality.is_valid:
                return SynthesisResult(
                    success=False,
                    error_message=f"Audio validation failed: {', '.join(quality.issues)}",
                    processing_time=time.time() - start_time,
                )

            return SynthesisResult(
                success=True,
                audio_fragment=fragment,
                processing_time=time.time() - start_time,
            )

        except SynthesisError as e:
            return SynthesisResult(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def validate_audio(
        self, fragment: AudioFragment, expected_duration: float
    ) -> AudioQuality:
        """Validate synthesized audio quality.

        Performs quality checks on synthesized audio including
        silence detection and duration verification.

        Args:
            fragment: Audio fragment to validate.
            expected_duration: Expected duration in seconds.

        Returns:
            AudioQuality object with validation results.
        """
        issues: list[str] = []
        is_silent = self._is_silent(fragment.audio_data)

        if is_silent:
            issues.append("Audio is silent")

        # Check duration match
        deviation = abs(fragment.duration - expected_duration)
        deviation_percent = (
            (deviation / expected_duration * 100) if expected_duration > 0 else 0
        )

        duration_match = deviation_percent <= self.DURATION_TOLERANCE * 100
        if not duration_match:
            issues.append(
                f"Duration mismatch: expected {expected_duration:.2f}s, "
                f"got {fragment.duration:.2f}s ({deviation_percent:.1f}% deviation)"
            )

        return AudioQuality(
            is_valid=len(issues) == 0,
            is_silent=is_silent,
            duration_match=duration_match,
            expected_duration=expected_duration,
            actual_duration=fragment.duration,
            deviation_percent=deviation_percent,
            issues=issues,
        )

    def _estimate_duration(self, text: str) -> float:
        """Estimate audio duration from text length.

        Uses average speaking rate to estimate how long
        the synthesized audio should be.

        Args:
            text: Text to estimate duration for.

        Returns:
            Estimated duration in seconds.
        """
        # Count Chinese characters and other characters separately
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        other_chars = len(text) - chinese_chars

        # Chinese characters are typically spoken slower
        chinese_rate = 3.5  # chars per second
        other_rate = 12.0  # chars per second (for punctuation, spaces, etc.)

        estimated = (chinese_chars / chinese_rate) + (other_chars / other_rate)

        # Ensure minimum duration
        return max(estimated, 0.5)

    def _is_silent(self, audio_data: bytes) -> bool:
        """Detect if audio data represents silence.

        Analyzes audio data to determine if it contains meaningful
        audio or is effectively silent.

        Args:
            audio_data: Raw audio bytes.

        Returns:
            True if audio is silent, False otherwise.
        """
        if len(audio_data) < 100:
            return True

        # Skip WAV header (44 bytes) and sample a portion of the audio
        # to check for silence
        sample_start = 44
        sample_size = min(4096, len(audio_data) - sample_start)
        sample = audio_data[sample_start : sample_start + sample_size]

        if len(sample) == 0:
            return True

        # Calculate RMS (root mean square) of 16-bit audio samples
        sum_squares = 0
        sample_count = len(sample) // 2

        for i in range(sample_count):
            # Read 16-bit sample (little-endian)
            sample_value = int.from_bytes(
                sample[i * 2 : i * 2 + 2],
                byteorder="little",
                signed=True,
            )
            sum_squares += sample_value * sample_value

        if sample_count == 0:
            return True

        rms = (sum_squares / sample_count) ** 0.5

        # Normalize to 0-1 range (16-bit max = 32767)
        normalized_rms = rms / 32767.0

        return normalized_rms < self.SILENCE_THRESHOLD

    def health_check(self) -> bool:
        """Check if the synthesis service is healthy.

        Returns:
            True if service is available, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.endpoint}/health",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False