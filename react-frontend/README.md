# SteelVision AI frontend

React/Vite frontend for the existing FastAPI, YOLO, OpenCV, SQLite, and ReportLab application. The frontend does not access SQLite or calculate inspection results.

## Local development

1. Start the backend from the repository root:

   ```powershell
   .\venv\Scripts\Activate.ps1
   python backend/main.py
   ```

2. Start the frontend:

   ```powershell
   cd react-frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173`. Set `VITE_API_BASE_URL` in `.env` when the backend runs elsewhere. Only the API base URL belongs in the frontend environment.

## Real API contract

All routes below except `/health`, `/api/auth/login`, and `/api/camera/stream` require the JWT returned by login as `Authorization: Bearer <token>`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Backend, database, model, and camera status |
| POST | `/api/auth/login` | Validate `{ username, password }` and return JWT |
| POST | `/api/auth/logout` | End the client session (JWT is stateless) |
| GET | `/api/inspections?page=&limit=&status=&severity=&search=` | Paginated inspection history |
| GET | `/api/inspections/{inspection_id}` | Inspection details and saved image URL |
| GET | `/api/images/{inspection_id}` | Saved annotated inspection JPEG |
| GET | `/api/reports` | Reports generated for inspections |
| GET | `/api/reports/{inspection_id}/download` | Generate on demand or download the real PDF |
| GET | `/api/analytics/summary` | Inspection totals, rates, and averages |
| GET | `/api/analytics/status-distribution` | Status counts |
| GET | `/api/analytics/severity-distribution` | Severity counts |
| GET | `/api/analytics/defect-distribution` | Defect class counts |
| GET | `/api/analytics/quality-trend` | Quality score by inspection |
| GET | `/api/analytics/defect-trend` | Defects grouped by parsed date |
| GET | `/api/analytics/daily-volume` | Inspections grouped by parsed date |
| GET | `/api/camera/status` | Camera state and latest YOLO detection |
| POST | `/api/camera/start` | Open the real OpenCV camera and load YOLO |
| POST | `/api/camera/stop` | Stop the camera service |
| POST | `/api/camera/capture` | Save the latest annotated frame and database record |
| GET | `/api/camera/stream` | Real MJPEG annotated camera stream |

The backend stores timestamps as `DD-MM-YYYY HH:MM:SS`; analytics date grouping parses that format explicitly.

## Validation

- `npm run build` creates the production bundle.
- `npm run lint` checks the React source.
- `python -m compileall -q backend` checks backend syntax.

The current `/health` check should report database `online` and model `ready` when the local environment is configured. Camera status depends on an available OpenCV device.

## Deployment preparation

Build with the target backend URL:

```powershell
$env:VITE_API_BASE_URL = 'https://your-real-backend.example.com'
npm run build
```

The generated `dist/` directory can be hosted by S3/CloudFront or Amplify. Configure the deployed origin in FastAPI CORS before production use. No AWS deployment is performed by this project until explicitly requested.
