# Collaboration Guide



### Main Branch (`main`)
- Production-ready code only
- Protected branch (no direct pushes)
- Only accepts merges from `dev` via Pull Requests

### Dev Branch (`dev`)
- Integration branch for all x - branches (***x is your name***)
- All feature branches merge here first
- Should be stable and tested before merging to `main`

## Initial Setup (First Time Only)

### 1. Set Up Python Virtual Environment

```bash
# Create a virtual environment 
python -m venv <venvname>

# Activate the virtual environment
venv\Scripts\activate

# Your terminal should now show (venv) 
```

### 2. Clone the Repository

```bash
git clone <repository-url>
# git clone https://github.com/Ritvent/Re-return.git    < - - - Clone this 

 
cd  Re-ret
# cd Re-return 
```



### 3. Install Django Dependencies

```bash
# Make sure you're in the project root directory with venv activated
# cd Re-return 
pip install -r requirements.txt

```


### 5. Verify Setup

```bash
# Run Django development server to test
# cd to 
python manage.py runserver
```

### 6. Set Up Git for Your Workflow

```bash
# Check current branch (should be main)
git branch

# Switch to dev branch
git checkout dev
git pull origin dev # you will pull the latest from dev remote

# Create your first <yourname - branch>
git checkout -b <yourname - branch>
# Example: 
# git checkout ross-branch
# git checkout kim-branch
```


## Workflow

### Development Routine

**Every time you start working:**

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Pull latest changes from remote dev everytime
git checkout dev
git pull origin dev 

# 3. Work on your feature branch
git checkout <yourname-branch>

# 4. If requirements.txt was updated, reinstall
pip install -r requirements.txt

# 5. Run migrations if models.py changed
python manage.py migrate
```

### 2. Working on Your Branch

```bash
# Make your changes to our project

# If you modified models, create migrations
python manage.py makemigrations

# Run migrations locally to test
python manage.py migrate

# Test your changes
python manage.py runserver

# Once satisfied, stage your changes
git add .

# Commit with clear, descriptive messages
git commit -m "commit message"

# Push your branch to remote yourname-branch
git push origin yourname-branch
```

**Important**
- Update requirements.txt if you install new packages:
  ```bash
  pip freeze > requirements.txt
  git add requirements.txt
  git commit -m "Add new dependency package"
  ```

### 3. Keeping Your Branch Updated

```bash 
# Regularly sync with dev to avoid conflicts
git checkout dev
git pull origin dev
git checkout yourname-branch
git merge dev

# Resolve any conflicts, then push
git push origin yourname-branch
```

### 4. Creating Pull Requests

1. Push your yourname-branch to GitHub
2. Go to the repository on GitHub
3. Click "Pull Request" → "New Pull Request"
4. Set base branch to `dev` (not `main`!)
5. Add a descriptive title and description:



