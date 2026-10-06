"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Delegate to explorer when you need to inspect or understand the workspace, "
                "read documentation, docstrings, data schemas, logs, or error outputs without making any changes. "
                "Provide all relevant file paths and questions in the delegation prompt."
            ),
            "system_prompt": (
                "You are an exploratory assistant. Your responsibility is to thoroughly read and analyze "
                "files, docstrings, logs, data formats, and codebases. Report your factual findings, structure, "
                "and anomalies clearly. Do not modify, create, or delete any files."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Delegate to implementer when you need to write or edit code, perform data cleaning/transformation, "
                "create required output files, or execute tests and scripts to fix errors. "
                "Include all task rules, file paths, and exact specifications in the delegation prompt."
            ),
            "system_prompt": (
                "You are an implementation assistant. Your responsibility is to write, modify, and fix code "
                "and data artifacts according to strict task specifications. Run tests or Python scripts to verify "
                "your work, and return a summary of the changes made and test results."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Delegate to reviewer when you need an independent verification of completed work, "
                "checking test results, edge cases, output file schemas, and rule compliance before submitting. "
                "Include the rules and paths of generated files in the delegation prompt."
            ),
            "system_prompt": (
                "You are a code and data reviewer. Your responsibility is to verify that all task requirements, "
                "tests, edge cases, and formatting conventions are strictly satisfied. Do not make changes yourself; "
                "report any discrepancies, unhandled edge cases, or errors found."
            ),
        },
    ]
