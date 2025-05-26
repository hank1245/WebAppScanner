# DirectoryTracer

**DirectoryTracer** is a web application that discovers hidden directories on websites. This tool is useful for identifying potential security vulnerabilities or exploring publicly accessible paths on both surface web and dark web domains.

---

## Features

- **Multi-target Scanning**: Scan multiple URLs simultaneously.
- **Dictionary-based Directory Discovery**: Use built-in wordlists to find common directory paths.
- **Custom Wordlist Support**: Add or remove your own path entries from the dictionary.
- **Dark Web Support**: Scan `.onion` domains through a TOR proxy.
- **Recursive Crawling**: Follow internal links to a specified depth.
- **robots.txt Compliance**: Optionally respect crawling restrictions defined in `robots.txt`.
- **Exclusion List**: Skip scanning specific URLs or domains.
- **Directory Listing Detection**: Identify paths with directory listing enabled.
- **Result Filtering & Sorting**: Filter and sort by status code, content length, and more.
- **Detailed Report Export**: Export scan results as a JSON file.

---

## How It Works

DirectoryTracer performs scanning using the following workflow:

1. **Scan Configuration**: The user specifies target URLs, scan mode, depth, and other options.
2. **Dictionary Probing**: URLs are appended with predefined or custom dictionary entries and sent as HTTP requests.
3. **Response Analysis**: Responses are analyzed based on HTTP status code, content length, and directory listing indicators.
4. **Recursive Crawling**: Discovered pages are parsed for additional links, up to the specified depth.
5. **PHP Site Detection**: Server headers and page contents are examined to identify PHP-based applications.
6. **Result Display**: Valid paths are displayed with metadata including response code and listing status.

---

## Tech Stack

### Frontend
- **React**: UI development
- **Axios**: API communication
- **CSS**: Responsive design

### Backend
- **FastAPI**: High-performance Python web framework
- **BeautifulSoup4**: HTML parsing
- **Requests**: HTTP client library

### Infrastructure
- **Docker & Docker Compose**: Containerization and orchestration
- **TOR Proxy**: Access `.onion` domains via SOCKS5 proxy

---

## Installation & Execution

### Prerequisites
- Docker
- Docker Compose

### Run Locally

```bash
# Clone the repository
git clone <repository-url>
cd directory_scanner

# Launch the application
docker-compose up -d
````

Access the app via:

* Frontend: [http://localhost:3000](http://localhost:3000)
* Backend API: [http://localhost:8000](http://localhost:8000)

---

## How to Use

1. Enter one target URL per line in the input field.
2. Select the scan mode (standard or dark web).
3. Set the maximum crawling depth and choose whether to obey `robots.txt`.
4. (Optional) Edit the dictionary or define exclusion rules.
5. Click the **"Start Scan"** button.
6. View results in the dashboard or download the report in JSON format.

---

## License

MIT License

---

