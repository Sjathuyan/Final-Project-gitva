
# GITVA Photo Print Studio

### MSc Computer Science (Conversion) – Final Project
**University:** The University of Law  
**Project:** GITVA Photo Print Studio  
**GitHub Repository:** Final-Project-gitva

## 1. Project Overview

GITVA Photo Print Studio is a web-based photo editing and personalised print design application developed as part of the MSc Computer Science (Conversion) final project at The University of Law.

The main aim of this project is to simplify photo editing and print design tasks through a user-friendly interface.

The application allows users to upload photographs, create personalised designs, remove image backgrounds using machine learning, select Photoshop PSD templates, and generate print-ready design images.

The system is developed using Python, FastAPI, HTML, CSS, JavaScript, and image processing libraries.

## 2. Project Objectives

- Develop a user-friendly photo editing and print design application.
- Automate background removal using machine learning.
- Support personalised print designs.
- Integrate Photoshop PSD templates.
- Provide colour analysis and theme selection.
- Reduce manual editing time.
- Demonstrate the integration of frontend and backend technologies.

## 3. Main Features

### Photo Upload
Users can upload JPG and PNG photographs for processing.

### Background Removal
The application uses the rembg library and a machine learning model to remove image backgrounds automatically.

### Personalised Print Designs
Users can select products, choose themes, add text, and generate personalised print designs.

### Photoshop PSD Templates
The system includes 27 PSD design templates across 8 categories.

### Colour Analysis
The application uses K-Means clustering to analyse dominant colours in photographs.

### Mug Preview
Users can preview their personalised designs on a mug.

### Batch Rendering
The system supports generating designs for multiple product sizes.

### Image Download
Users can download generated designs in PNG format.

## 4. Technologies Used

### Backend
- Python
- FastAPI
- Uvicorn

### Frontend
- HTML
- CSS
- JavaScript

### Image Processing
- Pillow
- NumPy
- rembg
- psd-tools
- scikit-learn

### Version Control
- Git
- GitHub
- Git Large File Storage (Git LFS)

## 5. System Requirements

- Windows 10 or Windows 11
- Python 3.12 (64-bit recommended)
- Internet connection for initial installation
- Approximately 2–3 GB of available storage
- Google Chrome or Microsoft Edge

Python 3.12 is recommended because newer Python versions may cause compatibility issues with the background removal library.

## 6. Installation Instructions

### Step 1: Download the Project

Clone the GitHub repository:

```bash
git lfs install
git clone https://github.com/Sjathuyan/Final-Project-gitva.git
```

Alternatively, download the repository and extract the ZIP file. Git LFS may be required to retrieve the complete PSD files.

### Step 2: Open the Project Folder

Navigate to the PhotoProject directory.

Open Command Prompt inside the PhotoProject folder.

### Step 3: Check Python Installation

```bash
python --version
```

Python 3.12 is recommended.

### Step 4: Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

```bash
venv\Scripts\activate
```

### Step 5: Install Required Libraries

Update pip:

```bash
python -m pip install --upgrade pip
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Make sure the requirements.txt file is available inside the PhotoProject folder.

### Step 6: Start the Application

Run the FastAPI backend server:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Wait until the terminal displays:

Application startup complete.

### Step 7: Open the Application

Open Google Chrome or Microsoft Edge.

Enter the following address:

http://localhost:8000

The GITVA Photo Print Studio interface will open.

Keep the Command Prompt window running while using the application.

## 7. How to Use the Application

1. Start the FastAPI backend server.
2. Open http://localhost:8000.
3. Upload a JPG or PNG photograph.
4. Select a product and design theme.
5. Enter personalised text.
6. Click Render to generate the design.
7. Preview the result.
8. Download the generated PNG image.
9. Explore the Templates tab for PSD designs.
10. Use the Mug tab to preview designs on a mug.

## 8. Project Folder Structure

```text
PhotoProject/
│
├── app/
│   ├── main.py
│   ├── routers/
│   └── core/
│
├── static/
│   └── index.html
│
├── Set 1/
│   └── PSD Design Templates
│
├── Set2/
│   └── Sample Photographs
│
├── output/
│
├── backend/
│
├── gen_thumbs.py
│
├── requirements.txt
│
└── start.bat
```

## 9. Troubleshooting

### Application Not Opening

Make sure the FastAPI server is running.

Check that the browser address is:

http://localhost:8000

### ModuleNotFoundError

Activate the virtual environment and reinstall dependencies:

```bash
venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Background Removal Not Working

- Use Python 3.12.
- Check the internet connection.
- Allow the machine learning model to download during first use.
- Ensure the required libraries are installed correctly.

### PSD Templates Not Appearing

Make sure the "Set 1" folder is located inside the PhotoProject directory.

If template preview images are missing, run:

```bash
python gen_thumbs.py
```

### Port 8000 Already in Use

Start the application on another port:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

Then open:

http://localhost:8001

## 10. Known Limitations

- Large image files may require additional processing time.
- Some Photoshop PSD files may have compatibility limitations.
- Background removal depends on the successful installation of the machine learning libraries.
- The initial background removal model download requires an internet connection.
- The application is an academic prototype and may require further improvements for production use.

## 11. Future Improvements

- Improve PSD template compatibility.
- Add more personalised print templates.
- Improve image processing performance.
- Enhance the user interface.
- Introduce additional automated editing features.
- Explore cloud deployment.

## 12. Academic Information

**Project Title:** GITVA Photo Print Studio

**Programme:** MSc Computer Science (Conversion)

**University:** The University of Law

**Project Type:** Final MSc Project

**GitHub Repository:** https://github.com/Sjathuyan/Final-Project-gitva

## 13. Conclusion

GITVA Photo Print Studio demonstrates the practical application of web development, Python programming, image processing, and machine learning in a personalised print design system.

The project aims to provide a simple and accessible solution for creating personalised photo-based print designs.

---

**Developed for academic purposes as part of the MSc Computer Science (Conversion) programme at The University of Law.**
