# Task Scheduler API

An API for scheduling and managing tasks with status tracking and smart prioritization.

---

## 🔧 Features

- ✅ Add new tasks
- 🔍 Retrieve tasks by ID
- 🔄 Update task status (with validation & transition control)
- ⏱️ Get next task to process based on estimated time and submission time
- 📋 List pending tasks with sorting and limit
- 🛡️ Status transition protection

---

## 🛠 Tech Stack

- Python 3.11
- FastAPI
- SQLite (via SQLAlchemy)

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/task-scheduler-api.git
cd task-scheduler-api
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
uvicorn main:app --reload
```
