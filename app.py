"""Memory Bank Dashboard -- Read-Only Flask App"""
import os
import re
import subprocess

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, abort, request

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
NOTES_DIR = _dir("NOTES_DIR", "docs", "notes")

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


@app.route("/api/notes")
def list_notes():
    items = _list_md(NOTES_DIR)
    return jsonify({"notes": items})


@app.route("/api/note/<path:filename>")
def get_note(filename):
    return jsonify(_safe_read(NOTES_DIR, filename))


@app.route("/api/notes/recent")
def recent_notes():
    allowed = {1, 3, 5, 10}
    try:
        count = int(request.args.get("count", 5))
    except (ValueError, TypeError):
        count = 5
    if count not in allowed:
        count = 5

    all_items = _list_md(NOTES_DIR)
    total = len(all_items)
    all_items.sort(key=lambda x: x.get("modified", 0), reverse=True)
    items = all_items[:count]

    result = []
    for item in items:
        safe_path = os.path.realpath(os.path.join(NOTES_DIR, item["filename"]))
        if not safe_path.startswith(NOTES_DIR + os.sep) and safe_path != NOTES_DIR:
            continue
        if not os.path.isfile(safe_path):
            continue
        with open(safe_path, "r", encoding="utf-8") as fh:
            content = fh.read()
        result.append({
            "filename": item["filename"],
            "label": item["label"],
            "content": content,
            "modified": item["modified"],
        })

    return jsonify({"notes": result, "total": total})


# --- Dashboard helpers ---

def _read_file(path):
    if not os.path.isfile(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _parse_section(content, heading):
    pattern = r"##\s+" + re.escape(heading) + r"\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else ""


def _parse_list_items(text):
    return [
        line.strip()[2:].strip()
        for line in text.split("\n")
        if line.strip().startswith("- ") and not line.strip().startswith("- _")
    ]


def _count_table_rows(text):
    rows = [l for l in text.split("\n") if l.strip().startswith("|")]
    return max(0, len(rows) - 2)


@app.route("/api/dashboard")
def dashboard_summary():
    result = {}

    # --- Progress ---
    content = _read_file(os.path.join(MEMORY_BANK_DIR, "progress.md"))
    status_section = _parse_section(content, "Current Status")
    works_section = _parse_section(content, "What Works")
    left_section = _parse_section(content, "What's Left")
    milestones_section = _parse_section(content, "Milestones")
    issues_section = _parse_section(content, "Known Issues")

    result["progress"] = {
        "current_status": status_section.split("\n")[0] if status_section else "",
        "what_works": len([l for l in works_section.split("\n") if "✅" in l or "[x]" in l.lower()]),
        "whats_left": len([l for l in left_section.split("\n") if "[ ]" in l]),
        "milestones_done": len(re.findall(r"- \[x\]", milestones_section, re.IGNORECASE)),
        "milestones_total": len(re.findall(r"- \[[x ]\]", milestones_section, re.IGNORECASE)),
        "known_issues": _count_table_rows(issues_section),
    }

    # --- Tasks ---
    content = _read_file(os.path.join(MEMORY_BANK_DIR, "tasks", "_index.md"))
    result["tasks"] = {
        "in_progress": _parse_list_items(_parse_section(content, "In Progress")),
        "pending": _parse_list_items(_parse_section(content, "Pending")),
        "completed": _parse_list_items(_parse_section(content, "Completed")),
        "abandoned": _parse_list_items(_parse_section(content, "Abandoned")),
    }

    # --- Active Context ---
    content = _read_file(os.path.join(MEMORY_BANK_DIR, "activeContext.md"))
    focus = _parse_section(content, "Current Focus")
    steps_section = _parse_section(content, "Next Steps")
    blockers_section = _parse_section(content, "Blockers")

    steps = [
        re.sub(r"^\d+\.\s*", "", l.strip())
        for l in steps_section.split("\n")
        if re.match(r"^\d+\.", l.strip())
    ]

    blockers_raw = _parse_list_items(blockers_section)
    blockers = [b for b in blockers_raw if "none" not in b.lower()]

    result["active_context"] = {
        "current_focus": focus.split("\n")[0] if focus else "",
        "next_steps": steps,
        "blockers": blockers,
    }

    # --- Counts ---
    result["counts"] = {
        "core_files": len([f for f in CORE_FILES if os.path.isfile(os.path.join(MEMORY_BANK_DIR, f["filename"]))]),
        "core_files_total": len(CORE_FILES),
        "tasks": len(_list_md(os.path.join(MEMORY_BANK_DIR, "tasks"), exclude={"_index.md"})),
        "lessons": len(_list_md(LESSONS_DIR, exclude={"lesson-learned-index.md"})),
        "adrs": len(_list_md(ADRS_DIR, exclude={"README.md"})),
        "features": len(_list_md(FEATURES_DIR)),
        "notes": len(_list_md(NOTES_DIR)),
    }

    # --- Recent files ---
    all_files = []
    for f in CORE_FILES:
        p = os.path.join(MEMORY_BANK_DIR, f["filename"])
        if os.path.isfile(p):
            all_files.append({"name": f["label"], "filename": f["filename"],
                              "source": "memory-bank", "modified": os.path.getmtime(p)})
    for tf in _list_md(os.path.join(MEMORY_BANK_DIR, "tasks"), exclude={"_index.md"}):
        all_files.append({"name": tf["label"], "filename": f"tasks/{tf['filename']}",
                          "source": "memory-bank", "modified": tf["modified"]})
    for lf in _list_md(LESSONS_DIR, exclude={"lesson-learned-index.md"}):
        all_files.append({"name": lf["label"], "filename": lf["filename"],
                          "source": "lesson", "modified": lf["modified"]})
    for af in _list_md(ADRS_DIR, exclude={"README.md"}):
        all_files.append({"name": af["label"], "filename": af["filename"],
                          "source": "adr", "modified": af["modified"]})
    for ff in _list_md(FEATURES_DIR):
        all_files.append({"name": ff["label"], "filename": ff["filename"],
                          "source": "feature", "modified": ff["modified"]})
    for nf in _list_md(NOTES_DIR):
        all_files.append({"name": nf["label"], "filename": nf["filename"],
                          "source": "note", "modified": nf["modified"]})
    all_files.sort(key=lambda x: x["modified"] or 0, reverse=True)
    result["recent_files"] = all_files[:8]

    return jsonify(result)


if __name__ == "__main__":
    print("Memory Bank Dashboard")
    print(f"  Memory Bank: {MEMORY_BANK_DIR}")
    print(f"  Lessons:     {LESSONS_DIR}")
    print(f"  ADRs:        {ADRS_DIR}")
    print(f"  Features:    {FEATURES_DIR}")
    print(f"  Notes:       {NOTES_DIR}")
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )
