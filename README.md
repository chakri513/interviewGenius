# 💼 AI-Powered Mock Interview Preparation System

## 🔍 Overview

This project is an AI-powered mock interview platform designed to help job seekers practice real-world interview scenarios. It uses NLP, ML, and the Google Gemini Pro API to dynamically generate questions, evaluate candidate responses (text and voice), and provide personalized, real-time feedback.

It offers:

* Role-specific question generation
* AI evaluation on technical, behavioral, and communication aspects
* Secure user authentication and performance analytics
* Quiz and interview modules
* Edge computing for reduced latency

---

## 📌 Features

* 🔐 **Secure Authentication**: Email + OTP-based 2FA
* 🧠 **AI-Driven Interview Questions**: Based on job role and user progress
* 🗣 **Speech & Text Support**: Accepts both typed and audio responses
* 📊 **Instant Feedback**: Real-time evaluation on clarity, confidence, and correctness
* 📈 **Performance Dashboard**: Tracks interview history, feedback, and improvement areas
* 📝 **Quiz Module**: Create, attempt, and score quizzes
* 📧 **Email Notifications**: Interview/quiz updates via email

---

## 🧱 Tech Stack

| Layer              | Technologies                       |
| ------------------ | ---------------------------------- |
| **Frontend**       | HTML, CSS, JavaScript              |
| **Backend**        | Python, FastAPI                    |
| **Database**       | PostgreSQL                         |
| **AI/NLP**         | Google Gemini Pro API, spaCy, NLTK |
| **Speech-to-Text** | Google APIs                        |
| **Auth**           | OAuth2.0, JWT, TLS/SSL             |

---

## ⚙️ System Requirements

### Software

* Python 3.9+
* FastAPI, Uvicorn, SQLAlchemy, Pydantic
* PostgreSQL
* Google Gemini Pro API access
* VS Code / PyCharm

### Hardware

* 8GB RAM minimum (Client)
* Cloud server or edge node with 4-core CPU & optional GPU
* Internet for API and cloud sync

---

## 🧪 Testing Types

* ✅ **Unit Testing**: FastAPI endpoints and AI logic
* 🔗 **Integration Testing**: Frontend ↔ Backend ↔ Database
* 🔐 **Security Testing**: Auth, session handling, data access
* 🚀 **Performance Testing**: Real-time AI feedback under load
* 👥 **User Acceptance Testing (UAT)**: Validated by real users

---

## 🔄 Flowchart Summary

1. User Logs In
2. Selects option: Quiz or Interview
3. Based on input:

   * Quiz: Create/Attempt → Submit → Get Score
   * Interview: Schedule → Answer → AI Evaluates → Feedback
4. Email Notification Sent
5. User Logs Out

*(Refer to flow\.png for visual representation)*

---

## 📂 Project Structure

```
├── main.py                 # FastAPI main app
├── /src
│   ├── /routers            # API endpoints (auth, quiz, interview)
│   ├── /services           # Auth service, token decoding
│   ├── /templates          # HTML templates
│   ├── /db
│       ├── db.py           # DB connection
│       ├── models.py       # SQLAlchemy models
├── /uploads                # Uploaded files
├── /static                 # Static files (CSS, JS)
```

---

## ▶️ Running the Project

### 1. Clone the repo

```bash
git clone https://github.com/your-repo/interview-genius.git
cd interview-genius
```

### 2. Set up environment

```bash
pip install -r requirements.txt
```

### 3. Run the backend

```bash
uvicorn main:app --reload --port 8000
```

### 4. Open in browser

```bash
http://127.0.0.1:8000
```

---

## 🛡 Security

* Role-Based Access Control (RBAC)
* JWT-based session management
* TLS/SSL encryption
* AI-anomaly detection for feedback manipulation

---

## 🚀 Future Improvements

* 🎥 Video Interview Integration
* 🧩 Gamification with Leaderboards
* 🌍 Multilingual Support
* 🤖 Enhanced AI Training via Federated Learning

---
## 📽️ Demo Video

https://github.com/user-attachments/assets/4c2c5b49-3c29-414e-aa3d-323b3dc67229


## OUTPUTS

![image](https://github.com/user-attachments/assets/dc726eed-c0a5-4f50-a3a3-1ed90fc3bd85)
![image](https://github.com/user-attachments/assets/224d4719-a9f5-49d1-a92a-676dd66eedb9)
![image](https://github.com/user-attachments/assets/a1e3dff5-ee72-4e20-86ce-27fc50c8cabb)
![image](https://github.com/user-attachments/assets/5a291860-715c-4d75-878a-e45813c200c7)
![image](https://github.com/user-attachments/assets/a827f541-401d-434c-8dac-2b880b9fc45c)
![image](https://github.com/user-attachments/assets/781ac5b1-443d-48d1-a4ab-faf9250199a5)
![image](https://github.com/user-attachments/assets/1329b4b5-0903-4380-b10f-7db9def4ebf8)
![image](https://github.com/user-attachments/assets/670c43f3-046c-4229-bcb6-eb4824d01814)
![image](https://github.com/user-attachments/assets/cadec0cb-4134-4dce-b6ba-1ddcabe8af8c)
![image](https://github.com/user-attachments/assets/c198686c-31cb-4599-b20e-b0a9201ae3da)
![image](https://github.com/user-attachments/assets/055b0682-a046-40e2-bc3a-072cef54adfd)



---

