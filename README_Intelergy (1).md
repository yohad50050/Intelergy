# 🔌 Intelergy – Smart Home Energy Monitoring System

**Intelergy** is a smart home energy monitoring system designed to track and analyze the power consumption of individual devices in real time.  
The project provides a full data pipeline: from live device polling to structured storage and automated data aggregation.  

> This is a personal project by a software engineering student, focused on applying backend development, database design, and real-world IoT integration.

---

## ⚙️ Features

- Real-time power consumption logging from **Shelly Plug S** devices (Gen 1 & Gen 2 APIs)
- Hierarchical structure: **Users → Profiles → Rooms → Devices**
- Automatic device registration with connectivity validation
- Historical data aggregation: **minutely → hourly → daily → weekly**
- Built with **Python + SQLAlchemy + MySQL**
- Full CLI interface for device and profile setup

---

## 📂 Project Structure

```
intelergy/
├── data_collector.py     # Entry point: collects power data from devices
├── data_proccessor.py    # Aggregates data (hourly, daily, weekly)
├── models.py             # SQLAlchemy schema definitions and DB setup
```

---

## 🛠 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your_username/intelergy.git
cd intelergy
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Set Up MySQL Database
Edit the connection string in `models.py` to match your MySQL credentials:
```python
engine = create_engine("mysql+mysqlconnector://user:password@localhost/Intelergy")
```

Then, create the schema:
```bash
python -c "from models import Base, engine; Base.metadata.create_all(engine)"
```

---

## 🚀 How It Works

### Step 1: Setup (One-Time)
Run the system and follow the CLI menu:
- Add a user, profile, room, and register each device by URL
- Connectivity is verified before adding the device

### Step 2: Real-Time Data Collection  
`data_collector.py` runs in a simple loop that:
- Every minute, fetches current power from each active device
- Saves a log entry into the database (minutely resolution)

> 💡 There’s also a version of the project designed to run as a background service rather than a timed loop, using API calls — but in practice, this turned out to be less convenient to develop and manage. The current loop-based version was chosen for its simplicity and reliability.

### Step 3: Data Aggregation  
Every time new data is added, `data_proccessor.py`:
- Aggregates 60-minute chunks into **hourly** entries  
- Aggregates 24 hours into **daily** entries  
- Aggregates 7 days into **weekly** entries

---

## 📊 Roadmap

### ✅ Completed
- Real-time power data collection from Shelly Plug S devices
- Full aggregation pipeline to hourly, daily, and weekly entries
- Structured schema: user, profile, room, device
- CLI-based setup and management

### 🔜 In Progress
- Adding multiple devices to test scaling and behavior
- Preparing for web interface (React + Flask backend)
- Refactoring aggregation structure (removing unnecessary many-to-many)

### 🧭 Future Plans
- Web dashboard with graphs and comparisons by profile, room, and device  
- Abnormal usage detection and real-time alerts  
- Device categorization (TV, AC, etc.) with tailored insights  
- Mobile-optimized web interface  
- Cloud database migration and multi-user support  
- **User presence detection** – if the user is outside, the system will suggest turning off specific devices  
- **Smart usage feedback** – notify the user if a device (e.g., TV or AC) has been running unusually long or is consuming excessive power  
- **Cost estimation engine** – calculate and display how much money was spent or saved per device  
- **Microservices architecture** – allow different components (data collection, processing, alerts) to run concurrently as microservices

---

## 👨‍💻 About

I’m a second-year software engineering student. This project started as a personal experiment to combine backend engineering, IoT, and real-world problem solving.