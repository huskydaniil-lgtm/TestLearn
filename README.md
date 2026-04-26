# TestLearn — Educational Platform for Software Testing Fundamentals

An educational website for learning the basics of software testing.
Course project for the discipline "Databases" at MFUA.

## Technologies

- **Backend:** FastAPI (Python)
- **Database:** SQLite (relational)
- **Templates:** Jinja2
- **Frontend:** HTML + Tailwind CSS (CDN) + Vanilla JS
- **Styling:** Tailwind CSS with custom color scheme (emerald/green)

## Project Structure

```
fastapi-app/
├── main.py              # Main FastAPI application
├── templates/           # Jinja2 templates
│   ├── base.html        # Base template (navigation, footer, blocks)
│   ├── index.html       # Home page
│   ├── theory.html      # Theoretical material
│   ├── topic.html       # Individual topic page
│   ├── quiz_list.html   # Quiz list
│   ├── quiz.html        # Taking a quiz
│   ├── quiz_result.html # Quiz results
│   ├── glossary.html    # Glossary of terms
│   ├── stats.html       # Statistics
│   ├── database.html    # Database structure (with ER diagram)
│   └── feedback.html    # Feedback form
├── static/              # Static files
├── testlearn.db         # SQLite database (created automatically)
├── requirements.txt     # Python dependencies
└── README.md            # Documentation
```

## Database

DBMS: SQLite with 8 tables:

| Table | Description |
|-------|-------------|
| `categories` | Categories (types of testing) |
| `topics` | Theoretical topics and lessons |
| `quizzes` | Quizzes for knowledge assessment |
| `questions` | Quiz questions (with answer options) |
| `quiz_results` | Quiz attempt results |
| `glossary` | Glossary of testing terms |
| `feedback` | Feedback messages |
| `user_progress` | User progress |

## Installation and Launch

### 1. Clone the repository

```bash
cd fastapi-app
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Open in browser

```
http://localhost:8000
```

## Functionality

- 📚 **Theory** — 16 topics across 5 testing categories, search by topics
- 📝 **Tests** — 6 tests (50 questions) with timer, randomization, and answer explanations
- 📖 **Glossary** — 43 terms with search and letter filtering
- 📊 **Statistics** — test attempt analytics, CSV export, progress reset
- 🗄️ **Database** — database structure with ER diagram (Mermaid.js)
- 💬 **Feedback** — form for sending messages, list of recent feedback
- 📱 **Responsive design** — correct display on mobile devices
- 🔍 **Search** — search in theory and glossary

## API Endpoints

- `GET /api/stats` — platform statistics (JSON)
- `GET /api/categories` — list of categories (JSON)
- `GET /api/quiz/{id}/questions` — quiz questions without answers (JSON)
- `GET /api/feedback` — list of feedback (JSON)

## Author

**Saidov D.A.**
Moscow Oblast Branch of MFUA
Direction: 09.03.03 Applied Informatics