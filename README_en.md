#  Redezeit Web Metrics Analysis

This repository hosts the collaborative data analysis project focused on [Redezeit.de](https://www.redezeit.de), a non-profit platform where individuals can find someone to listen when they feel they have no one else. The platform is sustained by trained, pro bono listeners, and makes no profit. Our goal is to support Redezeit’s mission by using data to improve outreach and understand how users engage with the website.

---

##  Project Overview

We aim to extract publicly available web metrics from Redezeit's Looker Studio dashboard via web scraping, analyze them using Python, and visualize insights in Power BI. While still in early development, the first objective is to identify user behavior and traffic trends—data that could later guide strategic improvements in visibility, reach, and usability.

---

##  Team

This project is developed by a team of data analysts-in-training:

- **Bernardo**
- **Birol**
- **Dorian**
- **Michael**

---

##  Tech Stack (Work in Progress)

- **Python**: Data extraction, processing, and transformation  
  - `pandas`, `numpy`, (and potentially `BeautifulSoup`, `requests`, etc.)
- **Power BI**: Interactive dashboards for visualizing trends
- **Looker Studio**: Source of web metrics

This list will expand as the project grows.

---

##  Key Metrics Targeted

- Visitor counts
- Bounce rates
- Session durations
- Landing page performance
- Referral sources (e.g., search engines, external links)

These metrics will help identify how users arrive at and interact with Redezeit's platform.

---

##  Project Structure (to be updated)

```bash
├── data/                # Raw and cleaned data
├── scripts/             # Python scripts for scraping and preprocessing
├── notebooks/           # Jupyter notebooks with analysis
├── visualizations/      # Power BI dashboards or exports
├── README.md
└── requirements.txt     # Python dependencies
