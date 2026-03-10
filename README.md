# Cypress to Playwright Conversion Agent

## Overview

The Cypress to Playwright Conversion Agent is an AI-assisted web application that automates the conversion of Cypress end-to-end (e2e) tests to Playwright tests. It uses Google's Gemini AI to analyze Cypress test files, understand their structure and logic, and generate equivalent Playwright test code with proper syntax and best practices.

This repository contains the full-stack application (FastAPI backend + HTML/JavaScript frontend) and helper logic to run the conversion workflow locally.

## Technologies

- **Backend / API**: FastAPI (Python)
- **Database**: MongoDB (via Motor async driver)
- **AI / LLM**: Google Vertex AI integration (gemini-2.5-pro for test conversion)
- **Frontend**: Vanilla HTML/JavaScript with CodeMirror for code editing
- **Configuration**: Environment variables via .env

## Prerequisites

- Python 3.8 or higher (3.10+ recommended)
- pip package manager
- Git (for cloning repository)
- Google Cloud Vertex AI access and a service account JSON
- MongoDB instance (local or cloud)

## Usage

### Clone the repository

```bash
git clone https://github.com/Krishna-Teja-Vinnakota/cypress-to-playwright-conversion-agent.git
cd cypress-to-playwright-conversion-agent
```

### Create and activate a virtual environment (recommended)

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python -m venv .venv
source .venv/bin/activate
```

### Install required packages

```bash
pip install -r requirements.txt
```

### Configure credentials and environment

Set required environment variables in a `.env` file or update `backend/config.py`. Required variables:

- `GOOGLE_CLOUD_PROJECT` — Google Cloud Project ID
- `GOOGLE_APPLICATION_CREDENTIALS` — path to Google service account JSON
- `VERTEX_AI_LOCATION` — Google Cloud Location (e.g., us-central1)
- `MONGO_URI` — MongoDB connection URI

### Start the application

```bash
cd backend
python run.py
```

Open your browser and navigate to `http://localhost:8000`.

### Using the Application

1. **Upload Cypress Test**: Upload your Cypress `.cy.ts` or `.cy.js` test file through the web interface.
2. **Convert Test**: Click "Convert" to let the AI analyze and convert your test to Playwright format.
3. **Review & Download**: Review the generated Playwright test code, make any necessary adjustments, and download the converted test file.

## Output and Persistence

- **Converted Tests**: Downloadable Playwright test files (`.spec.ts`) with proper TypeScript syntax
- **Session Management**: Temporary sessions stored in MongoDB for tracking conversion history
- **Template Support**: Pre-configured templates for both Cypress and Playwright project structures

## Example Quick Usage

1. Clone repo and create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS`, `VERTEX_AI_LOCATION`, and `MONGO_URI` in `.env`
4. Run `cd backend && python run.py` and open `http://localhost:8000`
5. Upload a Cypress test file and click convert to get the Playwright equivalent.