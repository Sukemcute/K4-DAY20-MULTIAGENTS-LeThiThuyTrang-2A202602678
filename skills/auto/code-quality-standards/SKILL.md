---
name: code-quality-standards
description: Activate this skill when modifying code to ensure compliance with quality standards.
---
1. **Do Not Modify Test Files**: Ensure that original test files remain unchanged. Create new test files if necessary.
2. **Implement Type Annotations**: Add type annotations for all public functions, including parameters and return values.
3. **Document Changes**: Record all changes in the CHANGELOG.md under '## Unreleased' with a bullet point for each fix.
4. **Add Regression Tests**: Create a dedicated regression test file with at least three tests for each bug fixed.
5. **Follow CSV Formatting Rules**: Ensure that CSV outputs adhere to specified formats, including quoting and header requirements.
6. **Handle Price Parsing**: Ensure that price parsing functions correctly handle various formats, including edge cases like parentheses.
7. **Maintain Code Consistency**: Ensure that all code changes maintain the intended functionality as described in the docstrings.