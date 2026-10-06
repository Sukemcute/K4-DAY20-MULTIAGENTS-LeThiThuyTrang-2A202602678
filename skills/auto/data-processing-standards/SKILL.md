---
name: data-processing-standards
description: Activate this skill when processing data to ensure compliance with data handling standards.
---
1. **Standardize Data Formats**: Ensure all date and region formats are consistent (e.g., UTC for timestamps, canonical spelling for regions).
2. **Handle Missing Values**: Implement checks to filter out or handle missing values appropriately in datasets.
3. **Remove Duplicates**: Ensure that duplicate entries are removed based on unique identifiers (e.g., order IDs).
4. **Convert Monetary Values**: Represent monetary values in integer cents, ensuring no decimal points are present in outputs.
5. **Create Metadata**: Include a metadata object in output files that specifies the source and counts of rows processed.
6. **Output Structure Compliance**: Ensure that output files adhere to specified structures, including required headers and data types.
7. **Validate Results**: Implement checks to validate that computed results match expected values before finalizing outputs.