import io
import zipfile
from typing import List

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ---------- Gemini client ----------
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash-image"


def edit_tshirt_image(pil_image: Image.Image, style_prompt: str) -> bytes:
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


# Prompt configs per background
PROMPT_LEFT = make_prompt(
    background_style="a clean modern white concrete floor surface, smooth texture, minimal and editorial feel",
    lighting_style="soft overhead studio lighting, cool-white tone, even and diffused, no harsh highlights, slightly elevated brightness to enhance the concrete feel",
    shadow_style="soft and subtle natural shadow cast directly beneath and around the t-shirt, slightly blurred edges to feel grounded on the surface",
)

PROMPT_RIGHT = make_prompt(
    background_style="a natural warm wooden floor surface, light oak texture, clean and organic feel with visible wood grain",
    lighting_style="warm natural daylight coming from the side, soft and golden tone, gentle highlights that complement the wood texture without overexposing",
    shadow_style="warm-toned soft shadow cast to one side beneath the t-shirt, slightly elongated and natural as if lit by a window, grounded on the wood",
)

PROMPT_TERRAZZO = make_prompt(
    background_style="a sandy beige terrazzo floor surface, smooth with small warm-toned stone chips, upscale and boutique feel",
    lighting_style="soft diffused natural light from above, warm-neutral tone, even across the surface with gentle highlights catching the terrazzo texture",
    shadow_style="soft and short shadow cast directly beneath the t-shirt, slightly warm-toned, grounded naturally on the terrazzo surface",
)


# ---------- Streamlit app ----------
st.set_page_config(page_title="T‑Shirt Photo Enhancer", layout="wide")

st.title("🛍️ T‑Shirt Photo Enhancer (Gemini)")

# Session state
if "results_left" not in st.session_state:
    st.session_state.results_left: List[bytes] = []
if "results_right" not in st.session_state:
    st.session_state.results_right: List[bytes] = []
if "results_terrazzo" not in st.session_state:
    st.session_state.results_terrazzo: List[bytes] = []


# ---------- Top area: 3 uploaders ----------
col_left, col_right, col_terrazzo = st.columns(3)

with col_left:
    st.subheader("🧱 White Concrete")
    files_left = st.file_uploader(
        "Upload PNG/JPG images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="uploader_left",
    )

with col_right:
    st.subheader("🌳 Wooden Floor")
    files_right = st.file_uploader(
        "Upload PNG/JPG images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="uploader_right",
    )

with col_terrazzo:
    st.subheader("🪨 Sandy Terrazzo")
    files_terrazzo = st.file_uploader(
        "Upload PNG/JPG images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="uploader_terrazzo",
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
    st.session_state.results_terrazzo = []
    st.rerun()

# ---------- Processing ----------
if btn_process and (files_left or files_right or files_terrazzo):
    with st.spinner("Processing images through Gemini..."):

        if files_left:
            for f in files_left:
                with st.status(f"[Concrete] Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    result_bytes = edit_tshirt_image(image, PROMPT_LEFT)
                    if result_bytes:
                        st.session_state.results_left.append(result_bytes)

        if files_right:
            for f in files_right:
                with st.status(f"[Wood] Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    result_bytes = edit_tshirt_image(image, PROMPT_RIGHT)
                    if result_bytes:
                        st.session_state.results_right.append(result_bytes)

        if files_terrazzo:
            for f in files_terrazzo:
                with st.status(f"[Terrazzo] Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    result_bytes = edit_tshirt_image(image, PROMPT_TERRAZZO)
                    if result_bytes:
                        st.session_state.results_terrazzo.append(result_bytes)

    st.success("✅ All images processed!")
    st.rerun()


# ---------- Download All button ----------
all_results = (
    st.session_state.results_left
    + st.session_state.results_right
    + st.session_state.results_terrazzo
)

if all_results:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, img_bytes in enumerate(st.session_state.results_left):
            zip_file.writestr(f"concrete_{i+1}.png", img_bytes)
        for i, img_bytes in enumerate(st.session_state.results_right):
            zip_file.writestr(f"wood_{i+1}.png", img_bytes)
        for i, img_bytes in enumerate(st.session_state.results_terrazzo):
            zip_file.writestr(f"terrazzo_{i+1}.png", img_bytes)
    zip_buffer.seek(0)

    st.download_button(
        label="⬇️ Download All Images (ZIP)",
        data=zip_buffer,
        file_name="tshirt_enhanced.zip",
        mime="application/zip",
        use_container_width=True,
    )

st.markdown("---")

# ---------- Bottom area: results ----------
st.subheader("🎨 Enhanced Results")

res_left_col, res_right_col, res_terrazzo_col = st.columns(3)

with res_left_col:
    st.markdown("### 🧱 White Concrete")
    if st.session_state.results_left:
        for img_bytes in st.session_state.results_left:
            st.image(img_bytes, use_container_width=True)
    else:
        st.info("👆 Upload images to Concrete side and click Process")

with res_right_col:
    st.markdown("### 🌳 Wooden Floor")
    if st.session_state.results_right:
        for img_bytes in st.session_state.results_right:
            st.image(img_bytes, use_container_width=True)
    else:
        st.info("👆 Upload images to Wood side and click Process")

with res_terrazzo_col:
    st.markdown("### 🪨 Sandy Terrazzo")
    if st.session_state.results_terrazzo:
        for img_bytes in st.session_state.results_terrazzo:
            st.image(img_bytes, use_container_width=True)
    else:
        st.info("👆 Upload images to Terrazzo side and click Process")
