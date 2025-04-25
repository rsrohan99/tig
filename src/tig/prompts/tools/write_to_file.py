from textwrap import dedent

WRITE_TO_FILE_PROMPT = dedent("""
## write_to_file
Description: Request to write full content to a file at the specified path. If the file exists, it will be overwritten with the provided content. If the file doesn't exist, it will be created. This tool will automatically create any directories needed to write the file.
Parameters:
- path: (required) The path of the file to write to (relative to the current workspace directory {pwd})
- content: (required) The content to write to the file. ALWAYS provide the COMPLETE intended content of the file, without any truncation or omissions. You MUST include ALL parts of the file, even if they haven't been modified. Do NOT include the line numbers in the content though, just the actual content of the file.
You don't have to create parent directories, they will be created automatically if they don't exist.
Usage:
<write_to_file>
<path>File path here</path>
<content>
Your file content here
</content>
</write_to_file>

Example: Requesting to write to frontend-config.json
<write_to_file>
<path>frontend-config.json</path>
<content>
{{
  "apiEndpoint": "https://api.example.com",
  "theme": {{
    "primaryColor": "#007bff",
    "secondaryColor": "#6c757d",
    "fontFamily": "Arial, sans-serif"
  }},
  "features": {{
    "darkMode": true,
    "notifications": true,
    "analytics": false
  }},
  "version": "1.0.0"
}}
</content>
</write_to_file>
""")
