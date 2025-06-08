# Directory Tracer - Web Directory & API Endpoint Scanner

Directory Tracer is a web application designed to scan websites for exposed directories, files, and potential API endpoints. It combines dictionary-based scanning, recursive crawling, and JavaScript analysis to uncover accessible paths.

## Key Features

* **Multi-Target Scanning**: Scan multiple websites simultaneously.
* **Dictionary-Based Scanning**: Uses a customizable wordlist to find common directories and files.
* **Recursive Crawling**: Parses HTML links (`<a>` tags) to discover new paths up to a user-defined depth.
* **Session Cookie Authentication**: Supports scanning sites that require a login by using the browser's session cookies.
* **JavaScript API Endpoint Discovery**: Extracts and scans linked JavaScript files to find potential API endpoints.
* **Server Information Gathering**: Identifies web server software and frameworks via HTTP headers.
* **Proxy Support**: Supports both direct connections and a "Darkweb" mode that uses a SOCKS5 proxy (e.g., Tor).
* **Interactive UI**: A user-friendly interface to configure scans and view results in a sortable, filterable table.
* **JSON Report**: Generates a comprehensive JSON report with detailed scan results.

## Technology Stack

* **Backend**: Python (FastAPI), Requests, BeautifulSoup
* **Frontend**: JavaScript (React), Axios
* **Containerization**: Docker, Docker Compose

## Installation and Execution

The application is designed to be run using Docker.

1.  **Prerequisites**: Docker and Docker Compose must be installed and running.
2.  **Build and Run**: Navigate to the project's root directory and run:
    ```bash
    docker-compose up --build -d
    ```
   
3.  **Accessing the Application**:
    * **Frontend**: `http://localhost:3000`
    * **Backend API Docs**: `http://localhost:8000/docs`
4.  **Stopping the Application**:
    ```bash
    docker-compose down
    ```
   

## How to Use

1.  Open the application at `http://localhost:3000`.
2.  **Enter Target URLs**: Input one or more full URLs, each on a new line.
3.  **Configure Options**: Set the scan mode, crawling depth, exclusions, and dictionary settings as needed.
4.  **Session Cookies (Optional)**: For authenticated scans, provide your browser's session cookie string.
5.  **Start Scan**: Click the "Start Scan" button.
6.  **View Results & Download Report**: Monitor results in the table and download the detailed JSON report when complete.

---

***Disclaimer**: This tool is for educational purposes and for testing systems where you have explicit authorization. Unauthorized scanning is illegal and unethical.*
