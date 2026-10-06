---
name: log-processing-standards
description: Activate this skill when processing logs to ensure compliance with logging standards.
---
1. **Filter Relevant Log Levels**: Only process log entries with ERROR or CRITICAL levels.
2. **Standardize Timestamps**: Convert all timestamps to UTC format (YYYY-MM-DDTHH:MM:SSZ).
3. **Extract Key Information**: For each log entry, extract the service name, error level, message, and exception details.
4. **Count Repeated Entries**: Track and count occurrences of repeated log messages, including those indicated by "last message repeated N times."
5. **Service Name Formatting**: Ensure service names are in lower-case with hyphens replaced by underscores.
6. **Sort Errors**: Sort error entries first by service name and then by timestamp in ascending order.
7. **Include Schema Information**: Ensure the output includes schema versioning and generation metadata as specified.