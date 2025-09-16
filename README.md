## Github-JD
A tool that generates resumes from your existing GitHub projects. Compare job descriptions to filter relevant projects and automatically build a resume or handpick the projects yourself. Acts as a personal database for storing projects and bullet points, which you can generate with AI or write manually. It makes resume updates easier and keeps track of your work, perfect for casting a wide net on entry-level roles.
---
Visit the site [here](https://github-jd.onrender.com)
### Features

* Add Projects: Scrape or manually add your GitHub projects.
* Generate Resume:
    * Manual: Handpick which projects appear.
    * AI‑powered: Automatically assemble bullet points and select projects.
* Export: Download your tailored resume as a .docx file.
---

### Built With

- Flask
- TailwindCSS
- PostgreSQL (or SQLite for local development)
- Gemini API
- Beautiful Soup
- Pandas

---

### Getting Started

#### Prerequisites

- Python 3.8+
- Virtualenv or Conda (recommended)
- Git

#### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/0layiw0la/Github-JD.git
   cd Github-JD
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate    # on Linux/Mac
   venv\\Scripts\\activate   # on Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get your Gemini API key**
   - Sign in to your Google Cloud Console: https://console.cloud.google.com/
   - Navigate to **APIs & Services** > **Credentials**.
   - Click **Create credentials** > **API key**.
   - Copy the generated key.

5. **Create a `.env` file in the project root**
   ```dotenv
   # .env
   SQL_DATABASE_URL=sqlite:///./projects_points.db    # or your PostgreSQL URL
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

6. **Database Setup**

Since each developer uses their own local database, use Flask-Migrate to initialize and apply migrations in one flow:
```bash
# Remove existing migrations folder (if any)
rm -rf migrations/

# Initialize migration repository
flask db init

# Generate initial migration
flask db migrate -m "Initial migration"

# Apply migrations and create the database
flask db upgrade
```

7. **Run the application**
   ```bash
   python main.py   # or python app.py depending on your entrypoint
   ```

---

