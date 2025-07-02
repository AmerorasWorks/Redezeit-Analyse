import sys
import os
import threading
import webbrowser
import socket
from streamlit.web import cli as stcli


def find_free_port() -> int:
    """
    Bindet kurzzeitig an Port 0 und gibt den so zugewiesenen
    freien Port zurück.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def open_browser(delay: float, port: int):
    """
    Öffnet nach kurzer Verzögerung den Standard-Browser
    zum Streamlit-Server.
    """

    def _open():
        webbrowser.open(f"http://localhost:{port}", new=2)

    timer = threading.Timer(delay, _open)
    timer.daemon = True
    timer.start()


def main():
    # 1) Wenn wir als gebündelte EXE laufen, liegt unsere App im _MEIPASS:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    app_script = os.path.join(base, "app.py")

    # 2) Freien Port suchen und Browser öffnen
    port = find_free_port()
    print(f"🚀 Starte Streamlit auf Port {port}")
    open_browser(delay=1.0, port=port)

    # 3) Argumente für den Streamlit-CLI-Aufruf
    sys.argv = [
        "streamlit",
        "run",
        app_script,
        "--global.developmentMode=false",
        f"--server.port={port}",
        "--server.headless=true",
    ]

    # 4) Starte Streamlit CLI
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
