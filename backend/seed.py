"""Sample data. Run with:  flask --app app seed"""
from models import Course, Lesson, User, db

COURSES = [
    ("Python Programming Basics", "Programming", "Beginner", "Asha Verma", 8,
     "python, programming, variables, functions, loops",
     "Learn Python from scratch: variables, control flow, functions, lists, dictionaries and file handling.",
     ["Setting up Python", "Variables and data types", "Loops and conditions", "Functions and modules"]),
    ("Data Analysis with Pandas", "Data Science", "Intermediate", "Rohan Mehta", 10,
     "pandas, python, dataframes, data cleaning, analysis",
     "Load, clean, reshape and summarise real datasets using pandas DataFrames and groupby operations.",
     ["Series and DataFrames", "Cleaning messy data", "Grouping and aggregation", "Merging datasets"]),
    ("Machine Learning with scikit-learn", "Data Science", "Intermediate", "Neha Kulkarni", 12,
     "machine learning, scikit-learn, python, classification, regression",
     "Build classification and regression models in Python, evaluate them, and avoid overfitting with scikit-learn.",
     ["What is machine learning", "Training and test sets", "Classification models", "Evaluating models"]),
    ("Flask Web Development", "Web Development", "Intermediate", "Arjun Rao", 9,
     "flask, python, web, jinja2, routing, mysql",
     "Build database-backed web applications with Flask, Jinja2 templates, forms, sessions and MySQL.",
     ["Your first Flask app", "Routing and Jinja2 templates", "Forms and validation", "Connecting to MySQL"]),
    ("HTML and CSS Foundations", "Web Development", "Beginner", "Priya Nair", 6,
     "html, css, web, layout, flexbox",
     "Structure pages with semantic HTML and style them with modern CSS, including flexbox and grid layouts.",
     ["Semantic HTML", "Selectors and the cascade", "Flexbox layouts", "Responsive design basics"]),
    ("Bootstrap 5 Responsive Design", "Web Development", "Beginner", "Priya Nair", 5,
     "bootstrap, css, html, responsive, components",
     "Create responsive, mobile-first interfaces quickly with the Bootstrap 5 grid, utilities and components.",
     ["The grid system", "Navbars and cards", "Forms and buttons", "Customising Bootstrap"]),
    ("SQL and MySQL Essentials", "Databases", "Beginner", "Karan Shah", 7,
     "sql, mysql, database, queries, joins",
     "Query relational data with SQL: SELECT, filtering, joins, aggregation and managing tables in MySQL.",
     ["Tables and keys", "SELECT and WHERE", "Joins", "Aggregation and grouping"]),
    ("Database Design and Normalization", "Databases", "Intermediate", "Karan Shah", 6,
     "database design, normalization, erd, mysql, schema",
     "Design clean relational schemas with entity-relationship diagrams, keys, constraints and normalization.",
     ["Entities and relationships", "Primary and foreign keys", "Normal forms", "Indexes and performance"]),
    ("NumPy for Numerical Computing", "Data Science", "Beginner", "Rohan Mehta", 5,
     "numpy, arrays, python, numerical, linear algebra",
     "Work with fast n-dimensional arrays, broadcasting and vectorised maths using NumPy.",
     ["Creating arrays", "Indexing and slicing", "Broadcasting", "Linear algebra basics"]),
    ("Statistics for Data Science", "Mathematics", "Beginner", "Meera Iyer", 8,
     "statistics, probability, data science, distributions, hypothesis testing",
     "Understand probability, distributions, sampling and hypothesis testing for data-driven decisions.",
     ["Descriptive statistics", "Probability basics", "Distributions", "Hypothesis testing"]),
    ("JavaScript Fundamentals", "Programming", "Beginner", "Arjun Rao", 8,
     "javascript, programming, dom, web, functions",
     "Learn core JavaScript and use it to make web pages interactive through the DOM.",
     ["Syntax and types", "Functions and scope", "The DOM", "Events and forms"]),
    ("Deep Learning Concepts", "AI", "Advanced", "Neha Kulkarni", 14,
     "deep learning, neural networks, machine learning, ai, python",
     "Understand neural networks, backpropagation, convolutional and recurrent architectures.",
     ["Neurons and layers", "Backpropagation", "Convolutional networks", "Training tips"]),
]


def run():
    if Course.query.first():
        print("Courses already exist, skipping seed.")
        return

    for title, category, level, instructor, hours, tags, desc, lessons in COURSES:
        course = Course(title=title, category=category, level=level, instructor=instructor,
                        duration_hours=hours, tags=tags, description=desc)
        for pos, lesson_title in enumerate(lessons, start=1):
            course.lessons.append(Lesson(
                title=lesson_title, position=pos, duration_minutes=12 + pos * 3,
                content=(f"In this lesson you will learn: {lesson_title.lower()}.\n\n"
                         f"Work through the examples for {title}, then try the practice "
                         "task on your own before marking the lesson complete.")))
        db.session.add(course)

    if not User.query.filter_by(email="demo@example.com").first():
        demo = User(name="Demo Learner", email="demo@example.com")
        demo.set_password("demo12345")
        db.session.add(demo)

    db.session.commit()
    print("Seeded 12 courses and a demo user (demo@example.com / demo12345).")
