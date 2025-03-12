# Smart Home Energy Monitoring System

This project is a real-time energy monitoring system that tracks power consumption from connected devices, processes the data, and stores it for historical analysis. It runs on a **Mosquitto MQTT broker** and records energy usage from **Shelly Plug S** devices. The system is currently designed for a **single user** but will be expanded in the future. Plans include moving the database to the cloud and adding a web interface.

## Features
- Real-time power consumption tracking via MQTT  
- Data aggregation at minutely, hourly, daily, and weekly intervals  
- Historical data storage for long-term analysis  
- Automatic device detection and onboarding  
- Database management using MySQL and SQLAlchemy  

## Why I Built This
I wanted to build something practical that could help users reduce their electricity costs. Smart energy monitoring isn’t very common, and I saw an opportunity to apply multiple concepts from IoT, databases, real-time data processing, and system architecture. Right now, I have the system connected to my lamp, which logs power consumption over time. I plan to add two more devices soon.

## Project Structure
```
smart-home-energy-monitoring/
├── README.md
└── src/
    ├── main.py             # Entry point
    ├── mqtt_client.py      # Handles MQTT communication
    ├── data_processor.py   # Processes and schedules data storage
    ├── db_manager.py       # Manages database interactions
    ├── models.py           # Defines database schema (SQLAlchemy)
```

## Installation

### Clone the Repository
```bash
git clone https://github.com/yohad50050/smart-home-energy-monitoring.git
cd smart-home-energy-monitoring
```

### Install Dependencies (Python 3.8+)
```bash
pip install -r requirements.txt
```

### Set Up the Database
Modify `models.py` to match your MySQL credentials and create the database schema:
```bash
python -c "from models import Base, engine; Base.metadata.create_all(engine)"
```

### Run the System
```bash
python main.py
```

## How It Works
- `mqtt_client.py`: Connects to an MQTT broker and listens for device power updates.  
- `db_manager.py`: Handles database read/write operations and data aggregation.  
- `data_processor.py`: Stores real-time power readings and processes historical logs.  
- `models.py`: Defines the database structure for devices and consumption records.  
- `main.py`: Starts the MQTT client and manages the data pipeline.  

## Roadmap
### Completed
- Real-time power tracking
- Consumption data stored and retrieved via an API
- Aggregation of hourly, daily, and weekly usage statistics

### Next Steps
- Adding two additional devices for further testing
- Building a basic web interface for visualization

### Future Plans
- Assigning devices to specific rooms and allowing consumption comparison
- Implementing alerts for abnormal power usage
- Moving the database to the cloud for remote access
- Optimizing the web interface for mobile devices
- Optional: The user can define the device type (TV, computer, refrigerator, etc.). The system will then provide consumption insights based on the device type, categorizing it as either energy-efficient or high-consumption.
- After several hours of continuous high power consumption, the system will prompt the user to confirm whether they want to turn off the plug.
- The system will ask the user for their location. Based on this, it will display relevant notifications.

## About
I'm a second-year Software Engineering student, and this is a personal project built for **self-learning**. It’s not part of my studies, but an independent effort to apply what I’ve learned in IoT, backend development, and database management. The project is a work in progress, and I continue to improve it over time.

**GitHub:** [yohad50050](https://github.com/yohad50050)  
**LinkedIn:** [Yohad BB](https://www.linkedin.com/in/yohad-bb-969776252/)


Feedback and contributions are welcome!  
