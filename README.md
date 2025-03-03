# 📷 Passport Photo Generator

A Streamlit web application that allows users to create professional passport photos that meet official requirements for various countries.

![Passport Photo Generator](https://i.imgur.com/iMmyeKr.png)

## Features

- **Multiple Passport Formats**: Supports US, EU/UK, Indian, Chinese, Canadian, Australian, and custom formats
- **Background Replacement**: Choose from preset colors or pick a custom background color
- **Face Detection**: Check if your face is properly positioned according to requirements
- **Image Enhancement**: Adjust brightness, contrast, sharpness, and saturation
- **Color Correction**: Apply gamma correction and auto white balance
- **Multiple Layout Options**: Generate single photos or print sheets with multiple copies
- **Export Options**: Download in JPEG, PNG, or PDF format
- **Manual Cropping**: Crop your image to focus on the face area
- **Enhancement Presets**: Quick adjustment presets for different styles

## Installation

1. Clone this repository:
```
git clone https://github.com/imomair1/passport-photo-generator.git
cd passport-photo-generator
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```
pip install -r requirements.txt
```

4. Run the app:
```
streamlit run passport.py
```

## Usage

1. Upload a front-facing photo with good lighting
2. Adjust the format settings for your specific passport or visa requirements
3. Customize the background color
4. Apply image enhancements if needed
5. Generate the passport photo
6. Download in your preferred format

## Requirements

The application requires the following Python packages:
- streamlit
- Pillow
- numpy
- opencv-python
- rembg
- streamlit-image-coordinates
- reportlab
- requests

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web app framework
- [rembg](https://github.com/danielgatis/rembg) for background removal
- [OpenCV](https://opencv.org/) for image processing capabilities
