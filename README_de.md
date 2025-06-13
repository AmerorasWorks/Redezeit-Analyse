#  Redezeit Webanalyse-Projekt

Dieses Repository dokumentiert unser gemeinsames Data-Analytics-Projekt rund um [Redezeit.de](https://www.redezeit.de) – eine gemeinnützige Plattform, auf der Menschen in emotional schwierigen Situationen kostenlose, pro bono Gespräche mit geschulten Zuhörer:innen führen können. Unser Ziel ist es, Redezeit durch datenbasierte Einblicke bei der Verbesserung der Reichweite und der Nutzer:innenbindung zu unterstützen.

---

##  Projektüberblick

Wir extrahieren öffentlich zugängliche Web-Metriken aus dem Looker-Studio-Dashboard von Redezeit mittels Webscraping, analysieren diese mit Python und bereiten die Ergebnisse in einem interaktiven Power BI Dashboard auf. Der erste Schritt unseres Projekts besteht darin, Besuchsverhalten und Traffic-Trends zu identifizieren, um langfristig Empfehlungen zur Optimierung der Plattform zu geben.

---

##  Team

Das Projekt wird von einem Team angehender Datenanalysten durchgeführt:

- **Bernardo**
- **Birol**
- **Dorian**
- **Michael**

---

##  Technologiestack (wird erweitert)

- **Python**: Für Datenextraktion, -bereinigung und -analyse  
  - `pandas`, `numpy`, (eventuell `BeautifulSoup`, `requests`, usw.)
- **Power BI**: Für Visualisierung und Dashboard-Erstellung
- **Looker Studio**: Quelle der Web-Metriken

Der Stack wird im Laufe des Projekts ergänzt.

---

##  Zielmetriken

Wir konzentrieren uns auf folgende Kennzahlen:

- Besucherzahlen
- Absprungraten (Bounce Rate)
- Sitzungsdauer
- Leistungsanalyse von Landingpages
- Verweisquellen (z. B. Suchmaschinen, externe Links)

Diese Metriken helfen uns, das Nutzungsverhalten besser zu verstehen.

---

##  Projektstruktur (vorläufig)

```bash
├── data/                # Roh- und bereinigte Daten
├── scripts/             # Python-Skripte für Scraping und Verarbeitung
├── notebooks/           # Jupyter Notebooks mit Analysen
├── visualizations/      # Power BI Dashboards und Exporte
├── README.md
└── requirements.txt     # Python-Abhängigkeiten
