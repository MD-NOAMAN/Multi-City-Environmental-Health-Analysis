import requests
import pandas as pd

cities = {
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Gulbarga": {"lat": 17.3376, "lon": 76.8379}
}

all_city_data = []

for city_name, coords in cities.items():
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={coords['lat']}&longitude={coords['lon']}&"
        f"hourly=temperature_2m,relative_humidity_2m,precipitation,"
        f"wind_speed_10m,surface_pressure&past_days=30"
    )
    aq_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={coords['lat']}&longitude={coords['lon']}&"
        f"hourly=pm2_5,pm10,nitrogen_dioxide,ozone&past_days=30"
    )

    w_res = requests.get(weather_url).json()
    aq_res = requests.get(aq_url).json()

    if "hourly" not in w_res or "hourly" not in aq_res:
        print(f"Skipping {city_name}: missing 'hourly' key "
              f"(weather error: {w_res.get('reason')}, aq error: {aq_res.get('reason')})")
        continue

    # Build each source into its own DataFrame — this avoids the
    # "mixing dicts with non-Series" error because pandas is handed
    # a clean dict-of-equal-length-lists each time.
    df_w = pd.DataFrame(w_res["hourly"])
    df_aq = pd.DataFrame(aq_res["hourly"])

    # Align on timestamp instead of assuming identical row order/length
    df_city = pd.merge(df_w, df_aq, on="time", how="inner", suffixes=("_w", "_aq"))
    df_city.insert(0, "city", city_name)
    df_city.rename(columns={"time": "timestamp"}, inplace=True)

    all_city_data.append(df_city)

df_raw_master = pd.concat(all_city_data, ignore_index=True)
df_raw_master.to_csv("raw_air_weather_data.csv", index=False)
print(f"Extraction complete! Total rows fetched: {len(df_raw_master)}")
display(df_raw_master.head())
import pandas as pd
from sqlalchemy import create_engine, text

# 1. Read your local CSV file
df = pd.read_csv("raw_air_weather_data.csv")

# 2. Set up your local MySQL connection 
db_user = "root"
db_password = "password" 
db_host = "localhost"
db_port = "3306"
db_name = "air_quality_project"

# Create database if it doesn't exist
engine_temp = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}")
with engine_temp.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name};"))

# Connect directly to the project database
engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# 3. Load data into a staging table
table_name = "staging_air_weather"
df.to_sql(table_name, con=engine, if_exists="replace", index=False)

print(f"Successfully loaded {len(df)} rows into MySQL table '{table_name}'!")
import pandas as pd
from sqlalchemy import create_engine

db_user = "root"
db_password = "password"  # Update with your password
db_host = "localhost"
db_port = "3306"
db_name = "air_quality_project"

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# Pull raw staging data back into Pandas
df = pd.read_sql("SELECT * FROM staging_air_weather", con=engine)
print(f"Retrieved {len(df)} rows from SQL staging table.")
import pandas as pd
import numpy as np

df = pd.read_csv("raw_air_weather_data.csv")

df.head(20)
df.info()
df.describe()
import pandas as pd
from sqlalchemy import create_engine

db_user = "root"
db_password = "password"  # Update with your actual password
db_host = "localhost"
db_port = "3306"
db_name = "air_quality_project"

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")

# Pull data cleanly using a context manager to handle the connection safely
with engine.connect() as connection:
    df = pd.read_sql("SELECT * FROM staging_air_weather", con=connection)

print(f"Retrieved {len(df)} rows from SQL staging table.")
display(df.head())

import pandas as pd
import numpy as np

RAW_PATH = "raw_air_weather_data.csv"
CLEAN_PATH = "output/clean_air_weather_data.csv"


# 1. LOAD

df = pd.read_csv(RAW_PATH)
print(f"[1] Loaded raw data: {df.shape[0]} rows, {df.shape[1]} cols")


# 2. STANDARDIZE COLUMN NAMES & TEXT FIELDS

df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# Clean city names: strip whitespace, fix casing, collapse internal spaces
df["city"] = (
    df["city"]
    .astype(str)
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
    .str.title()
)

# Catch near-duplicate city spellings (e.g. "Bangalore" vs "Bengaluru")
city_alias_map = {
    "Bangalore": "Bengaluru",
    "Calcutta": "Kolkata",
    "Madras": "Chennai",
    "Bombay": "Mumbai",
}
df["city"] = df["city"].replace(city_alias_map)

print("[2] Cities found:", sorted(df["city"].unique()))


# 3. FIX DTYPES

df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

numeric_cols = [
    "temperature_2m", "relative_humidity_2m", "precipitation",
    "wind_speed_10m", "surface_pressure", "pm2_5", "pm10",
    "nitrogen_dioxide", "ozone",
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Any rows where timestamp failed to parse are unusable -> drop
bad_ts = df["timestamp"].isna().sum()
if bad_ts:
    print(f"    Dropping {bad_ts} rows with unparseable timestamps")
    df = df.dropna(subset=["timestamp"])

print("[3] Dtypes fixed:")
print(df.dtypes)


# 4. HANDLE DUPLICATES

exact_dupes = df.duplicated().sum()
df = df.drop_duplicates()
print(f"[4] Dropped {exact_dupes} exact duplicate rows")

key_dupes = df.duplicated(subset=["city", "timestamp"]).sum()
if key_dupes:
    print(f"    Found {key_dupes} duplicate (city, timestamp) keys -> keeping last reading")
    df = df.drop_duplicates(subset=["city", "timestamp"], keep="last")
else:
    print("    No duplicate (city, timestamp) keys")

# 5. HANDLE MISSING VALUES

missing_summary = df.isna().sum()
print("[5] Missing values per column:\n", missing_summary[missing_summary > 0] if missing_summary.any() else "    None found")

if df[numeric_cols].isna().any().any():
    df = df.sort_values(["city", "timestamp"])
    # Time-aware fill: interpolate within each city's own hourly series first,
    # then forward/backward fill any remaining edge gaps.
    df[numeric_cols] = (
        df.groupby("city")[numeric_cols]
        .transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
    )
    # Fallback: if a whole city-column was NaN, fill with global column median
    for col in numeric_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(df[col].median())
    print("    Missing numeric values imputed via per-city linear interpolation")

# Drop rows still missing the essential keys
before = len(df)
df = df.dropna(subset=["city", "timestamp"])
if len(df) < before:
    print(f"    Dropped {before - len(df)} rows with missing city/timestamp")

# 6. VALIDATE / FIX OUT-OF-RANGE VALUES

def clip_report(series, low, high, name):
    n_bad = ((series < low) | (series > high)).sum()
    if n_bad:
        print(f"    {name}: {n_bad} values outside [{low}, {high}] -> clipped")
    return series.clip(lower=low, upper=high)

print("[6] Validating physical ranges")
df["relative_humidity_2m"] = clip_report(df["relative_humidity_2m"], 0, 100, "relative_humidity_2m")
for col in ["precipitation", "wind_speed_10m", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"]:
    df[col] = clip_report(df[col], 0, df[col].max(), col)  # no negative pollutant/weather readings

# Surface pressure: sane range for sea-level-adjusted station pressure (hPa)
df["surface_pressure"] = clip_report(df["surface_pressure"], 850, 1085, "surface_pressure")

# Temperature: sane range for these cities (Celsius)
df["temperature_2m"] = clip_report(df["temperature_2m"], -10, 55, "temperature_2m")

# Logical check: PM10 should be >= PM2.5 (PM2.5 is a subset of PM10 by definition)
inconsistent = (df["pm10"] < df["pm2_5"]).sum()
if inconsistent:
    print(f"    {inconsistent} rows where pm10 < pm2_5 -> setting pm10 = pm2_5 (data-entry fix)")
    df.loc[df["pm10"] < df["pm2_5"], "pm10"] = df["pm2_5"]
else:
    print("    pm10 >= pm2_5 holds for all rows")

# 7. CHECK FOR MISSING HOURLY TIMESTAMPS (GAPS) PER CITY

print("[7] Checking hourly continuity per city")
gap_rows = []
for city, g in df.groupby("city"):
    g = g.sort_values("timestamp")
    full_range = pd.date_range(g["timestamp"].min(), g["timestamp"].max(), freq="h")
    missing_hours = full_range.difference(g["timestamp"])
    if len(missing_hours):
        print(f"    {city}: {len(missing_hours)} missing hour(s)")
        gap_rows.append(
            pd.DataFrame({"city": city, "timestamp": missing_hours})
        )

if gap_rows:
    gaps_df = pd.concat(gap_rows, ignore_index=True)
    df = pd.concat([df, gaps_df], ignore_index=True)
    df = df.sort_values(["city", "timestamp"])
    df[numeric_cols] = (
        df.groupby("city")[numeric_cols]
        .transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
    )
    print(f"    Inserted {len(gaps_df)} missing hourly rows and interpolated their values")
else:
    print("    No gaps found — every city has a complete hourly series")

# 8. FINAL SORT, RESET INDEX, SCHEMA CHECK

df = df.sort_values(["city", "timestamp"]).reset_index(drop=True)

expected_cols = [
    "city", "timestamp", "temperature_2m", "relative_humidity_2m",
    "precipitation", "wind_speed_10m", "surface_pressure",
    "pm2_5", "pm10", "nitrogen_dioxide", "ozone",
]
assert list(df.columns) == expected_cols, f"Unexpected schema: {df.columns.tolist()}"
assert df.isna().sum().sum() == 0, "Nulls remain after cleaning!"
assert df.duplicated(subset=["city", "timestamp"]).sum() == 0, "Duplicate keys remain!"

print(f"[8] Final cleaned shape: {df.shape}")
print(df.dtypes)


# 9. EXPORT & LOAD BACK TO MYSQL


CLEAN_PATH = r"clean_air_weather_data.csv"
df.to_csv(CLEAN_PATH, index=False)
print(f"[9] Saved cleaned data -> {CLEAN_PATH}")

from sqlalchemy import create_engine
db_user = "root"
db_password = "password"  # Update with your password
db_host = "localhost"
db_port = "3306"
db_name = "air_quality_project"

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")
df.to_sql("clean_air_weather", con=engine, if_exists="replace", index=False, chunksize=1000)
print("Successfully loaded cleaned data into MySQL table `clean_air_weather`!")

