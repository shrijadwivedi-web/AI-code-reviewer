# AI Code Reviewer

A premium, full-stack application that analyzes GitHub repositories and pull requests to surface code quality issues, technical debt, and actionable AI-powered suggestions.

![AI Code Reviewer Banner](https://via.placeholder.com/1200x500.png?text=AI+Code+Reviewer)

## ✨ Features

- **Automated Static Analysis**: Detects large functions, deep nesting, magic numbers, and long files across 10+ languages (Python, JS/TS, Go, Java, and more).
- **AI-Powered Insights**: Uses Google Gemini 1.5 Flash to understand the context of issues and suggest precise, actionable refactoring examples.
- **Pull Request Context**: Analyze a specific PR URL to review only the changed files.
- **Premium UI**: Built with React, Framer Motion, and Tailwind CSS for a stunning dark-mode aesthetic with glassmorphic elements.
- **Quality Scoring**: Computes a codebase health score (0-100) based on severity-weighted penalties.

## 🛠 Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Framer Motion, TanStack Query, Axios
- **Backend**: Python, FastAPI, Pydantic, PyGithub
- **AI**: Google Generative AI (Gemini 1.5 Flash)
- **Deployment**: Ready for Vercel (Frontend) and Render (Backend)

---

## 🚀 Quick Start (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/ai-code-reviewer.git
cd ai-code-reviewer
```

### 2. Setup the Backend
The backend requires Python 3.10+.
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend` folder:
```env
# backend/.env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
ALLOWED_ORIGINS=http://localhost:5173
```
*Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com).*

Start the backend server:
```bash
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000/docs`.

### 3. Setup the Frontend
Open a new terminal window.
```bash
cd frontend
npm install
npm run dev
```
The app will be available at `http://localhost:5173`.

---

## 🏗 Architecture & Repository Structure

The application follows a clean separation of concerns:

- `frontend/src/components`: UI components built with React and Framer Motion.
- `frontend/src/api`: Axios client communicating with the backend.
  
- `backend/services/github_service.py`: Safely fetches repository files and PR diffs.
- `backend/services/analyzer.py`: Language-agnostic heuristic engine.
- `backend/services/ai_service.py`: Generates the prompt and parses structured JSON from Gemini.
- `backend/routers/`: FastAPI routes (`/analyze-repo`, `/analyze-pr`).

## ☁️ Deployment Guide

### Backend (Render)
1. Push the repository to GitHub.
2. Go to [Render](https://render.com) and create a new **Web Service**.
3. Connect your repository and select the `backend` folder as the Root Directory.
4. Render will automatically detect the `render.yaml` configuration.
5. Add `GEMINI_API_KEY` and `GITHUB_TOKEN` to your Environment Variables in the Render dashboard.

### Frontend (Vercel)
1. Go to [Vercel](https://vercel.com) and import the repository.
2. Set the Root Directory to `frontend`.
3. Update `vercel.json` with your new Render backend URL.
4. Deploy!

## 📄 License
MIT License.
