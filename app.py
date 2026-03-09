import io
from typing import List

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ---------- Gemini client ----------
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.1-flash-image-preview"


def edit_tshirt_image(pil_image: Image.Image, style_prompt: str) -> bytes:
    """
    Call Gemini once and return raw image bytes.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                style_prompt,
                pil_image,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1",
                    image_size="1024x1024",
                ),
            ),
        )

        for part in response.parts:
            if part.inline_data is not None:
                return part.inline_data.data

        st.warning("Gemini returned no image - showing original")
        return None

    except Exception as e:
        st.error(f"API error: {str(e)}")
        return None


def make_prompt(background_style: str, lighting_style: str, shadow_style: str) -> str:
    return (
        "You are editing an e‑commerce product photo of a t‑shirt for an online store.\n"
        "The t‑shirt should appear LAID FLAT on the surface below it, as if placed and styled on the ground.\n"
        "Keep the exact same t‑shirt, shape, print, color, and folds — do NOT change or replace the t‑shirt design.\n"
        "Remove the current background (especially the green part).\n"
        f"Place the t‑shirt flat and neatly on: {background_style}.\n"
        f"Lighting: {lighting_style}.\n"
        f"Shadows: {shadow_style}.\n"
        "Add slightly more empty space around the t-shirt — make it look like the photo was taken from a bit farther away, "
        "with breathing room on all sides.\n"
        "Enhance overall sharpness, color vibrancy, and image quality for a professional online store listing."
    )


# ---------- Streamlit app ----------
st.set_page_config(page_title="T‑Shirt Photo Enhancer", layout="wide")

st.title("🛍️ T‑Shirt Photo Enhancer (Gemini 3 Pro Image Preview)")

# Session state stores raw bytes
if "results_left" not in st.session_state:
    st.session_state.results_left: List[bytes] = []
if "results_right" not in st.session_state:
    st.session_state.results_right: List[bytes] = []


# ---------- Top area: uploaders ----------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📁 White Concrete Background")
    files_left = st.file_uploader(
        "Upload PNG/JPG images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="uploader_left",
    )

with col_right:
    st.subheader("🌳 Wooden Floor Background")
    files_right = st.file_uploader(
        "Upload PNG/JPG images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="uploader_right",
    )

st.markdown("---")

# ---------- Control buttons ----------
col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    btn_process = st.button("✨ Process Images", type="primary", use_container_width=True)

with col_btn2:
    btn_reset = st.button("🔄 Reset", use_container_width=True)

if btn_reset:
    st.session_state.results_left = []
    st.session_state.results_right = []
    st.rerun()

# ---------- Processing ----------
if btn_process and (files_left or files_right):
    with st.spinner("Processing images through Gemini..."):

        if files_left:
            prompt_left = make_prompt(
                background_style=(
                    "a clean modern white concrete floor surface, smooth texture, "
                    "minimal and editorial feel"
                ),
                lighting_style=(
                    "soft overhead studio lighting, cool-white tone, even and diffused, "
                    "no harsh highlights, slightly elevated brightness to enhance the concrete feel"
                ),
                shadow_style=(
                    "soft and subtle natural shadow cast directly beneath and around the t-shirt, "
                    "slightly blurred edges to feel grounded on the surface"
                ),
            )
            for f in files_left:
                with st.status(f"Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    result_bytes = edit_tshirt_image(image, prompt_left)
                    if result_bytes:
                        st.session_state.results_left.append(result_bytes)

        if files_right:
            prompt_right = make_prompt(
                background_style=(
                    "a natural warm wooden floor surface, light oak texture, "
                    "clean and organic feel with visible wood grain"
                ),
                lighting_style=(
                    "warm natural daylight coming from the side, soft and golden tone, "
                    "gentle highlights that complement the wood texture without overexposing"
                ),
                shadow_style=(
                    "warm-toned soft shadow cast to one side beneath the t-shirt, "
                    "slightly elongated and natural as if lit by a window, grounded on the wood"
                ),
            )
            for f in files_right:
                with st.status(f"Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    result_bytes = edit_tshirt_image(image, prompt_right)
                    if result_bytes:
                        st.session_state.results_right.append(result_bytes)

    st.success("✅ All images processed!")
    st.rerun()


# ---------- Bottom area: results ----------
st.subheader("🎨 Enhanced Results")

res_left_col, res_right_col = st.columns(2)

with res_left_col:
    st.markdown("### 🧱 White Concrete Results")
    if st.session_state.results_left:
        for img_bytes in st.session_state.results_left:
            st.image(img_bytes, use_container_width=True)
    else:
        st.info("👆 Upload images to left side and click Process")

with res_right_col:
    st.markdown("### 🌲 Wooden Floor Results")
    if st.session_state.results_right:
        for img_bytes in st.session_state.results_right:
            st.image(img_bytes, use_container_width=True)
    else:
        st.info("👆 Upload images to right side and click Process")
