# CUNY Academic Data Fetcher (MCP Tool)

## Overview

This tool provides a secure and efficient interface for retrieving academic information from CUNY (City University of New York) systems, including course schedules, degree progress, tuition costs, and institutional data. It is designed to help students and advisors quickly access critical academic planning information via the Model Context Protocol (MCP).

## Features

- **Comprehensive Data Retrieval:** Aggregates financial, academic, and course data in a single efficient call.
- **Course Scheduling:** Retrieves current and upcoming course schedules with times, locations, and instructor details.
- **Degree Progress Tracking:** Provides detailed degree audit information, including completed credits, GPA, and remaining requirements.
- **Financial Cost Estimation:** Calculates estimated tuition and fees for specific semesters.
- **Institutional Information:** Fetches enrollment appointment dates and open enrollment periods for all terms.

## Installation

To use this MCP tool, ensure you have the following dependencies installed:
- Python 3.8+
- `requests` library
- `beautifulsoup4` library (for HTML parsing if needed)

```bash
pip install -r requirements.txt
```

## Usage

### 1. Fetch All CUNY Information (Recommended)

Use the `fetch_cuny_information` function for a quick overview of all academic data.

```python
from cuny_mcp import fetch_cuny_information

# Fetch all data in one call
data = fetch_cuny_information(headless=True)
print(data)
```

### 2. Fetch Course Schedules

Use `fetch_cuny_courses` to get detailed course information.

```python
from cuny_mcp import fetch_cuny_courses

courses = fetch_cuny_courses()
print(courses)
```

### 3. Fetch Degree Progress

Use `fetch_cuny_degree_progress` for detailed degree audit info.

```python
from cuny_mcp import fetch_cuny_degree_progress

degree_info = fetch_cuny_degree_progress()
print(degree_info)
```

### 4. Fetch Financial Costs

Use `fetch_cuny_financial_cost` to get tuition and fee estimates.

```python
from cuny_mcp import fetch_cuny_financial_cost

costs = fetch_cuny_financial_cost()
print(costs)
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
