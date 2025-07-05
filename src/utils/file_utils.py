import sys
import os
import streamlit as st


def resource_path(relative_path: str) -> str:
    """
    Gibt den Pfad zu einer Ressource relativ zum Arbeitsverzeichnis zurück.
    Funktioniert im PyInstaller-Bundle und im Dev-Modus.
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def load_custom_css(relative_css_path: str):
    css_file = resource_path(relative_css_path)
    if not os.path.isfile(css_file):
        st.error(f"CSS nicht gefunden: {css_file}")
        return
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_project_root():
    # PyInstaller: sys._MEIPASS existiert nur bei gebündelten EXEs
    if hasattr(sys, "_MEIPASS"):
        # Wir nehmen den Ordner der EXE, eine Ebene höher ist meistens das Projekt
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Im Script-Modus: Einmal hoch zum Projektordner (z.B. von src/utils/)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


base_dir = get_project_root()
output_folder = os.path.normpath(os.path.join(base_dir, "src", "data", "raw"))
os.makedirs(output_folder, exist_ok=True)


def get_output_folder(subfolder="raw"):
    base_dir = get_project_root()
    output_folder = os.path.normpath(os.path.join(base_dir, "src", "data", subfolder))
    os.makedirs(output_folder, exist_ok=True)
    return output_folder