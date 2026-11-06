# AI-Powered Defect Detection System

An AI-based industrial quality inspection system that detects and classifies surface defects in different materials using **YOLO object detection models**. The system supports image-based and camera-based inspection, material validation, defect classification, inspection result management, analytics, and PDF report generation.

---

## 1. Project Overview

Quality inspection is an important process in manufacturing industries. Traditional manual inspection requires time and continuous human effort, and defects may sometimes be overlooked.

To address these challenges, we developed an **AI-Powered Defect Detection System** that uses deep learning and computer vision to automate the inspection process.

The system uses separate YOLO models trained for different material categories:

- Steel
- Metal
- Fabric
- Printed Circuit Boards (PCB)
- Welding

Users can upload an image or capture an image through a camera. The system processes the input using the selected material-specific YOLO model and identifies possible defects.

The inspection result includes detected defect names, confidence scores, bounding boxes, and an overall inspection decision.

The system also provides user authentication, inspection history, a dashboard, analytics, and downloadable PDF reports.

## 2. Objectives

- Automate the industrial quality inspection process.
- Detect surface defects using deep learning.
- Support multiple material categories.
- Identify and classify different types of defects.
- Support image upload and camera-based inspection.
- Validate images before performing defect detection.
- Display defect locations using bounding boxes.
- Generate inspection decisions based on detected defects.
- Maintain inspection records in a database.
- Provide dashboard visualizations and inspection analytics.
- Generate downloadable PDF inspection reports.
- Reduce manual inspection effort and support consistent inspection workflows.

## 3. Technologies Used

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | React.js, JavaScript, HTML, CSS |
| Frontend Build Tool | Vite |
| Backend Framework | FastAPI |
| AI / Deep Learning | YOLOv8, Ultralytics |
| Computer Vision | OpenCV |
| Image Processing | NumPy |
| Database | SQLite |
| Authentication | JWT, PBKDF2-HMAC-SHA256 |
| API Communication | REST API, Axios |
| Data Visualization | Plotly |
| PDF Generation | ReportLab |
| Development Environment | Visual Studio Code |
| Version Control | Git and GitHub |

## 4. System Architecture

The system follows a frontend-backend architecture.

```text
             USER
               |
               v
       REACT FRONTEND
               |
       Image Upload / Camera
               |
               v
         FASTAPI BACKEND
               |
               v
       IMAGE VALIDATION
               |
       Material Selection
               |
               v
       YOLO MODEL SELECTION
               |
     +---------+---------+
     |         |         |
   STEEL     METAL     FABRIC
   MODEL     MODEL     MODEL
     |         |         |
     +---------+---------+
               |
       +-------+-------+
       |               |
      PCB           WELDING
     MODEL           MODEL
       |               |
       +-------+-------+
               |
               v
       DEFECT DETECTION
               |
     Defect Name / Confidence
        Bounding Boxes
               |
               v
       RESULT CLASSIFICATION
               |
       PASS / REWORK / FAIL
               |
               v
        SQLITE DATABASE
               |
       +-------+--------+
       |       |        |
    HISTORY DASHBOARD REPORTS
                       |
                       v
                  PDF REPORT
```

## 5. Material Categories and Defect Classes

The system uses five separate YOLO models for material-specific defect detection.

### 5.1 Steel Defect Detection

Model path:

`steel_defect_model/weights/best.pt`

Supported defect classes:

- Scratches
- Dents
- Rust
- Other

### 5.2 Metal Defect Detection

Model path:

`metal_surface_model/weights/best.pt`

Supported defect classes:

- Inclusion
- Oil Spot
- Punching Hole
- Silk Spot
- Water Spot
- Welding Line

### 5.3 Fabric Defect Detection

Model path:

`fabrics_defect_model/weights/best.pt`

Supported defect classes:

- Color Bleeding
- Crease
- Hole

### 5.4 PCB Defect Detection

Model path:

`pcb_boards_model/weights/best.pt`

Supported defect classes:

- Missing Hole
- Mouse Bite
- Open Circuit
- Short
- Spur
- Spurious Copper

### 5.5 Welding Defect Detection

Model path:

`welding_defect_model/weights/best.pt`

Supported model classes:

- Bad Weld
- Good Weld

**Note:** The welding model distinguishes between good and bad weld classifications. Its interpretation should be handled separately from the defect-count rules used for the other material categories.

## 6. How the System Works

The system follows these steps:

### Step 1: User Authentication

The user registers or logs in using their account credentials.

The backend verifies the credentials and provides a JWT authentication token for authorized access.

### Step 2: Select Material

The user selects the material category to inspect:

- Steel
- Metal
- Fabric
- PCB
- Welding

### Step 3: Upload or Capture Image

The user can provide an image through:

- Image upload.
- Camera-based inspection.

### Step 4: Image Validation

Before defect detection, the backend performs basic image validation.

It checks image characteristics such as:

- Image quality.
- Image sharpness.
- Image entropy.
- Edge information.
- Possible blank or featureless images.

The system can reject invalid images and flag material mismatches when detected by its validation logic.

### Step 5: YOLO Model Selection

Based on the selected material, the backend loads or uses the corresponding trained YOLO model.

For example:

- Steel selection → Steel YOLO model.
- Metal selection → Metal YOLO model.
- Fabric selection → Fabric YOLO model.
- PCB selection → PCB YOLO model.
- Welding selection → Welding YOLO model.

### Step 6: Defect Detection

The selected YOLO model processes the input image and identifies possible defects.

The output includes:

- Defect classification.
- Confidence score.
- Bounding box coordinates.
- Annotated image showing detected regions.

### Step 7: Inspection Decision

For the standard defect-count-based material inspection workflow, the system uses the following project-specific decision rules:

| Detected Defects | Inspection Result |
|---|---|
| 0 defects | PASS |
| 1 defect | REWORK |
| 2 or more defects | FAIL |

These thresholds are project-defined rules and are not universal industrial quality standards.

### Step 8: Store Inspection Details

The backend stores inspection information in the SQLite database.

Stored information can include:

- Material category.
- Inspection date and time.
- Defect names.
- Confidence scores.
- Inspection result.
- Image references.

### Step 9: Dashboard and Analytics

The dashboard displays inspection information such as:

- Total inspections.
- PASS results.
- REWORK results.
- FAIL results.
- Material-wise inspection information.
- Defect statistics.
- Inspection history.

### Step 10: PDF Report Generation

The system generates downloadable PDF inspection reports containing available inspection details, defect information, and inspection results.

## 7. Main Modules

### 7.1 Authentication Module

- User registration.
- User login.
- Password hashing.
- JWT-based authentication.
- User logout.
- Protected application routes.

### 7.2 Material Selection Module

- Supports five material categories.
- Selects the corresponding YOLO model.
- Provides material-specific inspection workflows.

### 7.3 Image Validation Module

- Checks image quality.
- Detects blank or featureless images.
- Performs material validation checks.
- Helps prevent invalid inspection inputs.

### 7.4 Defect Detection Module

- Uses YOLO object detection.
- Identifies material-specific defects.
- Generates confidence scores.
- Displays bounding boxes around detected regions.

### 7.5 Inspection Decision Module

- Evaluates detected defects.
- Generates PASS, REWORK, or FAIL results using the defined project rules.
- Maintains inspection results.

### 7.6 Dashboard Module

- Displays inspection summaries.
- Provides material-wise statistics.
- Displays result distributions.
- Supports visual analysis of inspection records.

### 7.7 Inspection History Module

- Stores previous inspection records.
- Allows users to view inspection details.
- Supports tracking of previous results.

### 7.8 PDF Report Module

- Generates inspection reports.
- Displays available defect information.
- Includes inspection results.
- Supports PDF downloading.

### 7.9 Camera Inspection Module

- Supports camera-based image capture.
- Sends captured images for backend processing.
- Displays inspection results.

## 8. Database

The project uses **SQLite** as its database.

SQLite stores the application's inspection and related records without requiring a separate database server.

The database supports information related to:

- User accounts.
- Authentication.
- Inspection records.
- Material categories.
- Defect information.
- Inspection results.
- Image references.

## 9. Backend API

The backend is developed using FastAPI.

Important authentication endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Authenticate a user |
| POST | `/api/auth/logout` | Logout |

The application also provides material-specific inspection, analytics, history, image, and report endpoints.

The exact available routes can be checked through the FastAPI Swagger documentation.

Open:

`http://127.0.0.1:8000/docs`

## 10. Project Folder Structure

The following is a simplified logical representation. Actual filenames and folders may differ in the repository.

```text
quality-inspection-system/
│
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── auth/
│   ├── services/
│   ├── database/
│   └── reports/
│
├── react-frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── assets/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── steel_defect_model/
│   └── weights/
│       └── best.pt
│
├── metal_surface_model/
│   └── weights/
│       └── best.pt
│
├── fabrics_defect_model/
│   └── weights/
│       └── best.pt
│
├── pcb_boards_model/
│   └── weights/
│       └── best.pt
│
├── welding_defect_model/
│   └── weights/
│       └── best.pt
│
├── reports/
├── material_classification_dataset/
├── .venv/
├── requirements.txt
└── README.md
```

## 11. Installation and Setup

### Prerequisites

Install the following software:

- Python 3.10 or compatible project-supported version.
- Node.js and npm.
- Visual Studio Code.
- Git.
- Required YOLO model weight files.

### Step 1: Clone the Repository

```bash
git clone https://github.com/khushi-k-m/quality-inspection-system.git
```

### Step 2: Open the Project

```bash
cd quality-inspection-system
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

### Step 4: Activate the Virtual Environment

For Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

### Step 5: Install Python Dependencies

```cmd
pip install -r requirements.txt
```

### Step 6: Start the Backend

From the project root:

```cmd
uvicorn backend.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### Step 7: Install Frontend Dependencies

Open another terminal:

```cmd
cd react-frontend
npm install
```

### Step 8: Start the Frontend

```cmd
npm run dev
```

Frontend URL:

`http://localhost:5173`

**Important:** The YOLO weight files must be available at the configured model paths. Also configure any required environment variables or secrets before running the application.

## 12. Security Features

The application uses authentication and password protection mechanisms.

- Password hashing using PBKDF2-HMAC-SHA256.
- Random salt for password hashing.
- JWT-based authentication.
- Token expiration.
- Protected API access.
- Authenticated frontend requests.

The application uses an eight-hour JWT expiration configuration.

## 13. Advantages

- Automates important parts of quality inspection.
- Supports multiple industrial material categories.
- Uses separate trained models for different materials.
- Detects and classifies defects automatically.
- Displays defect locations using bounding boxes.
- Provides confidence scores for detections.
- Supports camera and image-upload workflows.
- Maintains inspection records.
- Provides dashboard analytics.
- Generates PDF reports.
- Uses a modular backend architecture.
- Can be extended with additional material categories and models.

## 14. Limitations

- Detection performance depends on model training data and image quality.
- Lighting, camera position, and background objects may affect predictions.
- False-positive and false-negative detections may occur.
- Material validation requires further improvement and testing.
- Inspection results should be verified before making critical industrial decisions.
- Actual model accuracy must be established through a properly labelled test dataset.

## 15. Future Enhancements

- Develop a dedicated Android application.
- Improve material classification and validation.
- Reduce false-positive detections.
- Improve real-time camera processing speed.
- Add more material categories.
- Expand and verify the human-reviewed training dataset.
- Improve model performance using validated training data.
- Add role-based access control.
- Add cloud-based inspection data storage.
- Provide advanced inspection analytics.
- Support production-level deployment and monitoring.

## 16. Project Team

**Project Title:** AI-Powered Defect Detection System

**Department:** Computer Science and Engineering

**Institution:** KVG College of Engineering, Sullia

**Technology Domain:** Artificial Intelligence, Deep Learning, Computer Vision, Web Development

## 17. Conclusion

The AI-Powered Defect Detection System demonstrates how deep learning and computer vision can support automated industrial quality inspection.

By integrating YOLO-based defect detection models with a React frontend, FastAPI backend, and SQLite database, the system provides a centralized platform for material selection, image inspection, defect identification, result classification, inspection history, analytics, and PDF report generation.

The project provides a foundation for improving inspection workflows and can be further enhanced through better validation, verified training datasets, model optimization, and mobile application development.

---

## 18. Author

**GitHub:** [Kruthi](https://github.com/Kruthinayak)

**Repository:** [AI-Powered Defect Detection System](https://github.com/khushi-k-m/quality-inspection-system)
