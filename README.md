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

## 📞 Contact

📧 Email: [contact.interviewgenius@gmail.com](mailto:contact.interviewgenius@gmail.com)
🌐 Website: [www.interviewgenius.com](http://www.interviewgenius.com)

---

Let me know if you'd like this in `.md` format or need help publishing it on GitHub!
