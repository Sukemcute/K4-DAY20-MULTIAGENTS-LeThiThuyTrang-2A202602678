"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import re
import json
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    """
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    else:
        out_dir = Path(out_dir)

    runs = []
    cond_path = Path(results_dir) / source_condition
    if cond_path.exists():
        for rfile in sorted(cond_path.glob("*/run.json")):
            try:
                r = json.loads(rfile.read_text(encoding="utf-8"))
            except Exception:
                continue
            if r.get("role") != "learn":
                continue

            trace_file = rfile.parent / "trace.md"
            trace_text = trace_file.read_text(encoding="utf-8") if trace_file.exists() else ""
            trace_tail = trace_text[-6000:] if len(trace_text) > 6000 else trace_text

            failed_checks = []
            for c in r.get("checks", []):
                if not c.get("passed"):
                    failed_checks.append((c.get("name", ""), c.get("detail", "")))

            runs.append({
                "task": r.get("task", rfile.parent.name),
                "failed": failed_checks,
                "trace": trace_tail,
            })

    has_failures = any(len(run["failed"]) > 0 for run in runs)
    if not runs or not has_failures:
        print("Cảnh báo: không có check thất bại ở tác vụ học trong", cond_path)
        return []

    prompt_parts = [
        f"You are a meta-learning skill curator writing reusable procedural SKILLs for an autonomous software engineering and data analytics agent.",
        f"Below are the failed checks (check name and automated reviewer feedback rules) and execution traces from learning task runs.",
        f"Your task is to synthesize general best-practice procedural rules (NOT task-specific hardcoded answers or data numbers) into at most {max_skills} concise skills that prevent these failures in new tasks.",
        "",
        "Requirements for each skill:",
        "- High generality: do NOT mention task IDs, test file names, specific sample data numbers, or evaluation markers.",
        "- Frontmatter must include: 'name' (lowercase alphanumeric with hyphens, e.g., code-quality-standards) and 'description' (a clear imperative sentence specifying WHEN to activate/read this skill).",
        "- Body must be concise (at most 50 lines), formatted as an actionable step-by-step checklist.",
        "- Output each skill using the exact block format:",
        "=== SKILL: <name> ===",
        "---",
        "name: <name>",
        "description: <when to use this skill>",
        "---",
        "<actionable procedural checklist>",
        "=== END ===",
        "",
        "### FAILED RUNS AND REVIEWER FEEDBACK:",
    ]

    for run in runs:
        if not run["failed"]:
            continue
        prompt_parts.append(f"\nTask: {run['task']}")
        prompt_parts.append("Failed checks and reviewer feedback:")
        for name, detail in run["failed"]:
            prompt_parts.append(f"- Check: {name} | Feedback: {detail}")
        if run["trace"]:
            prompt_parts.append(f"Trace excerpt:\n{run['trace']}")

    prompt = "\n".join(prompt_parts)
    if model is None:
        model = make_model()

    reply = model.invoke(prompt).content
    blocks = parse_skill_blocks(reply)

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            print(f"Skipping skill {name} due to problems: {problems}")
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(text, encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
