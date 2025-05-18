import streamlit as st
import pandas as pd
import psycopg2
import subprocess
import os
import time

st.set_page_config(page_title="Hotel Scraper Tool", layout="wide")
st.title("🏨 Google Maps Hotel Scraper + Viewer")

# --- Database Config ---
DB_HOST = st.secrets["DB_HOST"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]

# --- Scraper Controls ---
st.sidebar.header("🔍 Scraper Settings")
city = st.sidebar.text_input("Enter City/Region", "Leipzig")
language = st.sidebar.selectbox("Language", ["en", "de", "fr", "es"], index=0)
scrape = st.sidebar.button("🚀 Run Scraper")

# --- Write city to query_list.py ---
def update_query_file(city):
    with open("scraper/query_list.py", "w") as f:
        f.write(f"queries = ['{city}']\n")

# --- Modify run.py with city/language if needed ---
def patch_run_py(city, lang):
    path = "scraper/run.py"
    lines = open(path).readlines()
    with open(path, 'w') as file:
        for line in lines:
            if line.strip().startswith("country"):
                file.write(f"country = \"{city}\"\n")
            elif line.strip().startswith("language"):
                file.write(f"language = \"{lang}\"\n")
            else:
                file.write(line)

# --- Run the Scraper via subprocess ---
def run_scraper():
    update_query_file(city)
    patch_run_py(city, language)
    try:
        subprocess.run(["python3", "scraper/run.py"], check=True)
        st.success("Scraping complete!")
    except subprocess.CalledProcessError:
        st.error("Scraper failed. Check logs.")

# --- Load Data from Supabase DB ---
@st.cache_data
def load_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port="5432"
        )
        df = pd.read_sql("SELECT * FROM hotels ORDER BY name", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# --- Scrape if button clicked ---
if scrape:
    st.info(f"Scraping hotels in {city}... please wait")
    run_scraper()
    time.sleep(2)

# --- Data Viewer ---
st.subheader("📊 Scraped Hotel Data")
df = load_data()
if not df.empty:
    st.dataframe(df)
    st.download_button("Download CSV", df.to_csv(index=False), "hotels.csv")
else:
    st.warning("No data found in database.")
