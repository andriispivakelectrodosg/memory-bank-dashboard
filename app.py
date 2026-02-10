"""Memory Bank Dashboard -- Read-Only Flask App"""
import os
import subprocess

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, abort

load_dotenv()

app = Flask(__name__)

_base = os.path.dirname(os.path.abspath(__file__))


def _git_version():
    # 1. Explicit env var (set by Docker / CI)
    env = os.environ.get("APP_VERSION", "").strip()
    if env:
        return env
    # 2. Live git
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_base, stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        pass
    # 3. .version file (baked into Docker image)
    version_file = os.path.join(_base, ".version")
    if os.path.isfile(version_file):
        with open(version_file) as f:
            v = f.read().strip()
            if v:
                return v
    return "unknown"


APP_VERSION = _git_version()


def _dir(env_key, *default_parts):
    return os.path.realpath(
        os.environ.get(env_key, os.path.join(_base, "..", *default_parts))
    )


MEMORY_BANK_DIR = _dir("MEMORY_BANK_DIR", "memory-bank")
LESSONS_DIR = _dir("LESSONS_DIR", "docs", "lessons-learned")
ADRS_DIR = _dir("ADRS_DIR", "docs", "adrs")
FEATURES_DIR = _dir("FEATURES_DIR", "features")

CORE_FILES = [
    {"id": "projectbrief", "filename": "projectbrief.md", "label": "Project Brief"},
    {"id": "productContext", "filename": "productContext.md", "label": "Product Context"},
    {"id": "systemPatterns", "filename": "systemPatterns.md", "label": "System Patterns"},
    {"id": "techContext", "filename": "techContext.md", "label": "Tech Context"},
    {"id": "activeContext", "filename": "activeContext.md", "label": "Active Context"},
    {"id": "progress", "filename": "progress.md", "label": "Progress"},
]


def _safe_read(base_dir, filename):
    """Read a file with path traversal protection."""
    safe_path = os.path.realpath(os.path.join(base_dir, filename))
    if not safe_path.startswith(base_dir + os.sep) and safe_path != base_dir:
        abort(403)
    if not os.path.isfile(safe_path):
        abort(404)
    with open(safe_path, "r", encoding="utf-8") as fh:
        return {"filename": filename, "content": fh.read(), "modified": os.path.getmtime(safe_path)}


def _list_md(directory, exclude=None):
    """List .md files in a directory, excluding specific filenames."""
    exclude = exclude or set()
    if not os.path.isdir(directory):
        return []
    result = []
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".md") and fname not in exclude:
            path = os.path.join(directory, fname)
            result.append(
                {"filename": fname, "label": fname.replace(".md", ""), "modified": os.path.getmtime(path)}
            )
    return result


@app.route("/")
def index():
    return render_template("index.html", version=APP_VERSION)


@app.route("/api/files")
def list_files():
    files = []
    for f in CORE_FILES:
        path = os.path.join(MEMORY_BANK_DIR, f["filename"])
        exists = os.path.isfile(path)
        files.append({**f, "exists": exists, "modified": os.path.getmtime(path) if exists else None})
    return jsonify({"files": files})


@app.route("/api/file/<path:filename>")
def get_file(filename):
    return jsonify(_safe_read(MEMORY_BANK_DIR, filename))


@app.route("/api/tasks")
def list_tasks():
    tasks_dir = os.path.join(MEMORY_BANK_DIR, "tasks")
    items = _list_md(tasks_dir, exclude={"_index.md"})
    for item in items:
        item["filename"] = f"tasks/{item['filename']}"
    return jsonify({"tasks": items})


@app.route("/api/lessons")
def list_lessons():
    has_index = os.path.isfile(os.path.join(LESSONS_DIR, "lesson-learned-index.md"))
    items = _list_md(LESSONS_DIR, exclude={"lesson-learned-index.md"})
    return jsonify({"lessons": items, "has_index": has_index})


@app.route("/api/lesson/<path:filename>")
def get_lesson(filename):
    return jsonify(_safe_read(LESSONS_DIR, filename))


@app.route("/api/adrs")
def list_adrs():
    has_index = os.path.isfile(os.path.join(ADRS_DIR, "README.md"))
    items = _list_md(ADRS_DIR, exclude={"README.md"})
    return jsonify({"adrs": items, "has_index": has_index})


@app.route("/api/adr/<path:filename>")
def get_adr(filename):
    return jsonify(_safe_read(ADRS_DIR, filename))


@app.route("/api/features")
def list_features():
    items = _list_md(FEATURES_DIR)
    return jsonify({"features": items})


@app.route("/api/feature/<path:filename>")
def get_feature(filename):
    return jsonify(_safe_read(FEATURES_DIR, filename))


if __name__ == "__main__":
    print("Memory Bank Dashboard")
    print(f"  Memory Bank: {MEMORY_BANK_DIR}")
    print(f"  Lessons:     {LESSONS_DIR}")
    print(f"  ADRs:        {ADRS_DIR}")
    print(f"  Features:    {FEATURES_DIR}")
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )
