# ISM Brain Test — REST API Tester

A desktop application for testing REST API endpoints. Built with Python 3.12 and PySide6, it provides a clean GUI to compose GET and POST requests, inspect responses, and manage multiple named configurations persisted as JSON files.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Running with Docker (recommended)](#running-with-docker-recommended)
- [Running Locally (without Docker)](#running-locally-without-docker)
- [Usage Guide](#usage-guide)
- [Configuration File Format](#configuration-file-format)
- [Customising the UI](#customising-the-ui)

---

## Features

- Configure server **host**, **port**, and **endpoint** from the GUI
- Choose between **GET** and **POST** HTTP methods
- Enter a **JSON payload** for POST requests (payload panel auto-hides for GET)
- View the full response: status code, headers, and formatted body
- Save and load **named configurations** — group multiple configurations in a single JSON file
- Configurations are **persisted to disk** and survive container restarts

---

## Requirements

### To run with Docker (recommended)

| Requirement | Version |
|---|---|
| Docker Engine | 24.x or later |
| Docker Compose | v2 plugin or later |
| An X11 display server | (any modern Linux desktop) |

### To run locally

| Requirement | Version |
|---|---|
| Python | 3.12 or later |
| PySide6 | 6.6.0 or later |
| requests | 2.31.0 or later |

---

## Project Structure

```
ism-brain-test/
├── main.py              # Application entry point and all logic
├── mainwindow.ui        # Qt Designer UI definition file
├── requirements.txt     # Python package dependencies
├── Dockerfile           # Container image definition
├── docker-compose.yaml  # Compose service definition
├── .dockerignore        # Files excluded from the Docker build context
├── configs/             # Default directory for saved configuration files
│   └── .gitkeep
├── SPECS.md             # Original application specification
└── README.md            # This file
```

---

## Running with Docker (recommended)

This is the easiest way to get started. Docker handles all Python and Qt dependencies.

### 1 — Prerequisites

Make sure Docker and the Compose plugin are installed:

```bash
docker --version
docker compose version
```

### 2 — Allow the container to access your X display

The GUI is rendered on your host display via X11 forwarding. Run this once per session (or add it to your shell profile):

```bash
xhost +local:docker
```

### 3 — Build and start the application

```bash
cd ism-brain-test
docker compose up --build
```

The `--build` flag is only needed the first time or after any source file changes. Subsequent starts can use:

```bash
docker compose up
```

### 4 — Stop the application

Close the window or press `Ctrl+C` in the terminal. To remove the container:

```bash
docker compose down
```

### Persisting saved configurations

The `./configs/` directory on the host is bind-mounted into the container at `/app/configs`. Any configuration files you save from within the application will appear in that directory and survive container restarts or rebuilds.

---

## Running Locally (without Docker)

### 1 — Create and activate a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### 3 — Launch the application

```bash
python main.py
```

---

## Usage Guide

### Composing a request

1. Enter the server **Host** (IP address or hostname) and **Port** in the *Server* group.
2. Enter the **Endpoint** path (e.g. `/api/status`).
3. Select the HTTP **Method** (`GET` or `POST`).
   - For `POST` requests, the *Payload (JSON)* panel will appear. Enter a valid JSON object.
4. Click **Send Request**. The response (status, headers, and body) is displayed in the *Response* panel.

### Managing configurations

| Action | How |
|---|---|
| **Name the current form** | Type a name in the *Name* field (top toolbar) |
| **Save to list** | Click **Save** — the config is stored in memory under that name |
| **Apply a saved config** | Select a name from the dropdown, then click **Apply** |
| **Save all configs to disk** | Click **Save File…** or use `File → Save Configurations` (`Ctrl+S`) |
| **Load configs from disk** | Click **Open File…** or use `File → Open Configurations…` (`Ctrl+O`) |
| **Save to a new file** | Use `File → Save Configurations As…` (`Ctrl+Shift+S`) |

Multiple named configurations can coexist in a single JSON file, making it easy to share a configuration set with a colleague.

---

## Configuration File Format

Configuration files are plain JSON and can be edited by hand. Each top-level key is the configuration name.

```json
{
  "Health Check": {
    "host": "192.168.1.100",
    "port": "8080",
    "method": "GET",
    "endpoint": "/api/health",
    "payload": ""
  },
  "Create Device": {
    "host": "192.168.1.100",
    "port": "8080",
    "method": "POST",
    "endpoint": "/api/devices",
    "payload": "{\n  \"name\": \"sensor-01\",\n  \"type\": \"temperature\"\n}"
  }
}
```

---

## Customising the UI

The interface is defined in [mainwindow.ui](mainwindow.ui) and can be edited visually with **Qt Designer**:

```bash
# If running locally with the virtual environment active:
pyside6-designer mainwindow.ui
```

After saving the `.ui` file no compilation step is required — it is loaded at runtime by `QUiLoader`.
