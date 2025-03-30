# Telegram Weather Bot

## Overview
This Telegram bot provides weather updates for a given location. Users can set and save locations, retrieve weather forecasts, and receive weather alerts. The bot integrates with the OpenWeatherMap API to fetch weather data.

## Features
- 🌤 Fetch current weather for any location
- 📍 Save locations for quick access
- 📡 Receive weather alerts (under development)
- 🔄 Interactive menu for easy navigation
- 📊 Uses OpenWeatherMap API

## Installation

### Prerequisites
- Python 3.7+
- A Telegram bot token (Get one from [BotFather](https://t.me/BotFather))
- OpenWeatherMap API key (Register [here](https://home.openweathermap.org/api_keys))

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-weather-bot.git
   cd telegram-weather-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file and add your credentials:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   WEATHER_TOKEN=your_openweathermap_api_key
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Usage
- Start the bot: `/start`
- Get weather: Select "Get Weather" from the menu
- Save location: Enter a location when prompted
- Retrieve saved locations: The bot will list them when needed

## Technologies Used
- `python-telegram-bot`
- `geopy` (for location handling)
- `requests` (for API calls)
- `apscheduler` (for scheduling tasks)
- `dotenv` (for environment variable management)
- `logging` (for debugging)

## Future Enhancements
- ⏰ Automated weather updates
- 🌦️ Advanced weather alerts
- 📊 Graphical weather reports

## License
This project is licensed under the MIT License.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

## Contact
- Author: Your Name
- Telegram: [@YourBotUsername](https://t.me/YourBotUsername)
- GitHub: [Your GitHub Profile](https://github.com/yourusername)

