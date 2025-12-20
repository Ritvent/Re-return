# HanApp: Find What You Lost  

**HanApp** is a comprehensive **Lost & Found Management System** designed exclusively for **Palawan State University (PalSU)**. It connects students, faculty, and staffs through a secure, moderated platform that helps lost items find their way back to their rightful owners, faster and safer.

---

## ✨ Why HanApp?


🔐 **Verified & Secure** - Access limited to authenticated PalSU accounts  
💬 **Direct Messaging** - In-app communication between finders and owners  
🛡️ **Moderated Content** - Admin review prevents spam and misuse  
📧 **Smart Notifications** - Email alerts for approvals, updates, and messages

---

## 🚀 Features

### Core Features

| Feature                 | Description                                                       |
| ----------------------- | ----------------------------------------------------------------- |
|  **Item Posting**     | Post lost or found items with descriptions, images, and locations |
|  **Item Browsing**    | Search and filter items by category, date, and status             |
|  **Messaging System** | Thread-based messaging with optional image attachments            |
|  **Claim System**      | Mark items as claimed or found with completion tracking           |
|  **Success Stories**  | View successfully reunited items                                  |
|  **Archive System**  | Archive items with reasons (spam, duplicate, resolved, etc.)      |

---

### 🛠️ Admin Features

*  **Dashboard Analytics** — Insights on items, users, and claims
*  **Moderation Queue** — Review and approve pending posts
*  **User Management** — Assign roles and manage permissions
*  **Archive Management** — Restore or permanently remove archived items
*  **Item Control** — Edit, delist, or delete any item

---

## 🧱 Tech Stack

### Backend

* **Python** 3.11+
* **Django** 5.2.8
* **Django REST Framework** 3.15.2
* **django-allauth** 65.3.0 (Authentication & OAuth)
* **Pillow** 12.0.0 (Image processing)

### Frontend

* **Tailwind CSS** — Utility-first styling

### Database

* **SQLite** — Development
* **PostgreSQL** — Production

---

## 👥 User Roles & Permissions

HanApp follows a **three-tier access model** to ensure security and proper moderation.

### 🌐 Public Users (Non-authenticated)

| Permission            | Access |
| --------------------- | ------ |
| View landing page     | ✅      |
| Browse approved items | ✅      |
| View item details     | ✅      |
| View success stories  | ✅      |
| Post items            | ❌      |
| Send messages         | ❌      |
| Access dashboard      | ❌      |

---

### ✅ Verified PalSU Users

| Permission               | Access |
| ------------------------ | ------ |
| All public permissions   | ✅      |
| Post lost/found items    | ✅      |
| Send & receive messages  | ✅      |
| Edit/delete own items    | ✅      |
| Mark items as complete   | ✅      |
| View own message threads | ✅      |

---

### 👑 Admin Users

| Permission                    | Access |
| ----------------------------- | ------ |
| All verified user permissions | ✅      |
| Skip moderation approval      | ✅      |
| Access admin dashboard        | ✅      |
| Approve/reject items          | ✅      |
| Archive & restore items       | ✅      |
| Manage user roles             | ✅      |
| View system analytics         | ✅      |

---

## ⚙️ Installation

### 1️. Clone the Repository

```bash
git clone https://github.com/Ritvent/Re-return.git
cd Re-return
```

### 2️. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3️. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️. Environment Setup

Create a `.env` file inside the `projectsite` directory:

```env
SECRET_KEY=your-super-secret-key
DEBUG=True

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

### 5️. Apply Migrations

```bash
cd projectsite
python manage.py migrate
```

### 6️. Create Superuser

```bash
python manage.py createsuperuser
```

### 7️. Run Development Server

```bash
python manage.py runserver
```

---

## 🔐 Configuration

### Google OAuth Setup

Authentication is restricted to **@psu.palawan.edu.ph** accounts.

1. Open **Google Cloud Console**
2. Create or select a project
3. Enable Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add redirect URIs:

   * `http://127.0.0.1:8000/accounts/google/login/callback/`
   * `https://yourdomain.com/accounts/google/login/callback/`

---

### 📧 Email Notifications  
*Configure SMTP settings for email notifications:*

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

---

## 📖 Usage Guide

### Public Users

* Browse approved lost & found items
* Search and filter listings
* View success stories

### Verified PalSU Users

* Post lost or found items
* Message item owners or finders
* Mark items as claimed or found

### Admin Users

* Moderate submissions
* Manage users and roles
* View analytics and archives

---

## 🤝 How to Contribute?

1. Fork the repository
2. Create a feature branch
3. Commit with clear messages
4. Push to your fork
5. Open a Pull Request

---

## 📜 License

Developed as an academic project for **Palawan State University**. All rights reserved.  

Developed by: **Lumora**