# CUNY Academic Data Fetcher (MCP Tool)

## 📦 Overview

This tool provides a secure and efficient interface for retrieving academic information from CUNY (City University of New York) systems, including course schedules, degree progress, tuition costs, and institutional data. It is designed to help students and advisors quickly access critical academic planning information via the Model Context Protocol (MCP).

provides detailed reference documentation for every tool available in the three specified MCP servers. Each tool includes parameter schemas, type definitions, required/optional status, defaults, and JSON usage examples.

- **Comprehensive Data Retrieval:** Aggregates financial, academic, and course data in a single efficient call.
- **Course Scheduling:** Retrieves current and upcoming course schedules with times, locations, and instructor details.
- **Degree Progress Tracking:** Provides detailed degree audit information, including completed credits, GPA, and remaining requirements.
- **Financial Cost Estimation:** Calculates estimated tuition and fees for specific semesters.
- **Institutional Information:** Fetches enrollment appointment dates and open enrollment periods for all terms.

# MCP Tools Reference

Complete documentation for all tools across the following MCP servers:
- `mcp/fetch-cuny-information`
- `mcp/system`
- `mcp/fetch-rendered-html`


## 🚀 Installation

Configure your MCP client to connect to the server hosting these tools. Add the server URLs or executable paths to your MCP configuration file:
```json
{
  "mcpServers": {
    "fetch-cuny-information": {
      "command": "your-cuny-server-executable",
      "args": []
    },
    "system": {
      "command": "your-system-server-executable",
      "args": []
    },
    "fetch-rendered-html": {
      "command": "your-web-fetch-server-executable",
      "args": []
    }
  }
}
```

To use this MCP tool, ensure you have the following dependencies installed:
- Python 3.8+
- `requests` library
- `beautifulsoup4` library (for HTML parsing if needed)

```bash
pip install -r requirements.txt
```

---

## 🎓 `mcp/fetch-cuny-information` Server Tools

### `fetch_my_cuny_information`
Fetches a comprehensive overview of your CUNY academic profile (tuition, degrees, courses, financials) in a single optimized call.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `headless` | `boolean` | No | `true` | Runs the underlying browser in headless mode. |

**Example Usage:**
```json
{
  "name": "fetch_my_cuny_information",
  "arguments": {
    "headless": true
  }
}
```

### `fetch_my_cuny_courses`
Retrieves CUNY course schedules and details listed on your profile.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `timeout` | `integer` | No | `30000` | Timeout in milliseconds. |

**Example Usage:**
```json
{
  "name": "fetch_my_cuny_courses",
  "arguments": {
    "timeout": 30000
  }
}
```

### `fetch_my_cuny_degree_progress`
Retrieves CUNY degree progress, including transcripts, grades, and academic information.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `timeout` | `integer` | No | `30000` | Timeout in milliseconds. |

**Example Usage:**
```json
{
  "name": "fetch_my_cuny_degree_progress",
  "arguments": {
    "timeout": 30000
  }
}
```

### `fetch_my_cuny_financial_cost`
Retrieves the cost of CUNY courses per semester, including tuition and outstanding balances.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `timeout` | `integer` | No | `30000` | Timeout in milliseconds. |

**Example Usage:**
```json
{
  "name": "fetch_my_cuny_financial_cost",
  "arguments": {
    "timeout": 30000
  }
}
```

### `fetch_my_cuny_student_id`
Fetches your CUNY student ID and associated card information.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type_of_card` | `enum` | No | `"getEmplidCard"` | Card type: `"getEmplidCard"`, `"getLibraryIdCard"`, or `"both"`. |

**Example Usage:**
```json
{
  "name": "fetch_my_cuny_student_id",
  "arguments": {
    "type_of_card": "both"
  }
}
```

### `search_courses_on_cuny`
Searches for courses on CUNY campuses.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `string` | **Yes** | - | Search query string. |
| `college` | `string` (const) | No | `"leh01"` | College code (currently fixed to Lehman College). |

**Example Usage:**
```json
{
  "name": "search_courses_on_cuny",
  "arguments": {
    "query": "Introduction to Computer Science",
    "college": "leh01"
  }
}
```

### `resolve_section_code`
Resolves the section code based on the provided year and semester.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `year` | `integer` | **Yes** | - | Academic year. |
| `semester` | `enum` | No | `"spring"` | Semester: `"spring"`, `"summer"`, or `"fall"`. |

**Example Usage:**
```json
{
  "name": "resolve_section_code",
  "arguments": {
    "year": 2024,
    "semester": "fall"
  }
}
```

---

## ⚙️ `mcp/system` Server Tools

### `open_file`
Opens a file from the active user's directory or MCP root.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | **Yes** | - | Relative or absolute file path. |

**Example Usage:**
```json
{
  "name": "open_file",
  "arguments": {
    "path": "documents/report.txt"
  }
}
```

### `read_file`
Reads the full UTF-8 content of a file.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | **Yes** | - | Path to the file relative to the server root. |

**Example Usage:**
```json
{
  "name": "read_file",
  "arguments": {
    "path": "config/settings.json"
  }
}
```

### `write_file`
Writes or overwrites a file, creating parent directories automatically.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | **Yes** | - | Destination path relative to the server root. |
| `content` | `string` | **Yes** | - | UTF-8 text content to write. |
| `overwrite` | `boolean` | No | `true` | Whether to overwrite existing files. |

**Example Usage:**
```json
{
  "name": "write_file",
  "arguments": {
    "path": "output/result.md",
    "content": "# New Document\n\nGenerated content here.",
    "overwrite": true
  }
}
```

### `list_directory`
Lists contents of a directory.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | No | `"."` | Directory path relative to the server root. |

**Example Usage:**
```json
{
  "name": "list_directory",
  "arguments": {
    "path": "./src"
  }
}
```

### `delete_file`
Permanently deletes a single file.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | **Yes** | - | Path to the file to delete. |

**Example Usage:**
```json
{
  "name": "delete_file",
  "arguments": {
    "path": "temp/old_data.csv"
  }
}
```

### `delete_directory`
Recursively deletes a directory and its contents.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | **Yes** | - | Path to the directory to delete. |
| `confirm` | `boolean` | No | `false` | Must be `true` to proceed. |

**Example Usage:**
```json
{
  "name": "delete_directory",
  "arguments": {
    "path": "cache/temp_files",
    "confirm": true
  }
}
```

### `move`
Moves or renames a file or directory.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | `string` | **Yes** | - | Source path relative to the server root. |
| `destination` | `string` | **Yes** | - | Destination path relative to the server root. |

**Example Usage:**
```json
{
  "name": "move",
  "arguments": {
    "source": "docs/old.md",
    "destination": "archive/old.md"
  }
}
```

### `file_info`
Returns metadata about a file or directory.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `string` | **Yes** | - | Path relative to the server root. |

**Example Usage:**
```json
{
  "name": "file_info",
  "arguments": {
    "path": "data/sample.txt"
  }
}
```

---

## 🌐 `mcp/fetch-rendered-html` Server Tools

### `fetch_rendered_html`
Fetches the fully rendered HTML content of a webpage, executing client-side JavaScript before returning.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | `string` | **Yes** | - | The URL of the webpage to fetch. |
| `timeout` | `integer` | No | `30000` | Timeout in milliseconds for the request. |
| `wait_for_selector` | `string \| null` | No | `null` | CSS selector to wait for before returning HTML. |

**Example Usage:**
```json
{
  "name": "fetch_rendered_html",
  "arguments": {
    "url": "https://example.com",
    "timeout": 30000,
    "wait_for_selector": "#main-content"
  }
}
```

---

## 🔍 Dynamic Tool Discovery

MCP servers support runtime introspection. Use the following methods to discover all available tools, their schemas, and capabilities without hardcoding:

```json
// List all available tools
{
  "method": "tools/list"
}

// Get detailed schema for a specific tool
{
  "method": "tools/get_schema",
  "params": {
    "tool_name": "fetch_rendered_html"
  }
}
```


## API Endpoints

This tool interacts with CUNY's internal systems (e.g., CUNYFirst). Ensure you have proper authentication credentials configured in your environment.

## Security & Privacy

- **Data Sensitivity:** The data retrieved includes PII and financial information. Handle this data with care.
- **Authentication:** Ensure that your API keys or session tokens are stored securely and not exposed in code.
- **Rate Limiting:** Be mindful of CUNY's rate limits to avoid being blocked.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any bugs or feature requests.

## Disclaimer

This tool is for educational and personal planning purposes only. It is not affiliated with or endorsed by CUNY. Always verify information with official CUNY sources.
