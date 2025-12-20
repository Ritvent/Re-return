#  HanApp 
A comprehensive Lost & Found management system designed specifically for **Palawan State University**. The platform connects students, faculty, and staff to help reunite lost items with their rightful owners.

### Why HanApp?

- **Transparent & Verified** - All users authenticated with PalSU credentials
-  **Direct Messaging** - In-app communication between finders and owners
-  **Moderation System** - Admin oversight to prevent spam and ensure quality
-  **Email Notifications** - Automated alerts for item approvals, status updates, and new messages 

---

##  Features

### Core Features

| Feature | Description |
|---------|-------------|
|  **Item Posting** | Post lost or found items with detailed descriptions, images, and location |
|  **Item Browsing** | Search and filter items by category, date, and status |
|  **Messaging System** | Thread-based messaging with image attachments |
|  **Claim System** | Mark items as claimed/found with completion tracking |
|  **Success Stories** | View reunited items filtered by claimed or found status |
|  **Archive System** | Archive items with reasons (spam, duplicate, resolved, etc.) |


### Admin Features

- **Dashboard Analytics** - Statistics on items, users, and claims
- **Moderation Queue** - Review pending items before approval
-  **User Management** - Manage user roles and permissions
- **Archive Management** - View and restore archived items
- **Item Editing** - Delete/Delist any item

---

##  Tech Stack

- **Python** (3.11+) 
- **Django** (5.2.8) 
- **Django REST Framework** (3.15.2)
- **django-allauth** (65.3.0) - Authentication & OAuth
- **Pillow** (12.0.0) - Image processing

- **Tailwind CSS** - Utility-first CSS framework
- **SQLite** - Development database
- **PostgreSQL** - Production database 
---

## User Roles & Permissions

HanApp implements a three-tier role system to manage access and permissions:

### 🌐 Public Users (Non-authenticated)

| Permission | Access |
|------------|--------|
| View landing page | ✅ |
| Browse approved items | ✅ |
| View item details | ✅ |
| View success stories | ✅ |
| Post items | ❌ |
| Send messages | ❌ |
| Access dashboard | ❌ |

### ✅ Verified PalSU Users

| Permission | Access |
|------------|--------|
| All public permissions | ✅ |
| Post lost/found items | ✅ |
| Send/receive messages | ✅ |
| Mark own items as complete | ✅ |
| Edit own items | ✅ |
| Delete own items | ✅ |
| View own message threads | ✅ |


### 👑 Admin Users

| Permission | Access |
|------------|--------|
| All verified user permissions | ✅ |
| Post items without approval | ✅ |
| Access admin dashboard | ✅ |
| View moderation queue | ✅ |
| Approve/reject items | ✅ |
| Archive items with reasons | ✅ |
| Delete any archived item | ✅ |
| Restore archived items | ✅ |
| Manage user roles | ✅ |
| View all statistics | ✅ |


---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ritvent/Re-return.git
cd Re-return
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Environment Setup

Create a `.env` file in the `projectsite` directory:

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True

# Google OAuth (Required for authentication)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email Configuration (Optional - for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
```

### Step 5: Migrate

```bash
cd projectsite
python manage.py migrate
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
```


### Step 7: Run Development Server

```bash
python manage.py runserver
```



---

##  Configuration

### Google OAuth Setup

HanApp uses Google OAuth for authentication, restricted to PalSU email addresses (`@psu.palawan.edu.ph`).

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/accounts/google/login/callback/` (development)
   - `https://yourdomain.com/accounts/google/login/callback/` (production)

- - -
### Email Notifications

Configure SMTP settings for email notifications:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```



##  Usage Guide

### For Public Users

1. **Browse Items** - Visit the homepage to see all approved lost and found items
2. **Search & Filter** - Use the search bar and category filters to find specific items
3. **View Details** - Click on any item card to see full details
4. **Success Stories** - Visit the "Success Stories" page to see reunited items

### For Verified PalSU Users

#### Posting an Item

1. Click "Post an Item" in the navigation
2. Select item type (Lost or Found)
3. Fill in item details:
   - **Title** - Brief, descriptive title
   - **Category** - Select from the list of categories
   - **Description** - Detailed description of the item
   - **Location** - Where the item was lost/found
   - **Date** - When it was lost/found
   - **Contact Number** - Your phone number (optional)
   - **Image** - Upload an image (optional but recommended)
   - **Hide name** - Option to post anonymously without showing your name (Lost items only)
4. Submit for moderation review

#### Messaging

1. Click "Contact" on any item 
2. Fill in the subject and message
3. Optionally attach an image
4. Send the message
5. View replies in "Inbox" or "Sent Messages"

#### Completing an Item

1. Navigate to "Lost Items" or "Found Items"
2. Find your posted item
3. Click "Mark as Complete"
4. Select completion status:
   - **Claimed** - Owner found and claimed the item
   - **Found** - Item was found by the owner
5. Add optional notes and submit

### For Admin Users

#### Admin Dashboard

Access via the admin icon in the navigation bar:

- **Statistics** - Total items, pending items, users, claimed/found items
- **Recent Activity** - Latest posted items
- **Quick Actions** - Navigate to moderation, users, or archives

#### Moderation Queue

1. Go to Admin Dashboard → Moderation
2. Review pending items
3. For each item, choose:
   - ✅ **Approve** - Make item visible to all users
   - ❌ **Reject** - Hide item with optional reason
   - 🗑️ **Archive** - Archive with reason

#### User Management

1. Go to Admin Dashboard → Users
2. View all registered users
3. Change user roles
4. View user statistics

#### Archive Management

1. Go to Admin Dashboard → Archives
2. View all archived items
3. Filter by archive reason
4. Restore items if needed

---

## Contributing


### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Commit with clear messages: `git commit -m "Add: description of changes"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a Pull Request


##  License

This project was developed as an academic project for Palawan State University. All rights reserved.