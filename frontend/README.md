# Frontend — ESTÜ Akademik Asistan

> 🚧 **Under active development.** The UI and its features are still changing. See [Known Issues](#known-issues--todo).

This is the React single-page app for the Reliable Academic Assistant. Students log in, chat with the AI assistant (with source citations), import their transcript, calculate their GPA, and manage a personal calendar.

For the full project overview, see the [main README](../README.md). For the API, see the [backend README](../backend/README.md).

---

## Stack

- **React 18** + **Vite 6**
- **Tailwind CSS 4** (`@tailwindcss/vite`), with dark and light themes
- **React Router 6**, with protected and public routes
- **Axios**, with JWT interceptors that refresh the token automatically
- **react-markdown** + **remark-gfm** + `github-markdown-css` to render the assistant's answers
- **lucide-react** for icons

## Pages

| Route | Page | Description |
|---|---|---|
| `/login`, `/register` | `LoginPage`, `RegisterPage` | Public pages. Logged-in users are sent to `/chat`. |
| `/chat` | `ChatPage` | The AI chat, with the conversation list, Markdown answers, and clickable **source links** to the original PDFs. It also checks the backend with `/health`. |
| `/gpa` | `GPAPage` | Manage courses, calculate GPA, and upload a transcript PDF to import courses automatically |
| `/calendar` | `CalendarPage` | A monthly calendar for personal events (exams, deadlines…) |
| `/profile` | `ProfilePage` | Edit the name, student ID, department and year |

Pages that need a logged-in user are inside `ProtectedRoute` and `AppLayout`, which adds the sidebar and the mobile menu.

## Directory Structure

```
frontend/
├── index.html
├── vite.config.js             # React + Tailwind plugins
├── vercel.json                # SPA rewrite → index.html
├── testquestions.json         # 100-question RAG benchmark dataset
├── public/                    # favicon, icons
└── src/
    ├── main.jsx               # Entry: BrowserRouter + AuthProvider + routes
    ├── index.css              # Tailwind + theme tokens
    ├── context/AuthContext.jsx    # user state, login / register / logout, useAuth()
    ├── router/ProtectedRoute.jsx  # ProtectedRoute + PublicRoute
    ├── layout/
    │   ├── AppLayout.jsx      # Shell for authenticated pages
    │   └── Sidebar.jsx        # Navigation, theme toggle, user menu
    ├── pages/                 # Chat, GPA, Calendar, Profile, Login, Register
    └── services/api.js        # Axios instance, auth header, 401 → refresh queue
```

## Getting Started

You need **Node.js 20+** and npm.

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

| Script | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with HMR |
| `npm run build` | Build for production into `dist/` |
| `npm run preview` | Serve the production build locally |

### Connecting to the backend

The API base URL is currently **hardcoded** in `src/services/api.js`:

```js
const BASE_URL = 'https://reliable-academic-assistant-v2-live.onrender.com';
```

To use a local backend, change it to `http://localhost:8000`. The backend must also allow `http://localhost:5173` in CORS. Moving this setting to `VITE_API_URL` is on the roadmap.

## Authentication Flow

1. `login` or `register` stores `access_token` and `refresh_token` in `localStorage`.
2. Every request sends `Authorization: Bearer <access_token>`.
3. When a request returns **401**, the interceptor calls `/api/auth/refresh` once. Other requests wait in a queue and are retried with the new token. If the refresh fails, the tokens are cleared and the user is sent to `/login`.
4. On page load, `AuthContext` gets the current user from `/api/user/me`.

## Deployment

The app is deployed on **Vercel**. `vercel.json` sends every path to `index.html`, so client-side routes work when you reload the page.

- Build command: `npm run build`
- Output directory: `dist`

