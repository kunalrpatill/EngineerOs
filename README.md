# EngineerOS

An AI-powered Engineering Student Career Platform built as a college semester project.

EngineerOS helps engineering students from the beginning of their journey until they become career-ready, using AI-driven skill analysis and personalized roadmaps.

## Features

- **Student Profile** — Comprehensive profile with skills, interests, and career goals
- **AI Skill-Gap Analysis** — Identifies strengths and areas for improvement
- **Personalized Roadmap** — Step-by-step career plan tailored to your goals
- **Progress Tracking** — Track milestones, courses, and projects
- **Readiness Dashboard** — Visual career readiness score and analytics

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Database | MySQL (via XAMPP) |
| AI | Google Gemini API |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login |

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- XAMPP (with MySQL running)
- Git

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd engineeros
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate    # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Database

1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin (http://localhost/phpmyadmin)
3. Create a new database called `engineeros_db`
4. (Optional) Run `schema.sql` to create tables manually, or let Flask create them automatically

### 5. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your settings. The defaults work with a standard XAMPP installation.

### 6. Run the Application

```bash
python run.py
```

Open http://localhost:5000 in your browser.

## Project Structure

```
engineeros/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask extensions
│   ├── models/              # Database models
│   ├── routes/              # Flask Blueprints
│   ├── services/            # Business logic & AI
│   ├── forms/               # Flask-WTF forms
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
├── requirements.txt
├── schema.sql
├── run.py
└── README.md
```

## License

This project is part of a college semester project.
