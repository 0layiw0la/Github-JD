from flask import render_template,request,redirect,url_for,flash,session,jsonify
from sqlalchemy.exc import IntegrityError
from models import User, Projects
from functions.Scraping import ScrapeProjects
from functions.prompt import compare_jd,load_data,get_descriptions,generate_bullets
from functions.upload import allowed_file,process_pdf,process_text,UPLOAD_FOLDER
import requests
import pandas as pd 
import os
import json




def register_routes(app,db):

    """Handles user signup, allowing a maximum of 15 users to register. """
    @app.route('/signup', methods=['GET','POST'])
    def signup():
        if request.method == 'GET':
            return render_template('signupform.html')
        
        elif request.method == 'POST':
            name = request.form.get('name')
            password = request.form.get('password')

            user_count = User.query.count()  #Getting the number of stored users
            if user_count >=15: #if users greater than 15 tell them not allowed and an enless loop of reloading signup
                flash("User limit reached! No more signups allowed.", "error")
                return redirect(url_for('signup'))
            
            try: #Adding the user to the db if the maximum number hasnt been reached
                user = User(username=name, password_hash=password)
                db.session.add(user)
                db.session.commit()
                
            except IntegrityError:
                db.session.rollback()  # Rollback the transaction to prevent a corrupted session
                flash("Username already exists. Please choose another one.", "error")

            return redirect(url_for('login'))  # Redirect to avoid form resubmission


    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'GET':
            return render_template('loginform.html')
        elif request.method == 'POST':
            name = request.form.get('name')
            password = request.form.get('password')

            # Check if user exists in the database
            user = User.query.filter_by(username=name, password_hash=password).first()

            if user:
                session['username'] = user.username  # Store username in session
                flash('Login successful!', 'success')
                return redirect(url_for('index'))  
            else:
                flash('Invalid username or password. Please try again.', 'error')
                return redirect(url_for('login'))  # Redirect back to login



    @app.route('/')
    def index():
        username = session.get('username')  # Retrieve username from session
        if not username:
            return redirect(url_for('signup'))  # Redirect to signup if not logged in


        return render_template('index.html', welcome=username)  
    



    """ Allows users to add projects from GitHub by scraping data. """
    @app.route('/add', methods=['GET', 'POST'])
    def add():
        if request.method == 'GET':
            users = User.query.all()
            return render_template('add.html', users=users)

        elif request.method == 'POST':
            username = request.form.get('username', '').strip()

            if not username:
                flash("GitHub username cannot be empty!", "danger")
                return redirect(url_for('add'))

            try:
                projects = ScrapeProjects(username)

                if not projects:
                    flash(f"No projects found for '{username}' or invalid username!", "warning")
                    return redirect(url_for('add'))

                new_added = False  # Track if any new projects were added

                for project in projects:
                    exists = Projects.query.filter_by(username=project["username"], projectname=project["projectname"]).first()
                    if not exists:
                        new_project = Projects(
                            username=project["username"],
                            projectname=project["projectname"],
                            description=project["description"],
                            bulletpoints=None
                        )
                        db.session.add(new_project)
                        new_added = True

                if new_added:
                    db.session.commit()
                    flash(f"Successfully scraped and added new projects for {username}!", "success")

                return redirect(url_for('index'))  # Redirect to index on success

            except requests.exceptions.RequestException:  
                flash("Network error occurred while scraping. Please try again!", "danger")

            except Exception as e:
                db.session.rollback()
                print(f"Unexpected error: {e}")  #Log error but don't flash user

            return redirect(url_for('add'))  # Stay on `/add` if an error occurs


        
    @app.route('/compare', methods=['GET','POST'])
    def compare():

        """ 
        Compares job descriptions against stored project data and returns relevant projects.
        Users can upload a job description file or enter text manually.
        """

        # Check if a job description file was uploaded
        if request.method == 'GET':
            return render_template('compare.html')
        jd_text = ""
        if 'jd_file' in request.files:
            file = request.files['jd_file']
            if file and allowed_file(file.filename):
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                jd_text = process_pdf(file_path)

        # If no file was provided, try extracting text from form input
        if not jd_text:
            jd_text = process_text(request.form.get('jd_text', ''))

        # Ensure a job description was provided
        if not jd_text:
            flash("Please provide a job description.", "warning")
            return redirect(url_for('compare'))

        projects = load_data() # Load stored project data
        
        # If no projects are found in the database
        if not projects:
            flash("No projects found.", "info")
            return redirect(url_for('compare'))

         # Compare job description with stored projects
        top_projects = compare_jd(jd_text, projects)
        
        return render_template('compare_results.html', projects=top_projects)
    

    @app.route("/bullet", methods=["POST"])
    def bullet():

        """ 
        Generates bullet points for project descriptions based on user input.
        Users select projects and provide additional input to refine bullet points.
        """
         
        project_names = []
        user_inputs = {}

        # Extract project names and user inputs dynamically
        for key, value in request.form.items():
            if key.startswith("project_name_"):
                index = key.split("_")[-1]
                project_names.append(value.strip())  # Ensure clean project names
            elif key.startswith("project_info_"):
                index = key.split("_")[-1]
                user_inputs[index] = value.strip()  # Strip user input to remove unnecessary spaces

        if not project_names:
            flash("No projects selected.", "error")
            return redirect(url_for("compare"))

        # Fetch and clean descriptions
        descriptions = get_descriptions(project_names)

        # Merge descriptions with user input
        combined_inputs = {
            name: f"{descriptions.get(name, '').strip()} {user_inputs.get(str(i + 1), '').strip()}".strip()
            for i, name in enumerate(project_names)
        }

        # Call function to generate bullets
        bullet_results = generate_bullets(combined_inputs)

        for project_name, bullets in bullet_results.items():
            project = Projects.query.filter_by(
                username=session.get("username"),  # Ensure correct user
                projectname=project_name
            ).first()

            if project:
                project.bulletpoints = json.dumps(bullets)
                #project.bulletpoints = "<br/><br/>".join(bullets)  # Store bullets as newline-separated text

        try:
            db.session.commit()
            flash("Bullet points successfully saved!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error saving bullet points to database.", "error")
            print(f"Database error: {e}")

        return render_template("bullet_results.html", bullets=bullet_results)



    
    @app.route('/view', methods=['GET'])
    def view():

        """ 
        Displays all stored projects for the logged-in user in a table format.
        The table includes project names, descriptions, and generated bullet points.
        """

        username = session.get('username') 
        if not username:
            flash("You must be logged in to view projects!", "warning")
            return redirect(url_for('login'))  

        # Fetch all projects for the user in a single query
        user_projects = db.session.query(Projects.projectname, Projects.description,Projects.bulletpoints).filter_by(username=username).all()
        print(user_projects)
        if not user_projects:
            flash("No projects found.", "info")
            return render_template('view.html', table=None)
        formatted_projects = []

        for name, desc, bullets in user_projects:
            formatted_projects.append({
                "name": name,
                "description": desc or "No description provided",
                "bullets": json.loads(bullets) if bullets is not None else None   # expect list of strings for bullets
            })

        
        return render_template('view.html', projects=formatted_projects)

    @app.route('/delete', methods=['GET', 'POST'])
    def delete_user():
        if request.method == 'GET':
            return render_template('delete.html')

        elif request.method == 'POST':
            username = request.form.get('username')

            # Query for the user
            user = User.query.filter_by(username=username).first()

            if user:
                db.session.delete(user)
                db.session.commit()
                print(f"User '{username}' deleted successfully.", "success")
                return redirect(url_for('signup'))  # Redirect to signup after deletion
            else:
                flash("User not found!", "error")
                return redirect(url_for('delete_user'))  # Stay on delete page if user not found

    """ 
        Placeholder for a tracking feature. Intended for future implementation
        of project tracking functionality.
    """
    

    @app.route('/edit_project')
    def edit_project():
        project_name = request.args.get('name')
        username = session["username"]
        bullets = db.session.query(Projects.bulletpoints).filter(Projects.username == username, Projects.projectname == project_name).first()
        print(bullets)
        return f"{project_name} — {bullets.bulletpoints if bullets else 'No bullets found'}"


    @app.route('/add_bullet')
    def add_bullet():
        project_name = request.args.get('name')
        username = session["username"]
        bullets = db.session.query(Projects.bulletpoints).filter(Projects.username == username, Projects.projectname == project_name).first()
        return (project_name,bullets)
