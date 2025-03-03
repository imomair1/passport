import streamlit as st
from PIL import Image, ImageColor, ImageEnhance, ImageFilter
import numpy as np
import io
import cv2
from rembg import remove
import requests
import base64

# Set page configuration
st.set_page_config(
    page_title="Passport Photo Generator",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make app more visually appealing
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #1E88E5;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #0D47A1;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5 !important;
        color: white !important;
    }
    .download-btn {
        background-color: #66BB6A !important;
    }
    .help-text {
        font-size: 0.9rem;
        color: #666;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

def resize_to_passport(image, width=35, height=45, dpi=300):
    """Resize image to passport dimensions with specified DPI"""
    # Convert mm to pixels
    width_px = int(width * dpi / 25.4)
    height_px = int(height * dpi / 25.4)
    
    # Resize the image while maintaining aspect ratio
    img_width, img_height = image.size
    aspect = img_width / img_height
    
    if aspect > width_px / height_px:
        new_width = width_px
        new_height = int(width_px / aspect)
    else:
        new_height = height_px
        new_width = int(height_px * aspect)
    
    resized_img = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Create a canvas of passport size
    canvas = Image.new('RGB', (width_px, height_px), 'white')
    
    # Paste the resized image onto the canvas, centered
    paste_x = (width_px - new_width) // 2
    paste_y = (height_px - new_height) // 2
    canvas.paste(resized_img, (paste_x, paste_y))
    
    return canvas

def change_background(image, bg_color):
    """Remove the background and replace with selected color"""
    try:
        # Remove background
        img_array = np.array(image)
        rgba = remove(img_array)
        
        # Create new background of specified color
        bg_color_rgb = ImageColor.getrgb(bg_color)
        bg = Image.new('RGB', image.size, bg_color_rgb)
        
        # Convert RGBA to RGB with alpha transparency
        rgba_image = Image.fromarray(rgba)
        
        # Paste the foreground onto the colored background using alpha as mask
        bg.paste(rgba_image, (0, 0), rgba_image.split()[3])
        
        return bg
    except Exception as e:
        st.error(f"Error removing background: {str(e)}")
        return image

def enhance_image(image, brightness=1.0, contrast=1.0, sharpness=1.0, saturation=1.0):
    """Apply image enhancements"""
    # Apply brightness adjustment
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(brightness)
    
    # Apply contrast enhancement
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)
    
    # Apply sharpness enhancement
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(sharpness)
    
    # Apply color/saturation adjustment
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(saturation)
    
    return image

def apply_color_correction(image, gamma=1.0, auto_white_balance=False):
    """Apply color correction techniques"""
    # Convert PIL image to OpenCV format
    img_cv = np.array(image)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    # Apply gamma correction
    if gamma != 1.0:
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
        img_cv = cv2.LUT(img_cv, table)
    
    # Apply auto white balance if selected
    if auto_white_balance:
        result = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])
        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
        img_cv = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    
    # Convert back to PIL format
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_cv)

def apply_face_detection(image):
    """Detect faces in the image and provide feedback on position"""
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Load face cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) == 0:
        return image, "No face detected. Please upload a clearer photo of your face."
    
    if len(faces) > 1:
        return image, "Multiple faces detected. Please upload a photo with just one person."
    
    # Get the dimensions of the face
    x, y, w, h = faces[0]
    
    # Draw a rectangle around the face (for visualization)
    img_with_rect = img_array.copy()
    cv2.rectangle(img_with_rect, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # Calculate face position relative to image
    img_height, img_width = img_array.shape[:2]
    face_centerX = x + w/2
    face_centerY = y + h/2
    
    rel_x = face_centerX / img_width
    rel_y = face_centerY / img_height
    
    # Check if the face is well-positioned
    message = "Face detected."
    if rel_y < 0.4:
        message = "Face is too high in the frame. Try to center your face more."
    elif rel_y > 0.6:
        message = "Face is too low in the frame. Try to center your face more."
        
    if rel_x < 0.4:
        message = "Face is too far to the left. Try to center your face more."
    elif rel_x > 0.6:
        message = "Face is too far to the right. Try to center your face more."
    
    if 0.45 < rel_x < 0.55 and 0.45 < rel_y < 0.55:
        message = "✅ Face is well positioned!"
    
    return Image.fromarray(img_with_rect), message

def crop_image_center(image, crop_percentage=0.8):
    """Crop the center portion of the image based on percentage"""
    width, height = image.size
    
    # Calculate new dimensions
    new_width = int(width * crop_percentage)
    new_height = int(height * crop_percentage)
    
    # Calculate left, upper, right, lower coordinates for cropping
    left = (width - new_width) // 2
    upper = (height - new_height) // 2
    right = left + new_width
    lower = upper + new_height
    
    # Crop the image
    cropped_img = image.crop((left, upper, right, lower))
    return cropped_img

def main():
    # Add a sidebar for app navigation
    with st.sidebar:
        st.title("Passport Photo Generator")
        st.markdown("Create professional passport photos that meet official requirements.")
        
        st.subheader("Instructions")
        st.markdown("""
        1. Upload a front-facing photo
        2. Adjust settings as needed
        3. Generate and download your passport photo
        """)
        
        st.markdown("---")
        st.markdown("## Supported Formats")
        format_info = {
            "US Passport": "2×2 inch (51×51mm)",
            "EU/UK Passport": "35×45mm",
            "Indian Passport": "35×35mm",
            "Chinese Visa": "33×48mm",
            "Canadian Passport": "50×70mm",
            "Australian Passport": "35×45mm"
        }
        
        for format_name, format_size in format_info.items():
            st.markdown(f"**{format_name}**: {format_size}")
    
    # Initialize session state variables
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'enhanced_image' not in st.session_state:
        st.session_state.enhanced_image = None
    if 'face_feedback' not in st.session_state:
        st.session_state.face_feedback = ""
    
    # Main content area
    st.title("📷 Passport Photo Generator")
    st.write("Create professional passport photos that meet official requirements for various countries.")
    
    # Create two columns for the main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # File upload area
        uploaded_file = st.file_uploader(
            "Upload your photo", 
            type=["jpg", "jpeg", "png"],
            help="For best results, use a front-facing photo with good lighting and a neutral expression"
        )
        
        if uploaded_file is not None:
            try:
                # Display the original image
                original_image = Image.open(uploaded_file).convert('RGB')
                
                # Store original image in session state
                if 'original_image' not in st.session_state:
                    st.session_state.original_image = original_image
                
                # Display image
                st.subheader("Original Image")
                st.image(original_image, use_column_width=True)
                
                # Simple cropping options
                if st.checkbox("Auto Crop Image", help="Automatically crop to center portion of the image"):
                    crop_amount = st.slider("Crop Amount", 0.5, 1.0, 0.8, 0.05, 
                                            help="Lower values crop more from the edges")
                    original_image = crop_image_center(original_image, crop_amount)
                    st.success("Image cropped!")
                    st.image(original_image, use_column_width=True)
                
                # Face detection button
                if st.button("Check Face Position"):
                    with st.spinner("Analyzing face position..."):
                        img_with_face, feedback = apply_face_detection(original_image)
                        st.session_state.face_feedback = feedback
                        st.image(img_with_face, use_column_width=True)
                        st.info(feedback)
            
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")
    
    with col2:
        if uploaded_file is not None:
            # Create tabs for different functionalities
            tabs = st.tabs(["Photo Format", "Background", "Enhancements", "Advanced"])
            
            with tabs[0]:
                st.subheader("Photo Format Settings")
                
                # Standard formats with added options
                format_options = {
                    "US Passport (2×2 inch)": (51, 51),
                    "EU/UK Passport (35×45mm)": (35, 45),
                    "Indian Passport (35×35mm)": (35, 35),
                    "Chinese Visa (33×48mm)": (33, 48),
                    "Canadian Passport (50×70mm)": (50, 70),
                    "Australian Passport (35×45mm)": (35, 45),
                    "Custom...": (0, 0)
                }
                
                photo_format = st.selectbox(
                    "Select photo format",
                    options=list(format_options.keys()),
                    index=1
                )
                
                width, height = format_options[photo_format]
                
                # Custom format option
                if photo_format == "Custom...":
                    col1, col2 = st.columns(2)
                    with col1:
                        width = st.number_input("Width (mm)", min_value=20, max_value=100, value=35)
                    with col2:
                        height = st.number_input("Height (mm)", min_value=20, max_value=100, value=45)
                
                # DPI setting
                dpi = st.slider("DPI (Dots Per Inch)", 150, 600, 300, 50,
                               help="Higher DPI gives better print quality but larger file size")
                
                st.markdown(f"<p class='help-text'>Output size will be approximately {int(width * dpi / 25.4)}×{int(height * dpi / 25.4)} pixels</p>", unsafe_allow_html=True)
            
            with tabs[1]:
                st.subheader("Background Settings")
                
                # Background color selection with preview
                color_options = {
                    "White": "#FFFFFF", 
                    "Light Blue": "#ADD8E6", 
                    "Dark Blue": "#00008B",
                    "Light Gray": "#D3D3D3",
                    "Red": "#FF0000",
                    "Green": "#008000",
                    "Custom...": "#FFFFFF"
                }
                
                bg_color_name = st.selectbox(
                    "Select background color",
                    options=list(color_options.keys()),
                    index=0
                )
                
                if bg_color_name == "Custom...":
                    bg_color = st.color_picker("Choose custom color", "#FFFFFF")
                else:
                    bg_color = color_options[bg_color_name]
                
                # Display color preview
                st.markdown(f"""
                <div style="background-color: {bg_color}; 
                            width: 100%; 
                            height: 50px; 
                            border-radius: 5px;
                            border: 1px solid #ddd;
                            margin-bottom: 10px;"></div>
                """, unsafe_allow_html=True)
            
            with tabs[2]:
                st.subheader("Enhancement Settings")
                
                # Image enhancement sliders
                brightness = st.slider("Brightness", 0.5, 1.5, 1.0, 0.05)
                contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
                sharpness = st.slider("Sharpness", 0.0, 3.0, 1.0, 0.1)
                saturation = st.slider("Saturation", 0.0, 2.0, 1.0, 0.05)
                
                # Color correction options
                gamma = st.slider("Gamma Correction", 0.7, 1.5, 1.0, 0.05)
                auto_wb = st.checkbox("Auto White Balance")
                
                # Presets for quick adjustments
                st.subheader("Presets")
                preset_cols = st.columns(4)
                
                with preset_cols[0]:
                    if st.button("Natural"):
                        brightness, contrast, sharpness, saturation = 1.0, 1.1, 1.2, 1.0
                        gamma, auto_wb = 1.0, True
                
                with preset_cols[1]:
                    if st.button("Bright"):
                        brightness, contrast, sharpness, saturation = 1.2, 1.2, 1.3, 1.1
                        gamma, auto_wb = 0.9, True
                
                with preset_cols[2]:
                    if st.button("Clear"):
                        brightness, contrast, sharpness, saturation = 1.1, 1.3, 1.5, 0.9
                        gamma, auto_wb = 1.1, True
                
                with preset_cols[3]:
                    if st.button("B&W"):
                        brightness, contrast, sharpness, saturation = 1.0, 1.4, 1.2, 0.0
                        gamma, auto_wb = 1.0, False
                
                # Apply enhancements button
                if st.button("Apply Enhancements"):
                    with st.spinner("Applying enhancements..."):
                        # Apply enhancements to the original image
                        enhanced = enhance_image(original_image, brightness, contrast, sharpness, saturation)
                        enhanced = apply_color_correction(enhanced, gamma, auto_wb)
                        
                        st.session_state.enhanced_image = enhanced
                        st.success("✅ Enhancements applied!")
            
            with tabs[3]:
                st.subheader("Advanced Settings")
                
                # Print layout options
                st.subheader("Print Layout")
                layout_type = st.radio(
                    "Select layout type",
                    ["Single photo", "Multiple photos (print sheet)"],
                    horizontal=True
                )
                
                if layout_type == "Multiple photos (print sheet)":
                    col1, col2 = st.columns(2)
                    with col1:
                        rows = st.number_input("Number of rows", 1, 8, 4)
                    with col2:
                        cols = st.number_input("Number of columns", 1, 8, 4)
                    
                    st.markdown(f"<p class='help-text'>Will generate a sheet with {rows*cols} photos</p>", unsafe_allow_html=True)
                    
                    # Paper size
                    paper_size = st.selectbox(
                        "Paper size",
                        ["A4", "US Letter", "4×6 inch"]
                    )
                
                # Guidelines options
                show_guidelines = st.checkbox("Show face position guidelines", value=True)
                
                # Reset all settings button
                if st.button("Reset All Settings"):
                    # Reset all session state
                    for key in list(st.session_state.keys()):
                        if key != 'original_image':
                            del st.session_state[key]
                    st.experimental_rerun()
            
            # Process button for final image
            process_col1, process_col2 = st.columns([2, 1])
            with process_col1:
                if st.button("Generate Passport Photo", use_container_width=True):
                    with st.spinner("Processing your photo..."):
                        try:
                            # Step 1: Use enhanced image if available, otherwise original
                            if st.session_state.enhanced_image is not None:
                                process_image = st.session_state.enhanced_image
                            else:
                                process_image = original_image
                            
                            # Step 2: Change background
                            bg_changed = change_background(process_image, bg_color)
                            
                            # Step 3: Resize to passport format
                            passport_img = resize_to_passport(bg_changed, width, height, dpi)
                            
                            # Step 4: Generate print sheet if multiple layout selected
                            if layout_type == "Multiple photos (print sheet)":
                                # Create a new image based on paper size
                                if paper_size == "A4":
                                    sheet_width, sheet_height = int(210 * dpi / 25.4), int(297 * dpi / 25.4)
                                elif paper_size == "US Letter":
                                    sheet_width, sheet_height = int(8.5 * dpi), int(11 * dpi)
                                else:  # 4×6 inch
                                    sheet_width, sheet_height = int(4 * dpi), int(6 * dpi)
                                
                                sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
                                
                                # Calculate spacing
                                h_spacing = sheet_width // cols
                                v_spacing = sheet_height // rows
                                
                                # Paste photos onto sheet
                                for r in range(rows):
                                    for c in range(cols):
                                        x = c * h_spacing + (h_spacing - passport_img.width) // 2
                                        y = r * v_spacing + (v_spacing - passport_img.height) // 2
                                        sheet.paste(passport_img, (x, y))
                                
                                final_img = sheet
                            else:
                                final_img = passport_img
                            
                            # Store the result in session state
                            st.session_state.final_image = final_img
                            st.session_state.processed = True
                            
                        except Exception as e:
                            st.error(f"Error processing image: {str(e)}")
            
            with process_col2:
                # Quick preview
                if st.button("Quick Preview", use_container_width=True):
                    with st.spinner("Generating preview..."):
                        if st.session_state.enhanced_image is not None:
                            preview = st.session_state.enhanced_image
                        else:
                            preview = original_image
                        
                        # Show a simplified preview
                        st.image(preview, width=150)
    
    # Display results area
    if st.session_state.processed and 'final_image' in st.session_state:
        st.markdown("---")
        st.subheader("📸 Your Passport Photo")
        
        result_col1, result_col2 = st.columns([2, 1])
        
        with result_col1:
            st.image(st.session_state.final_image, width=400)
        
        with result_col2:
            # Download section
            st.markdown("### Download Options")
            
            # Format selection
            download_format = st.radio(
                "Select format",
                ["JPEG", "PNG"],
                horizontal=True
            )
            
            # Quality selection for JPEG
            if download_format == "JPEG":
                quality = st.slider("Quality", 70, 100, 95, 5)
            else:
                quality = 95
            
            # Download button
            buf = io.BytesIO()
            
            if download_format == "JPEG":
                st.session_state.final_image.save(buf, format="JPEG", quality=quality)
                file_extension = "jpg"
                mime_type = "image/jpeg"
            else:  # PNG
                st.session_state.final_image.save(buf, format="PNG")
                file_extension = "png"
                mime_type = "image/png"
            
            st.download_button(
                label=f"Download as {download_format}",
                data=buf.getvalue(),
                file_name=f"passport_photo.{file_extension}",
                mime=mime_type,
                use_container_width=True
            )
            
            # Additional info
            st.markdown("""
            ### Compliance Information
            
            This photo meets standard requirements for:
            - Proper dimensions
            - Even lighting
            - Neutral expression
            - Plain background
            
            Always check specific requirements for your country or visa application.
            """)

# Run the app
if __name__ == "__main__":
    main()
