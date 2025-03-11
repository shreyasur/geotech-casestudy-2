import streamlit as st
import requests

# ------------------------
# Helper Functions
# ------------------------

def validate_city(city_name):
    """
    Validate the city name using the Open-Meteo Geocoding API.
    Returns either:
      - A single location dict if only one result is found.
      - A list of options (dicts with index, label, and data) if multiple results.
      - (None, error message) if no results found.
    """
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=5"
    response = requests.get(geo_url)
    data = response.json()
    
    if "results" not in data or not data["results"]:
        return None, "Invalid city name. Please try again."
    elif len(data["results"]) > 1:
        options = []
        for idx, item in enumerate(data["results"], start=1):
            admin = item.get('admin1', '')
            location_str = f"{item['name']}, {admin}, {item['country']}".strip(', ')
            options.append({"index": idx, "label": location_str, "data": item})
        return options, None
    else:
        return data["results"][0], None

def fetch_weather(city_info):
    """
    Fetch the current weather for a given location using the Open-Meteo Weather API.
    """
    lat = city_info['latitude']
    lon = city_info['longitude']
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    response = requests.get(weather_url)
    weather_data = response.json()
    if "current_weather" not in weather_data:
        return None, "Weather data not available."
    return weather_data, None

def format_weather_report(city_info, weather_data):
    """
    Format the weather report as a neat markdown string.
    """
    current = weather_data["current_weather"]
    report = (
        f"### Weather Report for {city_info['name']}, {city_info.get('admin1', '')}, {city_info['country']}\n\n"
        f"**Temperature:** {current.get('temperature')}°C  \n"
        f"**Windspeed:** {current.get('windspeed')} km/h  \n"
        f"**Wind Direction:** {current.get('winddirection')}°  \n"
        f"**Time:** {current.get('time')}"
    )
    return report

def generate_goodbye_message():
    """
    Simulate an LLM-generated goodbye message.
    """
    prompt = (
        "Generate a friendly goodbye message for a weather bot conversation. "
        "It should thank the user for using the service and wish them a wonderful day."
    )
    # Simulated LLM output:
    return (
        "### Thank You!\n\n"
        "Thank you for using our weather bot. We hope you have a wonderful day ahead. Goodbye!"
    )

def reset_conversation():
    """
    Reset conversation by updating session state.
    """
    st.session_state.step = 1
    st.session_state.city_results = None
    st.session_state.selected_city = None
    st.session_state.check_another_clicks = 0  # reset the click counter

# ------------------------
# Streamlit App UI
# ------------------------

st.title("Weather Bot")

# Initialize session state variables if not already set.
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'city_results' not in st.session_state:
    st.session_state.city_results = None
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = None
if 'check_another_clicks' not in st.session_state:
    st.session_state.check_another_clicks = 0

# Step 1: Ask user to enter a city name.
if st.session_state.step == 1:
    st.write("Enter the name of the city you want the weather for:")
    city_input = st.text_input("City Name", key="city_input")
    if st.button("Submit City"):
        if city_input.strip() == "":
            st.error("Please enter a valid city name.")
        else:
            result, error = validate_city(city_input)
            if error:
                st.error(error)
            else:
                # If multiple options are found, proceed to step 2.
                if isinstance(result, list):
                    st.session_state.city_results = result
                    st.session_state.step = 2
                else:
                    st.session_state.selected_city = result
                    st.session_state.step = 3

# Step 2: If multiple locations are found, let the user select one.
if st.session_state.step == 2:
    st.write("Multiple locations found. Please select one:")
    options = st.session_state.city_results
    labels = [opt['label'] for opt in options]
    selected_index = st.radio("Select a location", options=range(len(labels)), format_func=lambda x: labels[x])
    if st.button("Confirm Selection"):
        st.session_state.selected_city = options[selected_index]['data']
        st.session_state.step = 3

# Step 3: Fetch and display weather data.
if st.session_state.step == 3:
    city_info = st.session_state.selected_city
    weather_data, error = fetch_weather(city_info)
    if error:
        st.error(error)
    else:
        report = format_weather_report(city_info, weather_data)
        st.markdown(report)
    
    # Provide two options: Check Another City or End Conversation.
    col1, col2 = st.columns(2)
    # Check Another City Button with double-click confirmation.
    if col1.button("Check Another City"):
        st.session_state.check_another_clicks += 1
        if st.session_state.check_another_clicks < 2:
            st.info("Please click 'Check Another City' again to confirm resetting the conversation.")
        else:
            reset_conversation()
    if col2.button("End Conversation"):
        goodbye_message = generate_goodbye_message()
        st.markdown(goodbye_message)
        st.session_state.step = 0
