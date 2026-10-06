"""GUIDE Phần 1 - Chạy một tác vụ (task) và ghi kết quả.   >>> SINH VIÊN CÀI ĐẶT run_task <<<

Pseudo-code: guides/pseudocode/03_runner.md
Kiểm tra:    pytest tests/test_03_runner.py
Chạy thật:   python -m lab.runner --condition baseline --tasks learn
"""
import argparse
import json
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import AIMessage, ToolMessage

from .agent import build_agent
from .grading import grade                                                      # có sẵn
from .tasks import ROOT, get_task, hash_dir, list_tasks, prepare_sandbox         # có sẵn

# Ba điều kiện thí nghiệm (condition). `skills_dir` là thư mục skill nguồn (tính từ thư mục gốc của lab).
CONDITIONS = {
    "baseline": {"mode": "single", "skills_dir": None},
    "subagents": {"mode": "subagents", "skills_dir": None},
    "skills-auto": {"mode": "single", "skills_dir": "skills/auto"},
}


def render_trace(messages) -> str:
    """CÓ SẴN, KHÔNG SỬA. Chuyển danh sách message của luồng chính thành Markdown (vết - trace).

    Lưu ý: chỉ gồm luồng chính. Việc subagent làm bên trong KHÔNG hiện trong vết;
    chỉ thấy lệnh gọi `task` và báo cáo cuối của subagent.
    """
    home = str(Path.home())

    def clean(text) -> str:
        return str(text).replace(home, "~")[:1500]

    parts = []
    for m in messages:
        if isinstance(m, AIMessage):
            if m.content:
                parts.append(f"### Assistant\n{clean(m.content)}")
            for tc in m.tool_calls:
                parts.append(f"### Tool call: {tc['name']}\n{clean(json.dumps(tc['args'], ensure_ascii=False))}")
        elif isinstance(m, ToolMessage):
            parts.append(f"### Tool result\n{clean(m.content)}")
        else:
            parts.append(f"### {m.type.capitalize()}\n{clean(m.content)}")
    return "\n\n".join(parts)


def run_task(task_id: str, condition: str, results_dir="results", model=None, recursion_limit: int = 60) -> dict:
    """Chạy MỘT tác vụ dưới MỘT điều kiện, chấm điểm, ghi kết quả, và trả về bản ghi (record).

    Ghi vào: <results_dir>/<condition>/<task_id>/run.json và trace.md  (trace.md = render_trace(messages)).
    """
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")

    cfg = CONDITIONS[condition]
    task = get_task(task_id)
    skills_dir = ROOT / cfg["skills_dir"] if cfg.get("skills_dir") else None
    out = Path(results_dir) / condition / task_id
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "task": task_id,
        "condition": condition,
        "role": task.role,
        "error": None,
        "timestamp": timestamp,
    }

    sandbox_raw = tempfile.mkdtemp(prefix=f"lab_{condition}_{task_id}_")
    sandbox = Path(sandbox_raw)

    messages = []
    final_message = ""
    try:
        prepare_sandbox(task, sandbox, skills_dir)
        hash_before = hash_dir(sandbox / "skills")
        record["skills_sha256"] = hash_before

        agent = build_agent(sandbox, mode=cfg["mode"], use_skills=(skills_dir is not None), model=model)
        usage = UsageMetadataCallbackHandler()
        t0 = time.time()

        try:
            for chunk in agent.stream(
                {"messages": [{"role": "user", "content": task.instruction}]},
                config={"callbacks": [usage], "recursion_limit": recursion_limit},
                stream_mode="values",
            ):
                if "messages" in chunk:
                    messages = chunk["messages"]
            final_message = str(messages[-1].content) if messages and hasattr(messages[-1], "content") else ""
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            if messages:
                final_message = str(messages[-1].content) if hasattr(messages[-1], "content") else ""

        duration = round(time.time() - t0, 1)
        record["seconds"] = duration

        total_input = sum(u.get("input_tokens", 0) for u in usage.usage_metadata.values())
        total_output = sum(u.get("output_tokens", 0) for u in usage.usage_metadata.values())
        total_tokens = sum(u.get("total_tokens", 0) for u in usage.usage_metadata.values())
        record["tokens"] = {"input": total_input, "output": total_output, "total": total_tokens}

        tool_calls_list = []
        for m in messages:
            if isinstance(m, AIMessage) and hasattr(m, "tool_calls"):
                tool_calls_list.extend(m.tool_calls)

        record["tool_calls"] = len(tool_calls_list)
        record["subagent_calls"] = sum(1 for tc in tool_calls_list if tc.get("name") == "task")

        skills_read_set = set()
        for tc in tool_calls_list:
            if tc.get("name") == "read_file":
                fp = str(tc.get("args", {}).get("file_path", "")).replace("\\", "/")
                if "skills/" in fp:
                    after = fp.split("skills/", 1)[1]
                    parts = [p for p in after.split("/") if p]
                    if parts:
                        skills_read_set.add(parts[0])

        record["skills_read"] = len(skills_read_set)
        hash_after = hash_dir(sandbox / "skills")
        record["skills_modified"] = (hash_after != hash_before)
        record["final_message"] = final_message

        g = grade(task, sandbox / "workspace")
        record["score"] = g.get("score", 0.0)
        record["passed"] = g.get("passed", 0)
        record["total"] = g.get("total", 0)
        record["checks"] = g.get("checks", [])

        (out / "trace.md").write_text(render_trace(messages), encoding="utf-8")
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)

    (out / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def main(argv=None):
    """CÓ SẴN, KHÔNG SỬA. Giao diện dòng lệnh (CLI): --condition, --tasks (id... | all | learn | eval), --results, --recursion-limit.

    In mỗi lần chạy một dòng: điều kiện, id, passed/total, token, số tool call, số giây, lỗi (nếu có).
    """
    ap = argparse.ArgumentParser(description="Run tasks under one condition.")
    ap.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    ap.add_argument("--tasks", nargs="+", default=["all"], help="task ids, or 'all', 'learn', 'eval'")
    ap.add_argument("--results", default="results")
    ap.add_argument("--recursion-limit", type=int, default=60)
    args = ap.parse_args(argv)
    if args.tasks == ["all"]:
        ids = [t.id for t in list_tasks()]
    elif args.tasks in (["learn"], ["eval"]):
        ids = [t.id for t in list_tasks(args.tasks[0])]
    else:
        ids = args.tasks
    for tid in ids:
        try:
            r = run_task(tid, args.condition, args.results, recursion_limit=args.recursion_limit)
        except Exception as exc:  # noqa: BLE001
            print(f"{args.condition:13s} {tid:11s} CRASH {type(exc).__name__}: {exc}", flush=True)
            continue
        print(f"{args.condition:13s} {tid:11s} score={r['passed']}/{r['total']} tokens={r['tokens']['total']} "
              f"calls={r['tool_calls']} {r['seconds']}s" + (f" ERROR={r['error']}" if r["error"] else ""), flush=True)


if __name__ == "__main__":
    main()
