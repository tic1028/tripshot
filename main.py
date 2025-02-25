import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# Set your desired time zone (e.g., Pacific Time Zone)
TIMEZONE = "US/Pacific"


# Function to convert time to the specified timezone
def convert_to_timezone(dt, timezone):
    tz = pytz.timezone(timezone)
    return dt.astimezone(tz)


# Load bus schedule from a local CSV file
@st.cache_data
def load_data():
    df = pd.read_csv("bus_schedule.csv")  # Load CSV file

    # Ensure "Departure Time" is always in HH:MM:SS format
    df["Departure Time"] = df["Departure Time"].astype(str).str[-8:]  # Extract last 8 characters (HH:MM:SS)
    df["Departure Time"] = pd.to_datetime(df["Departure Time"], format="%H:%M:%S").dt.time  # Convert to time object
    return df


def time_difference(dep_time):
    now = datetime.now(pytz.timezone(TIMEZONE)).time()  # Get current time in the specified time zone
    now_dt = datetime.combine(datetime.today(), now).replace(
        tzinfo=pytz.timezone(TIMEZONE))  # Current time with timezone
    dep_dt = datetime.combine(datetime.today(), dep_time).replace(
        tzinfo=pytz.timezone(TIMEZONE))  # Departure time with timezone

    # If the departure time is before the current time, add one day to the departure time
    if dep_dt < now_dt:
        dep_dt += pd.Timedelta(days=1)

    time_diff = dep_dt - now_dt  # Time difference
    minutes, seconds = divmod(time_diff.seconds, 60)  # Convert to minutes and seconds

    # If the time difference is greater than 2 hours, format as "X hours Y minutes"
    if time_diff.total_seconds() >= 3600:  # 2 hours = 7200 seconds
        hours, minutes = divmod(minutes, 60)  # Convert minutes to hours and remaining minutes
        return f"{hours} hours {minutes} minutes"
    else:
        return f"{minutes} minutes {seconds} seconds"


def get_next_buses(df, route, max_results=4):
    now = datetime.now(pytz.timezone(TIMEZONE)).time()  # Get current time in the specified time zone
    upcoming_buses = df[(df["Route"] == route) & (df["Departure Time"] > now)]

    # Calculate time left for each bus
    upcoming_buses["Time Left"] = upcoming_buses["Departure Time"].apply(time_difference)

    return upcoming_buses.sort_values("Departure Time").head(max_results).reset_index(drop=True)  # Remove index


def get_latest_bus(df, route):
    now = datetime.now(pytz.timezone(TIMEZONE)).time()  # Get current time in the specified time zone
    past_buses = df[(df["Route"] == route) & (df["Departure Time"] < now)]

    # Calculate time left for each bus (even though it will be negative, this shows how long ago the bus departed)
    past_buses["Time Left"] = past_buses["Departure Time"].apply(time_difference)

    if past_buses.empty:
        return None  # No past buses available
    return past_buses.sort_values("Departure Time").iloc[-1:]  # Get the most recent past bus


def get_last_bus_from_work(df):
    """Get the last bus from Work → Palo Alto for today"""
    now = datetime.now(pytz.timezone(TIMEZONE)).time()
    work_to_palo_alto = df[df["Route"] == "Work → Palo Alto"]
    future_buses = work_to_palo_alto[work_to_palo_alto["Departure Time"] > now]

    if future_buses.empty:
        return None  # No buses left today

    # Sort buses by departure time and get the latest one
    last_bus = future_buses.sort_values("Departure Time").iloc[-1:]

    # Calculate time left for the last bus
    last_bus["Time Left"] = last_bus["Departure Time"].apply(time_difference)
    return last_bus


def main():
    # Apply mobile-friendly styles
    st.markdown("""
        <style>
            h2 { text-align: center; }
            table { width: 100%; text-align: center; font-size: 18px; }
            .block-container { padding: 1rem; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚍 Next Available Buses")

    df = load_data()
    if df.empty:
        st.warning("No schedule data found!")
        return

    # Palo Alto → Work Section
    st.header("📍 Palo Alto → Work")
    buses_to_work = get_next_buses(df, "Palo Alto → Work")
    if buses_to_work.empty:
        st.info("No upcoming buses available.")
    else:
        st.table(buses_to_work[["Route", "Departure Time", "Time Left"]])

    st.markdown("<br><hr><br>", unsafe_allow_html=True)  # Spacer for separation

    # Work → Palo Alto Section
    st.header("📍 Work → Palo Alto")
    buses_to_palo_alto = get_next_buses(df, "Work → Palo Alto")
    if buses_to_palo_alto.empty:
        st.info("No upcoming buses available.")
    else:
        st.table(buses_to_palo_alto[["Route", "Departure Time", "Time Left"]])

    st.markdown("<br><hr><br>", unsafe_allow_html=True)  # Spacer for separation

    # Latest Past Bus from Work → Palo Alto
    st.header("🕒 Last Bus (Work → Palo Alto)")
    last_bus = get_last_bus_from_work(df)
    if last_bus is None:
        st.info("No past buses available yet.")
    else:
        st.table(last_bus[["Route", "Departure Time", "Time Left"]])
        st.warning("If you missed this bus, there are no more buses for today. 🛑")


if __name__ == "__main__":
    main()
