# Redezeit Webanalyse‑Projekt

Dieses Repository hostet das gemeinschaftliche Data‑Analytics‑Projekt rund um Redezeit.de – eine gemeinnützige Plattform, auf der Menschen in emotional schwierigen Situationen kostenlose, pro bono Gespräche mit geschulten Zuhörer\:innen führen können. Unser Ziel ist es, Redezeit durch datenbasierte Einblicke bei der Verbesserung der Reichweite und der Nutzer\:innenbindung zu unterstützen.

## Projektüberblick

Im Fokus steht die Extraktion, Bereinigung und Analyse der Web-Traffic-Daten aus Google Looker Studio. Die wichtigsten KPIs (z. B. Seitenaufrufe, Besucherquellen, Endgeräte, Nutzungsverhalten, etc.) werden automatisiert gesammelt und für Power BI oder Google Looker Studio zur weiteren Analyse aufbereitet.

## Hauptbestandteile

- **Streamlit-App** zur Bedienung des Scraping-Tools (UI mit Login, Zeitraum-Auswahl, Logging)
- **Automatisierte Scraper** für verschiedene Dashboard-Elemente (Landingpages, Events, Besucherquellen usw.)
- **CSV-Handler** zum Speichern und Bereinigen der Rohdaten
- **Datenaufbereitung** für die Weiterverarbeitung in Power BI oder Looker Studio

## Verzeichnisstruktur

```plaintext
├── app.py                # Haupt-Streamlit-App
├── src/
│   ├── utils/            # Hilfsfunktionen (z. B. File, Logging, CSV, Chrome)
│   └── scraper/          # Einzelne Scraper-Module
├── data/
│   ├── raw/              # Gescrapte Rohdaten (CSV)
│   └── clean/            # Bereinigte Daten (CSV)
├── style.css             # Custom CSS für das Streamlit-Layout
└── README.md             # Diese Projektbeschreibung
```

## Installation

1. **Repo klonen:**

   ```bash
   git clone https://github.com/AmerorasWorks/Redezeit-Analyse.git
   cd Redezeit-Analyse
   ```

2. **Python-Umgebung einrichten (empfohlen):**

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux/Mac
   .venv\Scripts\activate         # Windows
   ```

3. **Abhängigkeiten installieren:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Chromedriver bereitstellen:**\
   Lege die aktuelle `chromedriver.exe` ins Hauptverzeichnis (neben app.py).

## Nutzung

1. **Streamlit-App starten:**

   ```bash
   streamlit run app.py
   ```

2. **Im Browser öffnen:**\
   Die Weboberfläche erscheint automatisch. Hier kannst du dich einloggen, den gewünschten Zeitraum wählen und den Scrape-Prozess starten.

3. **Rohdaten werden als CSV abgelegt:**\
   Die Scraper speichern die Daten in `data/raw/`.

4. **Daten bereinigen:**\
   Über die App kannst du die Rohdaten für die weitere Analyse automatisch bereinigen lassen (`data/clean/`).

5. **Berichtserstellung:**\
   Importiere die Clean-Daten in Power BI oder Looker Studio für die Dashboards.

## Mitwirkende

- Hybriz, u. a. Projektleitung, Entwicklung, Data Engineering
- Mitwirkende aus der Redezeit-Community

## Lizenz

Siehe [LICENSE](LICENSE) für Details. Das Projekt steht unter der MIT-Lizenz.

