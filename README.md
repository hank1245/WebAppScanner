# Directory Tracer - Web Directory & API Endpoint Scanner

Directory Tracer is a web application designed to scan websites for exposed directories, files, and potential API endpoints. It combines dictionary-based scanning, recursive crawling, and JavaScript analysis to uncover accessible paths.

## Overview

This tool allows users to input one or more target URLs and configure various scanning parameters. It attempts to identify directory listings, common files, and potential API base paths by analyzing linked JavaScript files. Identified API paths are also subjected to dictionary-based scanning. Authentication for sites requiring login can be handled by providing session cookies.

## Key Features

- **Multi-Target Scanning**: Scan multiple websites simultaneously.
- **Dictionary-Based Scanning**: Utilizes a customizable wordlist to search for common directories and files.
  - Default dictionary provided.
  - Users can add or remove dictionary items for a specific scan.
- **Recursive Crawling**: Parses HTML links (`<a>` tags) to discover new paths up to a user-defined depth.
- **Session Cookie Authentication**: Supports scanning sites that require login by allowing users to provide their browser's session cookie string.
- **JavaScript API Endpoint Discovery**:
  - Extracts JavaScript file links from crawled pages.
  - Fetches and parses linked JavaScript files to find potential API endpoint base URLs (using regular expressions).
  - Performs dictionary-based scans on discovered API base paths.
- **Server Information Gathering**: Attempts to identify web server software and underlying frameworks via HTTP headers.
- **Path Exclusions**:
  - Respects `robots.txt` (configurable).
  - Allows users to specify URL paths/patterns to exclude from scans.
- **Proxy Support**:
  - Normal mode (direct connection).
  - Darkweb mode (utilizes a SOCKS5 proxy - pre-configured for Tor-like access if a SOCKS5 proxy is running at `localhost:9050`).
- **Interactive Frontend**:
  - User-friendly interface to configure scan parameters (target URLs, depth, exclusions, dictionary, cookies, mode).
  - Displays scan results in a sortable and filterable table.
  - Shows server information and a scan summary for each target.
- **Downloadable JSON Report**: Generates a comprehensive JSON report including:
  - Scan metadata (targets, duration, settings).
  - Server information.
  - Detailed information for all attempted paths (status code, content length, directory listing status, discovery source, etc.).
  - List of successfully found directories/files.

## Technology Stack

- **Backend**: Python (FastAPI), Requests, BeautifulSoup
- **Frontend**: JavaScript (React), Axios
- **Containerization**: Docker, Docker Compose

## Installation and Execution

The application is designed to be run using Docker and Docker Compose.

1.  **Prerequisites**:

    - Docker installed and running.
    - Docker Compose installed.

2.  **Clone Repository (if applicable)**:

    ```bash
    git clone <repository-url>
    cd directory_scanner
    ```

3.  **Build and Run**:
    Navigate to the project's root directory (where `docker-compose.yml` is located) and run:

    ```bash
    docker-compose up --build -d
    ```

    - The `-d` flag runs containers in detached mode.
    - The `--build` flag forces a rebuild of the images if there are code changes.

4.  **Accessing the Application**:

    - Frontend (React App): `http://localhost:3000`
    - Backend API (FastAPI): `http://localhost:8000/docs` (for API documentation)

5.  **Stopping the Application**:
    ```bash
    docker-compose down
    ```

## How to Use

1.  Open the application in your browser at `http://localhost:3000`.
2.  **Target URL List**: Enter one or more full URLs to scan (e.g., `http://example.com`, `https://test.site/path/`). Each URL should be on a new line.
3.  **Session Cookies (Optional)**:
    - If the target site requires login, first log in to the site using your regular browser.
    - Open your browser's Developer Tools (usually F12).
    - Navigate to the "Application" (Chrome/Edge) or "Storage" (Firefox) tab.
    - Find "Cookies" under the Storage section for the website.
    - Copy the relevant session cookie(s) as a string (e.g., `sessionid=xxxxxx; anothertoken=yyyyyy`).
    - Paste this string into the "Session Cookies" field in the scanner UI. The scanner will use these cookies for all requests to the target site.
4.  **Scan Mode**:
    - `Normal`: Direct connection.
    - `Darkweb`: Uses a SOCKS5 proxy (default: `localhost:9050`). Ensure Tor or a similar proxy is running and accessible at this address if you select this mode.
5.  **Max Depth**: Set the maximum depth for recursive crawling of links.
6.  **Exclusions**: List URL paths or patterns (one per line) to exclude from the scan.
7.  **Respect robots.txt**: Check this option to make the scanner obey `Disallow` rules from `robots.txt`.
8.  **Dictionary Settings**:
    - **Use Default Dictionary**: Uncheck to provide a completely custom list.
    - **Add/Remove Items**: Modify the dictionary for the current scan. Changes are not saved permanently to the default list.
9.  **Start Scan**: Click the "Start Scan" button.
10. **View Results**:
    - Scan progress and results will appear in the table.
    - The table can be filtered by status code and discovery source (e.g., JS API).
    - Server information for each target will be displayed.
11. **Download Report**: Once the scan is complete, click "Download Report" to get a JSON file with detailed results.

## Report Format

The JSON report includes:

- `scan_completed_timestamp`
- `scan_duration_seconds`
- `targets_scanned_count`
- `targets_list`
- `server_information`: An array where each object contains `target` and `info` (Server, X-Powered-By, Framework_Hint).
- `max_depth`
- `respect_robots_txt`
- `session_cookies_provided`: Boolean indicating if session cookies were entered.
- `exclusions_list`
- `checked_paths_count`: Total number of paths attempted.
- `all_attempted_paths_details`: An array of objects with details for each scanned URL:
  - `url`
  - `status_code`
  - `content_length`
  - `directory_listing`: Boolean
  - `note`: Additional information from the scanner.
  - `source`: How the path was discovered (e.g., `initial`, `crawl`, `js_api`).
- `successful_directories_count`
- `successful_directories_list`: A filtered list of successfully found items.
- `dictionary_settings`: Information about the dictionary used.

## Important Notes & Disclaimer

- **Ethical Use**: This tool is intended for educational purposes and for testing systems where you have explicit authorization to scan. Unauthorized scanning of websites is illegal and unethical.
- **Performance**: Scanning large websites with high depth or large dictionaries can be time-consuming and resource-intensive.
- **JavaScript Parsing Limitations**: Finding API endpoints in JavaScript files relies on regular expressions and may not find all endpoints or may produce false positives, especially with obfuscated or complex JavaScript.
- **Session Cookie Security**: Exercise caution when handling session cookies. The application uses them for requests during the scan session but does not store them in the report (only a flag `session_cookies_provided` indicating if they were provided is stored).
