import io
from typing import List

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# ---------- Gemini client ----------
API_KEY = st.secrets["GEMINI_API_KEY"]  # uses Streamlit secrets
client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3-pro-image-preview"  # your specified model


def edit_tshirt_image(
    pil_image: Image.Image,
    style_prompt: str,
) -> Image.Image:
    """
    Call Gemini once for a single image and style.
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
                    image_size="1024x1024",  # your specified size
                ),
            ),
        )

        # Take the first returned image
        for part in response.parts:
            img = part.as_image()
            if img is not None:
                return img

        # Fallback: return original if nothing came back
        st.warning("Gemini returned no image - showing original")
        return pil_image
        
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return pil_image


def make_prompt(background_style: str) -> str:
    """
    Build a strong editing prompt that keeps the t‑shirt unchanged.
    """
    return (
        "You are editing an e‑commerce product photo of a t‑shirt.\n"
        "Keep the exact same t‑shirt, shape, print, color, and folds. "
        "Do NOT change or replace the t‑shirt, do NOT hallucinate a new design.\n"
        "Remove the current background (especially the green part) and replace it with a "
        f"{background_style}.\n"
        "IMPORTANT: Add slightly more empty space around the t-shirt - "
        "make it look like the photo was taken from a bit farther away, "
        "with more breathing room around the product.\n"
        "Enhance lighting and overall image quality for professional online store listing. "
        "Preserve realistic shadows and natural look."
    )


# ---------- Streamlit app ----------
st.set_page_config(page_title="T‑Shirt Photo Enhancer", layout="wide")

st.title("🛍️ T‑Shirt Photo Enhancer (Gemini 3 Pro Image Preview)")

# Session state for results
if "results_left" not in st.session_state:
    st.session_state.results_left: List[Image.Image] = []
if "results_right" not in st.session_state:
    st.session_state.results_right: List[Image.Image] = []


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
        # Process LEFT uploader images (white concrete background)
        if files_left:
            prompt_left = make_prompt(
                "modern white concrete studio background, clean, minimal, soft shadows"
            )
            for i, f in enumerate(files_left):
                with st.status(f"Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    edited = edit_tshirt_image(image, prompt_left)
                    st.session_state.results_left.append(edited)

        # Process RIGHT uploader images (wooden floor background)
        if files_right:
            prompt_right = make_prompt(
                "natural and clean wooden floor background, neutral wall, warm but subtle lighting"
            )
            for i, f in enumerate(files_right):
                with st.status(f"Processing {f.name}...", expanded=False):
                    image = Image.open(io.BytesIO(f.read())).convert("RGB")
                    edited = edit_tshirt_image(image, prompt_right)
                    st.session_state.results_right.append(edited)

    st.success("✅ All images processed!")
    st.rerun()


# ---------- Bottom area: results (FIXED) ----------
st.subheader("🎨 Enhanced Results")

res_left_col, res_right_col = st.columns(2)

with res_left_col:
    st.markdown("### 🧱 White Concrete Results")
    if st.session_state.results_left:
        for img in st.session_state.results_left:
            # FIXED: Convert PIL Image to bytes for Streamlit
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            st.image(img_byte_arr, caption=None, use_container_width=True)
    else:
        st.info("👆 Upload images to left side and click Process")

with res_right_col:
    st.markdown("### 🌲 Wooden Floor Results") 
    if st.session_state.results_right:
        for img in st.session_state.results_right:
            # FIXED: Convert PIL Image to bytes for Streamlit
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            st.image(img_byte_arr, caption=None, use_container_width=True)
    else:
        st.info("👆 Upload images to right side and click Process")
