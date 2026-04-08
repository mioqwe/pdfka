import asyncio
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Set

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from pdfka.pdf_generator import PDFGenerator
from pdfka.template import TemplateContext
from pdfka.utils import validate_json_structure

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str):
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.add(connection)
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


def get_input_file_path(input_path: Optional[str]) -> Path:
    if input_path:
        return PROJECT_ROOT / input_path
    return PROJECT_ROOT / "input" / "example_input.json"


def load_input_json(input_path: Optional[str]) -> Dict[str, Any]:
    file_path = get_input_file_path(input_path)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_preview_html(input_path: Optional[str] = None) -> str:
    json_data = load_input_json(input_path)
    validate_json_structure(json_data)

    context = TemplateContext(
        name=json_data.get("name"),
        rating=json_data.get("rating"),
        reviews=json_data.get("reviews"),
    )

    generator = PDFGenerator()
    return generator.generate_full_preview(json_data, context)


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def preview_endpoint(request):
    input_path = request.query_params.get("input")
    try:
        html = generate_preview_html(input_path)
        return HTMLResponse(html)
    except Exception as e:
        return HTMLResponse(f"<pre>Error: {e}</pre>", status_code=500)


async def data_endpoint(request):
    input_path = request.query_params.get("input")
    try:
        data = load_input_json(input_path)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def css_endpoint(request):
    css_path = PROJECT_ROOT / "templates" / "tailwind.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        return HTMLResponse(css_content, media_type="text/css")
    return HTMLResponse("/* CSS not found */", status_code=404)


async def live_preview_page(request):
    from starlette.staticfiles import StaticFiles

    html_content = get_live_preview_html()
    return HTMLResponse(html_content)


def get_live_preview_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Live Preview</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            height: 100vh;
        }
        
        .sidebar {
            width: 320px;
            background: #16213e;
            border-right: 1px solid #0f3460;
            display: flex;
            flex-direction: column;
            transition: width 0.3s ease;
        }
        
        .sidebar.collapsed {
            width: 48px;
        }
        
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid #0f3460;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .sidebar-header h2 {
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
        }
        
        .toggle-btn {
            background: none;
            border: none;
            color: #eee;
            cursor: pointer;
            padding: 4px;
            font-size: 18px;
        }
        
        .json-content {
            flex: 1;
            overflow: auto;
            padding: 16px;
        }
        
        .json-content pre {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-all;
        }
        
        .main {
            flex: 1;
            overflow: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .pages {
            display: flex;
            flex-direction: column;
            gap: 32px;
        }
        
        .pdf-page {
            width: 297mm;
            height: 210mm;
            background: white;
            position: relative;
            overflow: hidden;
            flex-shrink: 0;
        }
        
        .preview-frame {
            width: 297mm;
            height: 210mm;
            border: none;
            background: white;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transform-origin: top center;
            display: block;
            margin-bottom: 32px;
        }
        
        .status-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #16213e;
            border-top: 1px solid #0f3460;
            padding: 8px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #4ade80;
        }
        
        .status-dot.disconnected {
            background: #f87171;
        }
        
        .nav-buttons {
            display: flex;
            gap: 8px;
        }
        
        .nav-btn {
            background: #0f3460;
            border: none;
            color: #eee;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .nav-btn:hover {
            background: #1a4a7a;
        }
        
        .page-nav {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 16px;
        }
        
        .page-nav span {
            color: #888;
            font-size: 14px;
        }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h2 class="hidden" id="sidebarTitle">Input JSON</h2>
                <button class="toggle-btn" id="toggleSidebar">☰</button>
            </div>
            <div class="json-content" id="jsonContent">
                <pre id="jsonPre">Loading...</pre>
            </div>
        </div>
        
        <div class="main">
            <div class="page-nav">
                <button class="nav-btn" id="prevBtn">← Prev</button>
                <span id="pageIndicator">Page 1 of 1</span>
                <button class="nav-btn" id="nextBtn">Next →</button>
            </div>
            
            <div class="pages" id="pagesContainer">
                <iframe class="preview-frame" id="previewFrame" sandbox="allow-same-origin"></iframe>
            </div>
        </div>
    </div>
    
    <div class="status-bar">
        <div class="status-indicator">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">Connected</span>
        </div>
        <div class="nav-buttons">
            <button class="nav-btn" id="refreshBtn">Refresh</button>
        </div>
    </div>

    <script>
        let ws = null;
        let currentPage = 0;
        let pages = [];
        
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const pagesContainer = document.getElementById('pagesContainer');
        const pageIndicator = document.getElementById('pageIndicator');
        const sidebar = document.getElementById('sidebar');
        const toggleBtn = document.getElementById('toggleSidebar');
        const jsonPre = document.getElementById('jsonPre');
        const sidebarTitle = document.getElementById('sidebarTitle');
        
        function connectWS() {
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${location.host}/ws`);
            
            ws.onopen = () => {
                statusDot.classList.remove('disconnected');
                statusText.textContent = 'Connected';
            };
            
            ws.onclose = () => {
                statusDot.classList.add('disconnected');
                statusText.textContent = 'Disconnected - Reconnecting...';
                setTimeout(connectWS, 2000);
            };
            
            ws.onmessage = (event) => {
                if (event.data === 'reload') {
                    loadPreview();
                }
            };
        }
        
        async function loadPreview() {
            try {
                const [previewRes, cssRes] = await Promise.all([
                    fetch('/preview'),
                    fetch('/css')
                ]);
                const html = await previewRes.text();
                const css = await cssRes.text();
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const pageDivs = doc.querySelectorAll('.pdf-page');
                
                pagesContainer.innerHTML = '';
                pages = [];
                
                pageDivs.forEach((pageDiv, index) => {
                    const frame = document.createElement('iframe');
                    frame.className = 'preview-frame';
                    frame.sandbox = 'allow-same-origin';
                    
                    const pageHtml = `<!doctype html><html><head><meta charset="UTF-8"><style>${css}</style></head><body>${pageDiv.outerHTML}</body></html>`;
                    
                    frame.srcdoc = pageHtml;
                    pagesContainer.appendChild(frame);
                    pages.push(frame);
                });
                
                updatePageIndicator();
                fitPagesToScreen();
            } catch (e) {
                console.error('Failed to load preview:', e);
            }
        }
        
        async function loadJSON() {
            try {
                const response = await fetch('/data');
                const data = await response.json();
                jsonPre.textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                jsonPre.textContent = 'Failed to load JSON';
            }
        }
        
        function updatePageIndicator() {
            pageIndicator.textContent = `Page ${currentPage + 1} of ${pages.length}`;
        }
        
        function scrollToPage(index) {
            if (index >= 0 && index < pages.length) {
                currentPage = index;
                pages[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
                updatePageIndicator();
            }
        }
        
        function fitPagesToScreen() {
            if (pages.length === 0) return;
            const screenHeight = window.innerHeight - 150;
            const scale = screenHeight / (210 * 3.78);
            const clampedScale = Math.min(scale, 1);
            pages.forEach(frame => {
                frame.style.transform = `scale(${clampedScale})`;
            });
        }
        
        document.getElementById('prevBtn').addEventListener('click', () => scrollToPage(currentPage - 1));
        document.getElementById('nextBtn').addEventListener('click', () => scrollToPage(currentPage + 1));
        document.getElementById('refreshBtn').addEventListener('click', loadPreview);
        
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            if (sidebar.classList.contains('collapsed')) {
                toggleBtn.textContent = '☰';
                sidebarTitle.classList.add('hidden');
            } else {
                toggleBtn.textContent = '✕';
                sidebarTitle.classList.remove('hidden');
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') scrollToPage(currentPage - 1);
            if (e.key === 'ArrowRight') scrollToPage(currentPage + 1);
            if (e.key === 'r' && e.ctrlKey) {
                e.preventDefault();
                loadPreview();
            }
        });
        
        window.addEventListener('resize', fitPagesToScreen);
        
        loadPreview();
        loadJSON();
        connectWS();
    </script>
</body>
</html>"""


routes = [
    Route("/", lambda request: RedirectResponse(url="/live_preview")),
    Route("/live_preview", live_preview_page),
    Route("/preview", preview_endpoint),
    Route("/data", data_endpoint),
    Route("/css", css_endpoint),
    WebSocketRoute("/ws", websocket_endpoint),
]

app = Starlette(routes=routes)

fonts_dir = PROJECT_ROOT / "fonts"
if fonts_dir.exists():
    app.mount("/fonts", StaticFiles(directory=str(fonts_dir)), name="fonts")


class FileWatcher:
    def __init__(self, input_path: Optional[str] = None):
        self.input_path = input_path
        self.should_stop = False
        self.last_modified = {}

    def get_mtime(self, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except:
            return 0

    def watch(self):
        import time
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler, FileModifiedEvent

        class Handler(FileSystemEventHandler):
            def __init__(self, watcher):
                self.watcher = watcher

            def on_modified(self, event):
                if event.is_directory:
                    return
                path = Path(event.src_path).resolve()
                if path.suffix in [".html", ".css", ".py", ".json"]:
                    asyncio.run(self.watcher.trigger_reload())

        observer = Observer()

        paths_to_watch = [
            PROJECT_ROOT / "templates",
            PROJECT_ROOT / "pdfka",
        ]

        input_file = get_input_file_path(self.input_path)
        if input_file.exists():
            paths_to_watch.append(input_file.parent)

        for path in paths_to_watch:
            if path.exists():
                observer.schedule(Handler(self), str(path), recursive=True)

        observer.start()

        try:
            while not self.should_stop:
                time.sleep(0.5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    async def trigger_reload(self):
        await manager.broadcast("reload")


def start_file_watcher(input_path: Optional[str] = None):
    watcher = FileWatcher(input_path)
    thread = threading.Thread(target=watcher.watch, daemon=True)
    thread.start()
    return watcher


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5500)
