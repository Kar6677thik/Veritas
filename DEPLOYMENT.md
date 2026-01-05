# Deployment Guide for Veritas

Veritas uses a **Split Deployment Architecture**:
1.  **Backend (API + Agents)**: Deployed on a container service execution (like **Render** or **Google Cloud Run**) because it performs long-running tasks (>60s) that would time out on serverless functions.
2.  **Frontend (React UI)**: Deployed on **Vercel** for optimal performance and edge caching.

---

## 🏗️ Step 1: Deploy Backend (Render)

We recommend [Render.com](https://render.com) for the backend as it offers a free tier for Docker containers.

1.  **Push your code to GitHub**.
2.  Go to [Render Dashboard](https://dashboard.render.com).
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repository.
5.  **Configuration**:
    *   **Name**: `veritas-backend`
    *   **Runtime**: **Docker** (This is crucial! Do not select Python)
    *   **Region**: Closest to you (e.g., Oregon)
    *   **Instance Type**: Free (or Starter for better performance)
6.  **Environment Variables**:
    *   Add `GOOGLE_API_KEY`: `your_gemini_api_key_here`
7.  Click **Create Web Service**.
8.  **Wait for Build**: It will take a few minutes to build the Docker image.
9.  **Copy URL**: Once live, copy the URL (e.g., `https://veritas-backend.onrender.com`).

---

## ⚡ Step 2: Deploy Frontend (Vercel)

1.  Go to [Vercel Dashboard](https://vercel.com/dashboard).
2.  Click **Add New...** -> **Project**.
3.  Import the same GitHub repository.
4.  **Framework Preset**: Select **Vite**.
5.  **Root Directory**: Click "Edit" and select `frontend`.
6.  **Environment Variables**:
    *   Name: `VITE_API_URL`
    *   Value: The **Backend URL** from Step 1 (e.g., `https://veritas-backend.onrender.com`).
    *   *Note: Do not add a trailing slash.*
7.  Click **Deploy**.

---

## ✅ Verification

1.  Visit your Vercel URL (e.g., `https://veritas-app.vercel.app`).
2.  Click **"Get Started"** -> **"Start Analysis"**.
3.  Upload a paper.
4.  If the agents start processing in the graph, the connection is successful!

## 🔧 Troubleshooting

*   **CORS Error**: The backend is configured to allow all origins (`*`) by default, so this shouldn't happen. If it does, verify the backend URL in Vercel settings.
*   **Timeout / 504**: If using Vercel Serverless for backend (not recommended), agents might time out. This is why we use Render for the backend.
