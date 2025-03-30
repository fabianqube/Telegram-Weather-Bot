from typing import Final
import os
import telebot
import requests
import json
import logging, logging.config
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler

# Constants
USERNAME: Final = ''
TOKEN: Final = ''
WEATHER_TOKEN: Final = ''

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN', TOKEN)  # Use TOKEN directly if env var is missing
WEATHER_TOKEN = os.getenv('WEATHER_TOKEN', WEATHER_TOKEN)
USER_DATA_FILE = 'user_data.json'

# Initialize logging
config = {
    'disable_existing_loggers': False,
    'version': 1,
    'formatters': {
        'short': {
            'format': '%(asctime)s %(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'short',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    },
}
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# User state tracker
user_states = {}

def location_handler(message):
    '''
    Returns the latitude and longitude coordinates from user's message (location) using the Nominatim geocoder.
    If location is found - returns the rounded latitude and longitude
    else - returns None without sending a "Sorry" message.
    '''
    try:
        if isinstance(message, str):
            location = message
        else:
            location = message.text
            
        geolocator = Nominatim(user_agent="my_app")
        location_data = geolocator.geocode(location)
        
        if location_data is None:
            logger.error(f'Location not found: {location}')
            return None  # Return None without sending the "Sorry" message
        
        latitude = round(location_data.latitude, 2)
        longitude = round(location_data.longitude, 2)
        logger.info(f"Latitude '{latitude}' and Longitude '{longitude}' found for location '{location}'")
        return latitude, longitude
        
    except Exception as e:
        logger.error(f'Error finding location: {e}')
        return None

def get_weather(latitude, longitude):
    '''
    Fetches the weather data from OpenWeatherMap API for the specified latitude and longitude.
    '''
    url = f'https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={WEATHER_TOKEN}&units=metric'
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f'Weather API error: {e}')
        return None

def fetch_weather(message): 
    '''
    Fetches the weather information after a location is provided.
    '''
    try:
        location_result = location_handler(message)
        if location_result is None:
            return

        latitude, longitude = location_result
        weather = get_weather(latitude, longitude)
        if weather is None:
            bot.send_message(message.chat.id, 'Sorry, I could not retrieve the weather information.')
            return

        data = weather.get('list', [])
        if not data:
            bot.send_message(message.chat.id, 'No weather data available.')
            return

        info = data[0].get('weather', [])
        if not info:
            bot.send_message(message.chat.id, 'No weather description available.')
            return

        description = info[0].get('description', 'Unknown')
        temp = data[0].get('main', {}).get('temp', 'N/A')

        weather_message = f'*Weather:* {description.capitalize()}\n*Temperature:* {temp}°C'
        
        bot.send_message(message.chat.id, 'Here\'s the weather!')
        bot.send_message(message.chat.id, weather_message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f'Error in fetch_weather: {e}')
        bot.send_message(message.chat.id, 'Sorry, an unexpected error occurred.')

def load_user_data():
    """Load user data from the JSON file."""
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump({}, f)
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_user_data(data):
    """Save updated user data to the JSON file."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

def save_location(message):
    """Save location to user's data dictionary with retry logic."""
    try:
        location = message.text.strip()
        logger.info(f"Verifying location: {location}")
        
        # Verify location exists before saving
        location_result = location_handler(message)
        if location_result is None:
            logger.warning(f"Invalid location attempted: {location}")

            # Send a "try again" prompt with Yes/No buttons
            markup = InlineKeyboardMarkup()
            yes_button = InlineKeyboardButton("Yes", callback_data="try_again_yes")
            no_button = InlineKeyboardButton("No", callback_data="try_again_no")
            markup.add(yes_button, no_button)
            
            bot.send_message(message.chat.id, 
                             "This location could not be found. Would you like to try again?", 
                             reply_markup=markup)
            return
        
        # Load user data after location is verified
        user_data = load_user_data()
        user_id = str(message.chat.id)
        logger.info(f"Processing verified location '{location}' for user {user_id}")

        # Create new structure if user doesn't exist
        if user_id not in user_data:
            logger.info(f"Creating new user data for {user_id}")
            user_data[user_id] = {
                "locations": [],
                "preferences": {
                    "alert_frequency": "daily",
                    "temperature_unit": "celsius"
                },
                "alerts_enabled": True
            }
        elif not isinstance(user_data[user_id], dict):
            logger.warning(f"Invalid user data structure for {user_id}. Resetting...")
            user_data[user_id] = {
                "locations": [],
                "preferences": {
                    "alert_frequency": "daily",
                    "temperature_unit": "celsius"
                },
                "alerts_enabled": True
            }

        # Add location if not present
        if location not in user_data[user_id]["locations"]:
            user_data[user_id]["locations"].append(location)
            logger.info(f"Added location '{location}' for user {user_id}")
            
            # Save and confirm
            save_user_data(user_data)
            logger.info(f"Saved updated user data: {user_data}")
            
            locations_list = "\n".join(f"📍 {loc}" for loc in user_data[user_id]["locations"])
            bot.send_message(message.chat.id, f"Location verified and saved successfully!\nYour saved locations:\n{locations_list}")
        else:
            bot.send_message(message.chat.id, f"Location '{location}' is already in your saved locations.")
        
    except Exception as e:
        logger.error(f"Error saving location: {e}", exc_info=True)
        bot.send_message(message.chat.id, "Sorry, there was an error saving your location.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''
    Sends a welcome message with options to the user.
    '''
    markup = InlineKeyboardMarkup()
    yes_button = InlineKeyboardButton("Yes", callback_data="start_yes")
    no_button = InlineKeyboardButton("No", callback_data="start_no")
    markup.add(yes_button, no_button)

    bot.send_message(
        message.chat.id, 
        "Hi there! I'm your personal weather assistant, here to help you stay prepared for anything Mother Nature throws your way! Would you like to start using this bot?",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "start_yes")
def handle_start_yes(call):
    '''
    Handles the user's response to the welcome message.
    '''
    bot.send_message(call.message.chat.id, "Great! Let's get started. 😊")

    markup = InlineKeyboardMarkup()
    weather_button = InlineKeyboardButton("Get Weather", callback_data="get_weather")
    set_location_button = InlineKeyboardButton("Set Location", callback_data="set_location")
    alerts_button = InlineKeyboardButton("Weather Alerts", callback_data="weather_alerts")
    
    markup.add(weather_button, set_location_button)
    markup.add(alerts_button)

    bot.send_message(call.message.chat.id, "What would you like to do next?", reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "start_no")
def handle_start_no(call):
    '''
    Handles the user's response to not starting the bot.
    '''
    bot.send_message(call.message.chat.id, "Alright! If you change your mind, just type /start to begin. 😊")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "get_weather")
def handle_get_weather(call):
    '''
    Handles the user's request to get weather information.
    '''
    user_states[call.message.chat.id] = 'waiting_for_weather_location'
    bot.send_message(call.message.chat.id, "Please enter a location to get the weather:")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "set_location")
def handle_set_location(call):
    '''
    Handles the user's request to set a location.
    '''
    user_states[call.message.chat.id] = 'waiting_for_save_location'
    bot.send_message(call.message.chat.id, "Please enter the location you'd like to save for updates:")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "weather_alerts")
def handle_weather_alerts(call):
    '''
    Handles the user's request for weather alerts.
    '''
    bot.send_message(call.message.chat.id, "Weather alerts feature is under development!")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "try_again_yes")
def handle_try_again_yes(call):
    '''
    Allows the user to retry entering the location if it's invalid.
    '''
    user_states[call.message.chat.id] = 'waiting_for_save_location'
    bot.send_message(call.message.chat.id, "Please enter the location you'd like to save for updates:")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "try_again_no")
def handle_try_again_no(call):
    '''
    If the user chooses not to try again, we stop the process.
    '''
    bot.send_message(call.message.chat.id, "Okay, the location wasn't saved. If you'd like to try again, just type a location.")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    '''
    Central message handler that routes messages based on the user's current state
    '''
    current_state = user_states.get(message.chat.id)
    
    if current_state == 'waiting_for_weather_location':
        fetch_weather(message)
        user_states.pop(message.chat.id, None)  # Clear the state
    elif current_state == 'waiting_for_save_location':
        save_location(message)
        user_states.pop(message.chat.id, None)  # Clear the state
    else:
        # Handle unexpected messages or provide help
        bot.send_message(message.chat.id, "Please use the menu options. Type /start to see available commands.")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
