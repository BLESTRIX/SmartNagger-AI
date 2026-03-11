import torch
import os
import numpy as np
from PIL import Image
import streamlit as st
from transformers import BlipProcessor, BlipForConditionalGeneration


# ==================== BLIP IMAGE CAPTIONER ====================
class ImageCaptioner:
    """
    Uses BLIP (Salesforce) to generate a natural language caption from an image.
    The caption is then passed to Groq for NLP-based classification.
    """

    def __init__(self):
        self.processor = None
        self.model = None
        self._load_model()

    @st.cache_resource(show_spinner="Loading BLIP image model...")
    def _load_model(_self):
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        model.eval()
        return processor, model

    def _ensure_loaded(self):
        if self.processor is None or self.model is None:
            self.processor, self.model = self._load_model()

    def generate_caption(self, image) -> str:
        """
        Generate a descriptive caption for the given image.

        Args:
            image: PIL.Image, file-like object, or path string

        Returns:
            Caption string describing the image content
        """
        self._ensure_loaded()

        try:
            # Normalise input to PIL Image
            if isinstance(image, str):
                pil_img = Image.open(image).convert("RGB")
            elif isinstance(image, Image.Image):
                pil_img = image.convert("RGB")
            else:
                # Streamlit UploadedFile or BytesIO
                pil_img = Image.open(image).convert("RGB")

            inputs = self.processor(pil_img, return_tensors="pt")

            with torch.no_grad():
                output = self.model.generate(**inputs, max_new_tokens=60)

            caption = self.processor.decode(output[0], skip_special_tokens=True)
            return caption

        except Exception as e:
            st.error(f"Image captioning error: {str(e)}")
            return "an unidentified civic issue"


# ==================== VOICE TO TEXT (GROQ WHISPER API) ====================
class VoiceToText:
    """
    Transcribes audio using Groq's Whisper-large-v3 API.

    Why not local openai-whisper
    ----------------------------
    The traceback shows `whisper.py` doing `ctypes.CDLL(libc_name)` — this
    means the WRONG 'whisper' package is installed (a soundcard library, not
    OpenAI Whisper). Even with the correct package, openai-whisper always
    shells out to ffmpeg which causes WinError 2 on Windows without ffmpeg
    on PATH.

    Groq Whisper API solution
    -------------------------
    - Sends raw WAV bytes over HTTPS to Groq's whisper-large-v3 endpoint.
    - Zero local dependencies: no whisper package, no ffmpeg, no ctypes.
    - Works identically on Windows / Mac / Linux.
    - More accurate than whisper-tiny.
    - Reuses the GROQ_API_KEY already configured in your project.

    You can safely remove 'openai-whisper' and 'whisper' from requirements.txt.
    """

    def __init__(self):
        self.client = self._init_client()

    # ------------------------------------------------------------------
    def _init_client(self):
        """Initialise Groq client from env or st.secrets."""
        try:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY", "")
            if not api_key:
                try:
                    api_key = st.secrets.get("GROQ_API_KEY", "")
                except Exception:
                    pass

            if not api_key:
                st.error(
                    "❌ GROQ_API_KEY not found. "
                    "Add it to your .env file or Streamlit secrets to enable voice transcription."
                )
                return None

            return Groq(api_key=api_key)

        except ImportError:
            st.error("❌ 'groq' package not installed. Run: pip install groq")
            return None
        except Exception as e:
            st.error(f"❌ Could not initialise Groq client: {e}")
            return None

    # ------------------------------------------------------------------
    def transcribe(self, audio_bytes, language: str = "auto") -> str:
        """
        Transcribe audio bytes using Groq Whisper API.

        Steps
        -----
        1. Validate client is ready.
        2. Read and validate audio bytes.
        3. Write to temp file, close it, send to Groq, delete temp file.
        4. Return transcribed text.

        Args:
            audio_bytes : bytes or file-like object from st.audio_input()
            language    : "auto" for auto-detect, or ISO code "en" / "ur"

        Returns:
            Transcribed text string, or "" on any failure.
        """
        import tempfile

        # ── Check 1: client ready ─────────────────────────────────────────
        if not self.client:
            st.error("Voice transcription unavailable — check GROQ_API_KEY.")
            return ""

        # ── Check 2: read audio bytes ─────────────────────────────────────
        try:
            raw = audio_bytes.read() if hasattr(audio_bytes, "read") else bytes(audio_bytes)
        except Exception as e:
            st.error(f"Could not read audio data: {e}")
            return ""

        if not raw or len(raw) < 200:
            st.warning("⚠️ No audio detected. Please record again.")
            return ""

        # ── Step 1: write to temp file and CLOSE before sending ───────────
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="sn_audio_")
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(raw)

            # ── Check 3: file written correctly ───────────────────────────
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                st.error("Temp audio file empty — please try recording again.")
                return ""

            # ── Step 2: send to Groq Whisper API ──────────────────────────
            kwargs = {
                "model": "whisper-large-v3",
                "response_format": "text",
            }
            # Groq does not accept "auto" — omit language for auto-detection
            if language and language != "auto":
                kwargs["language"] = language

            with open(tmp_path, "rb") as audio_file:
                result = self.client.audio.transcriptions.create(
                    file=("recording.wav", audio_file.read(), "audio/wav"),
                    **kwargs,
                )

            # Groq returns plain string when response_format="text"
            text = result.strip() if isinstance(result, str) else result.text.strip()

            # ── Check 4: non-empty transcript ─────────────────────────────
            if not text:
                st.warning("⚠️ No speech detected. Please speak clearly and try again.")
            return text

        except Exception as e:
            st.error(f"Transcription error: {e}")
            return ""

        finally:
            # ── Step 3: always clean up temp file ─────────────────────────
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass


# ==================== NLP CLASSIFIER (GROQ-POWERED) ====================
class NLPClassifier:
    """
    Uses Groq LLM to intelligently classify any text (from direct input,
    BLIP caption, or Whisper transcription) into:
      - Issue type
      - Severity (High / Medium / Low)
      - Responsible department
    Eliminates all hardcoded mappings.
    """

    ISSUE_TYPES = [
        "Pothole",
        "Garbage",
        "Water Leak",
        "Broken Streetlight",
        "Damaged Road",
        "Illegal Dumping",
        "Sewage Overflow",
        "Other",
    ]

    DEPARTMENTS = {
        "Pothole": "Roads & Highways Department",
        "Garbage": "Sanitation & Waste Management",
        "Water Leak": "Water & Sewerage Authority",
        "Broken Streetlight": "Electricity Department",
        "Damaged Road": "Roads & Highways Department",
        "Illegal Dumping": "Sanitation & Waste Management",
        "Sewage Overflow": "Water & Sewerage Authority",
        "Other": "General Administration",
    }

    def __init__(self):
        self._init_groq()

    def _init_groq(self):
        try:
            from groq import Groq

            api_key = os.getenv("GROQ_API_KEY", "")
            if not api_key:
                try:
                    api_key = st.secrets.get("GROQ_API_KEY", "")
                except Exception:
                    api_key = ""

            self.client = Groq(api_key=api_key) if api_key else None
        except Exception as e:
            st.warning(f"Groq not available: {e}. Using keyword fallback.")
            self.client = None

    def classify(self, text: str):
        """
        Classify the given text using Groq NLP.

        Returns:
            tuple: (issue_type, severity, department)
        """
        if self.client:
            return self._classify_with_groq(text)
        return self._classify_with_keywords(text)

    def _classify_with_groq(self, text: str):
        """Send text to Groq and parse structured response."""
        issue_list = ", ".join(self.ISSUE_TYPES)

        prompt = f"""You are a civic issue classifier for Pakistani cities.

Analyze the following description and return ONLY a JSON object with these exact keys:
- "issue_type": one of [{issue_list}]
- "severity": one of ["High", "Medium", "Low"]
- "department": the responsible government department

Severity guidelines:
- High: immediate safety risk, health hazard, infrastructure failure (potholes, water leaks, sewage)
- Medium: quality of life impact but not immediately dangerous (garbage, broken streetlights)
- Low: minor inconvenience or general complaints

Description: "{text}"

Return ONLY valid JSON, nothing else. Example:
{{"issue_type": "Pothole", "severity": "High", "department": "Roads & Highways Department"}}"""

        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=150,
            )
            raw = response.choices[0].message.content.strip()

            import json, re

            # Extract JSON even if there's surrounding text
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                issue_type = data.get("issue_type", "Other")
                severity = data.get("severity", "Medium")
                department = data.get(
                    "department", self.DEPARTMENTS.get(issue_type, "General Administration")
                )

                # Validate issue_type against known list
                if issue_type not in self.ISSUE_TYPES:
                    issue_type = "Other"
                    department = "General Administration"

                return issue_type, severity, department

        except Exception as e:
            st.warning(f"Groq classification error: {e}. Using keyword fallback.")

        return self._classify_with_keywords(text)

    def _classify_with_keywords(self, text: str):
        """Simple keyword-based fallback classifier."""
        text_lower = text.lower()

        rules = [
            (["pothole", "hole", "crater", "garhha", "گڑھا"], "Pothole", "High"),
            (["garbage", "trash", "waste", "kachra", "کچرا", "dump", "litter"], "Garbage", "Medium"),
            (["water leak", "pipe", "leak", "pani ka rasao", "پانی", "flood"], "Water Leak", "High"),
            (["light", "lamp", "streetlight", "dark", "روشنی", "lait"], "Broken Streetlight", "Medium"),
            (["road damage", "asphalt", "pavement", "broken road"], "Damaged Road", "High"),
            (["illegal dump", "unauthorized"], "Illegal Dumping", "Medium"),
            (["sewage", "drain", "overflow", "manhole"], "Sewage Overflow", "High"),
        ]

        for keywords, issue_type, severity in rules:
            if any(kw in text_lower for kw in keywords):
                return issue_type, severity, self.DEPARTMENTS[issue_type]

        return "Other", "Low", "General Administration"


# ==================== UNIFIED COMPLAINT CLASSIFIER ====================
class ComplaintClassifier:
    """
    Single entry point for all input types.
    Internally uses BLIP → NLP for images, Whisper → NLP for audio,
    and direct NLP for text.
    """

    def __init__(self):
        self.nlp = NLPClassifier()
        self._image_captioner = None
        self._voice_to_text = None

    @property
    def image_captioner(self):
        if self._image_captioner is None:
            self._image_captioner = ImageCaptioner()
        return self._image_captioner

    @property
    def voice_to_text(self):
        if self._voice_to_text is None:
            self._voice_to_text = VoiceToText()
        return self._voice_to_text

    def classify_text(self, text: str):
        """Classify from plain text input."""
        return self.nlp.classify(text)

    def classify_image(self, image):
        """
        Classify from image (PIL Image, UploadedFile, or path).
        Step 1: BLIP generates caption.
        Step 2: Groq classifies the caption.
        Returns: (issue_type, severity, department, caption)
        """
        caption = self.image_captioner.generate_caption(image)
        issue_type, severity, department = self.nlp.classify(caption)
        return issue_type, severity, department, caption

    def classify_audio(self, audio_bytes, language: str = "auto"):
        """
        Classify from real-time audio recording.
        Step 1: Whisper transcribes audio.
        Step 2: Groq classifies the transcription.
        Returns: (issue_type, severity, department, transcription)
        """
        transcription = self.voice_to_text.transcribe(audio_bytes, language)
        if not transcription:
            return "Other", "Low", "General Administration", ""
        issue_type, severity, department = self.nlp.classify(transcription)
        return issue_type, severity, department, transcription


# ==================== CACHED SINGLETONS ====================
@st.cache_resource
def get_complaint_classifier():
    return ComplaintClassifier()


# Legacy aliases so existing imports don't break
@st.cache_resource
def get_image_classifier():
    return get_complaint_classifier()


@st.cache_resource
def get_voice_to_text():
    return get_complaint_classifier().voice_to_text


@st.cache_resource
def get_text_classifier():
    return get_complaint_classifier()