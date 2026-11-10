# Lumen Learn - Online Learning Platform

Flask + MySQL learning platform with a scikit-learn course recommender.
Frontend and backend live in separate folders.

```
online-learning-platform/
  backend/                 Python, Flask, MySQL, ML
    app.py                 routes, auth, CLI commands
    models.py              SQLAlchemy models
    recommender.py         TF-IDF + cosine-similarity recommender (scikit-learn, pandas, numpy)
    seed.py                sample courses + demo user
    config.py, schema.sql, requirements.txt, .env.example
  frontend/                Jinja2 templates + static assets
    templates/             base, index, courses, course_detail, lesson, dashboard, login, register
    static/css/style.css   custom styles on top of Bootstrap 5
    static/js/main.js
```

## Setup

1. Create the MySQL database:
   ```sql
   CREATE DATABASE online_learning CHARACTER SET utf8mb4;
   ```
2. Install and configure:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env            # then edit DB_USER / DB_PASSWORD
   ```
3. Create tables, add sample data, run:
   ```bash
   flask --app app init-db
   flask --app app seed
   flask --app app run --debug
   ```
   Open http://127.0.0.1:5000. Demo login: `demo@example.com` / `demo12345`.

(`backend/schema.sql` can create the tables by hand if you prefer.)

## How recommendations work

`recommender.py` turns each course's title, category, tags and description into TF-IDF vectors
and compares them with cosine similarity.
- Course page: "Learners also take" shows the most similar courses.
- Dashboard / home: averages the similarity of everything you are enrolled in and suggests the
  best matches you have not taken yet.
- JSON endpoint: `GET /api/recommendations` (login required).
