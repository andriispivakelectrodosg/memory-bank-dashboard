"""Memory Bank Dashboard -- Read-Only Flask App"""
import os
from flask import Flask, jsonify, render_template, abort

app = Flask(__name__)

MEMORY_BANK_DIR = os.path.realpath(
    os.environ.get(
        "MEMORY_BANK_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "memory-bank"),
    )
)

LESSONS_DIR = os.path.realpath(
    os.environ.get(
        "LESSONS_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "lessons-learned"),
    )
)

CORE_FILES = [
    {"id": "projectbrief", "filename": "projectbrief.md", "label": "Project Brief"},
    {"id": "productContext", "filename": "productContext.md", "label": "Product Context"},
    {"id": "systemPatterns", "filename": "systemPatterns.md", "label": "System Patterns"},
    {"id": "techContext", "filename": "techContext.md", "label": "Tech Context"},
    {"id": "activeContext", "filename": "activeContext.md", "label": "Active Context"},
    {"id": "progress", "filename": "progress.md", "label": "Progress"},
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/files")
def list_files():
    files = []
    for f in CORE_FILES:
        path = os.path.join(MEMORY_BANK_DIR, f["filename"])
        exists = os.path.isfile(path)
        files.append(
            {
                **f,
                "exists": exists,
                "modified": os.path.getmtime(path) if exists else None,
            }
        )
    return jsonify({"files": files})


@app.route("/api/file/<path:filename>")
def get_file(filename):
    safe_path = os.path.realpath(os.path.join(MEMORY_BANK_DIR, filename))
    if not safe_path.startswith(MEMORY_BANK_DIR + os.sep) and safe_path != MEMORY_BANK_DIR:
        abort(403)
    if not os.path.isfile(safe_path):
        abort(404)
    with open(safe_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    return jsonify(
        {
            "filename": filename,
            "content": content,
            "modified": os.path.getmtime(safe_path),
        }
    )


@app.route("/api/tasks")
def list_tasks():
    tasks_dir = os.path.join(MEMORY_BANK_DIR, "tasks")
    if not os.path.isdir(tasks_dir):
        return jsonify({"tasks": []})
    task_files = []
    for fname in sorted(os.listdir(tasks_dir)):
        if fname.endswith(".md") and fname != "_index.md":
            path = os.path.join(tasks_dir, fname)
            task_files.append(
                {
                    "filename": f"tasks/{fname}",
                    "label": fname.replace(".md", ""),
                    "modified": os.path.getmtime(path),
                }
            )
    return jsonify({"tasks": task_files})


@app.route("/api/lessons")
def list_lessons():
    if not os.path.isdir(LESSONS_DIR):
        return jsonify({"lessons": [], "has_index": False})
    lesson_files = []
    has_index = False
    for fname in sorted(os.listdir(LESSONS_DIR)):
        if fname == "lesson-learned-index.md":
            has_index = True
            continue
        if fname.endswith(".md"):
            path = os.path.join(LESSONS_DIR, fname)
            lesson_files.append(
                {
                    "filename": fname,
                    "label": fname.replace(".md", ""),
                    "modified": os.path.getmtime(path),
                }
            )
    return jsonify({"lessons": lesson_files, "has_index": has_index})


@app.route("/api/lesson/<path:filename>")
def get_lesson(filename):
    safe_path = os.path.realpath(os.path.join(LESSONS_DIR, filename))
    if not safe_path.startswith(LESSONS_DIR + os.sep) and safe_path != LESSONS_DIR:
        abort(403)
    if not os.path.isfile(safe_path):
        abort(404)
    with open(safe_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    return jsonify(
        {
            "filename": filename,
            "content": content,
            "modified": os.path.getmtime(safe_path),
        }
    )


if __name__ == "__main__":
    print(f"Memory Bank Dashboard")
    print(f"Reading from: {MEMORY_BANK_DIR}")
    print(f"Lessons from: {LESSONS_DIR}")
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )
