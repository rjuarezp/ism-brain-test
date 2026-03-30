#!/usr/bin/env python3
"""ISM Brain Test — REST API Tester.

Sends GET/POST requests to a configurable REST endpoint and displays
the response.  Multiple named configurations can be saved and loaded
from JSON files.
"""

import json
import sys
from pathlib import Path

import requests
from PySide6.QtCore import QThread, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

class RequestWorker(QThread):
    """Executes an HTTP request in a background thread."""

    # Emits (response | None, error_message | None)
    finished = Signal(object, object)

    def __init__(self, method: str, url: str, payload: dict | None = None):
        super().__init__()
        self.method = method
        self.url = url
        self.payload = payload

    def run(self):
        try:
            if self.method == "GET":
                resp = requests.get(self.url, timeout=10)
            else:  # POST
                resp = requests.post(self.url, json=self.payload, timeout=10)
            self.finished.emit(resp, None)
        except Exception as exc:
            self.finished.emit(None, str(exc))


# ---------------------------------------------------------------------------
# Application controller
# ---------------------------------------------------------------------------

class AppController:
    """Owns the main window and handles all application logic."""

    def __init__(self):
        self._configs: dict = {}          # name → config dict
        self._config_file: str | None = None
        self._worker: RequestWorker | None = None

        loader = QUiLoader()
        ui_path = str(Path(__file__).parent / "mainwindow.ui")
        self.window = loader.load(ui_path)
        if self.window is None:
            raise RuntimeError(
                f"Could not load UI file '{ui_path}': {loader.errorString()}"
            )

        self._connect_signals()
        # Initialise payload visibility to match the default method (GET)
        self._on_method_changed(self.window.comboMethod.currentText())

    # ── Signal wiring ───────────────────────────────────────────────────────

    def _connect_signals(self):
        w = self.window
        w.btnSend.clicked.connect(self._send_request)
        w.btnSaveConfig.clicked.connect(self._save_config_to_list)
        w.btnApplyConfig.clicked.connect(self._apply_selected_config)
        w.btnOpenFile.clicked.connect(self._open_config_file)
        w.btnSaveFile.clicked.connect(self._save_config_file)
        w.comboMethod.currentTextChanged.connect(self._on_method_changed)
        w.actionOpenFile.triggered.connect(self._open_config_file)
        w.actionSaveFile.triggered.connect(self._save_config_file)
        w.actionSaveFileAs.triggered.connect(self._save_config_file_as)
        w.actionExit.triggered.connect(w.close)

    # ── UI helpers ──────────────────────────────────────────────────────────

    def _on_method_changed(self, method: str):
        """Show the payload group only for POST requests."""
        self.window.groupPayload.setVisible(method == "POST")

    def _build_url(self) -> str:
        w = self.window
        host = w.lineEditHost.text().strip()
        port = w.lineEditPort.text().strip()
        endpoint = w.lineEditEndpoint.text().strip()
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        base = f"http://{host}:{port}" if port else f"http://{host}"
        return base + endpoint

    def _form_to_dict(self) -> dict:
        w = self.window
        return {
            "host": w.lineEditHost.text(),
            "port": w.lineEditPort.text(),
            "method": w.comboMethod.currentText(),
            "endpoint": w.lineEditEndpoint.text(),
            "payload": w.plainTextPayload.toPlainText(),
        }

    def _dict_to_form(self, data: dict):
        w = self.window
        w.lineEditHost.setText(data.get("host", ""))
        w.lineEditPort.setText(data.get("port", ""))
        idx = w.comboMethod.findText(data.get("method", "GET"))
        w.comboMethod.setCurrentIndex(max(idx, 0))
        w.lineEditEndpoint.setText(data.get("endpoint", ""))
        w.plainTextPayload.setPlainText(data.get("payload", ""))

    # ── HTTP request ────────────────────────────────────────────────────────

    def _send_request(self):
        w = self.window
        if not w.lineEditHost.text().strip():
            QMessageBox.warning(w, "Missing host", "Please enter a host address.")
            return

        method = w.comboMethod.currentText()
        payload = None

        if method == "POST":
            text = w.plainTextPayload.toPlainText().strip()
            if text:
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError as exc:
                    QMessageBox.critical(
                        w, "Invalid JSON", f"Payload is not valid JSON:\n{exc}"
                    )
                    return

        url = self._build_url()
        w.plainTextResponse.setPlainText(f"Sending {method} {url} …")
        w.btnSend.setEnabled(False)

        self._worker = RequestWorker(method, url, payload)
        self._worker.finished.connect(self._on_request_done)
        self._worker.start()

    def _on_request_done(self, response, error):
        w = self.window
        w.btnSend.setEnabled(True)

        if error:
            w.plainTextResponse.setPlainText(f"Error:\n{error}")
            return

        lines = [f"Status: {response.status_code} {response.reason}", "", "Headers:"]
        for k, v in response.headers.items():
            lines.append(f"  {k}: {v}")
        lines += ["", "Body:"]
        try:
            lines.append(json.dumps(response.json(), indent=2))
        except Exception:
            lines.append(response.text)

        w.plainTextResponse.setPlainText("\n".join(lines))

    # ── Configuration management ────────────────────────────────────────────

    def _save_config_to_list(self):
        """Save the current form values under the given name."""
        w = self.window
        name = w.lineEditConfigName.text().strip()
        if not name:
            QMessageBox.warning(w, "No name", "Enter a name for this configuration.")
            return
        self._configs[name] = self._form_to_dict()
        if w.comboConfigs.findText(name) == -1:
            w.comboConfigs.addItem(name)
        w.statusBar().showMessage(f"Configuration '{name}' saved to list.")

    def _apply_selected_config(self):
        """Load the selected configuration into the form."""
        w = self.window
        name = w.comboConfigs.currentText()
        if name not in self._configs:
            return
        w.lineEditConfigName.setText(name)
        self._dict_to_form(self._configs[name])
        w.statusBar().showMessage(f"Applied configuration '{name}'.")

    def _open_config_file(self):
        """Load all configurations from a JSON file."""
        w = self.window
        path, _ = QFileDialog.getOpenFileName(
            w, "Open Configurations", "configs", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            QMessageBox.critical(w, "Load Error", str(exc))
            return
        self._configs = data
        self._config_file = path
        w.comboConfigs.clear()
        for name in self._configs:
            w.comboConfigs.addItem(name)
        w.statusBar().showMessage(
            f"Loaded {len(self._configs)} configuration(s) from {path}"
        )

    def _save_config_file(self):
        if not self._config_file:
            self._save_config_file_as()
        else:
            self._write_configs(self._config_file)

    def _save_config_file_as(self):
        w = self.window
        path, _ = QFileDialog.getSaveFileName(
            w, "Save Configurations", "configs", "JSON Files (*.json)"
        )
        if not path:
            return
        if not path.endswith(".json"):
            path += ".json"
        self._config_file = path
        self._write_configs(path)

    def _write_configs(self, path: str):
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._configs, f, indent=2, ensure_ascii=False)
            self.window.statusBar().showMessage(
                f"Saved {len(self._configs)} configuration(s) to {path}"
            )
        except Exception as exc:
            QMessageBox.critical(self.window, "Save Error", str(exc))

    def show(self):
        self.window.show()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    controller = AppController()
    controller.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
