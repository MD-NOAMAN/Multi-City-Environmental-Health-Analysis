# Multi-City-Environmental-Health-Analysis


An end-to-end telemetry and analytics platform that ingests raw weather and pollutant data from the Open-Meteo API, transforms and queries it using SQL, and visualizes dynamic health risk insights through an interactive Power BI dashboard.

---

## 📊 Executive Summary
This project bridges data engineering and environmental analytics by capturing real-time environmental indicators across multiple cities. The system tracks key pollutants ($\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{NO}_2$, Ozone) alongside meteorological telemetry (Temperature, Humidity, Heat Index) to evaluate local pollution spikes and environmental health risks.

---

## 🛠️ Tech Stack & Tools
* **Data Ingestion:** Python, Open-Meteo API (`requests`, `pandas`)
* **Database & Transformation:** SQL / SQLite (`clean_air_weather` schema)
* **Business Intelligence:** Power BI, DAX (Data Analysis Expressions)
* **Advanced Analytics:** Power BI Field Parameters, Bing Maps Spatial Analytics, Dynamic Heat Stress Modeling

---

## 🔄 End-to-End Architecture

1. **API Ingestion:** Automated raw data extraction from the Open-Meteo API using Python to gather historical multi-city environmental telemetry.
2. **SQL Transformation:** Executed SQL queries to clean, type-cast, and structure raw data into an optimized database table (`clean_air_weather`).
3. **DAX & Feature Engineering:**
   * Formulated DAX algorithms for **Heat Index (°C)** and **5-tier Heat Stress** classifications.
   * Applied `Sort Order` auxiliary columns to eliminate DAX circular dependency errors.
4. **Dynamic Field Parameters:** Implemented Field Parameters paired with DAX logic (`SWITCH`, `MAX`) to dynamically drive KPI cards, dynamic labels, and visual axes across all 4 pollutants on a single canvas.

---

## 📈 Dashboard Features
* **Air Quality Trend Over Time:** Continuous time-series line chart supporting date hierarchy drill-downs (Month ➔ Day).
* **Peak Pollution by City:** Sorted column ranking identifying regional health hotspots.
* **Environmental Factor Split:** Dual-metric bar chart evaluating underlying temperature and humidity weather drivers.
* **Geospatial Hotspots Map:** Spatial visualization with dynamic bubble sizes scaled to active pollutant levels.

* > 📖 **Detailed Technical Guide:** For full Python code walkthroughs, SQL analytical queries, and Power BI DAX debugging steps, check out the separate [DOCUMENTATION.md](DOCUMENTATION.md) file.
