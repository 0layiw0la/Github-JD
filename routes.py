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
    


    @app.route('/details', methods=['GET', 'POST'])
    def details():
        if not session.get('username'):
            flash('Please login first', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=session['username']).first()

        if request.method == 'GET':
            # Pre-populate form if user data exists
            if user:
                try:
                    extracurriculars = json.loads(user.extracurriculars) if user.extracurriculars else {
                        'activities': [],
                        'descriptions': []
                    }
                    return render_template('details.html',
                        fullname=user.fullname,
                        email=user.email,
                        linkedin=user.linkedin,
                        github=user.github,
                        school_name=user.school_name,
                        course=user.course,
                        duration=user.duration,
                        programming_languages=user.programming_languages,
                        libraries=user.libraries,
                        tools=user.tools,
                        extracurricular_activities=extracurriculars.get('activities', []),
                        extracurriculars_about=extracurriculars.get('descriptions', [])
                    )
                except json.JSONDecodeError:
                    # Handle corrupt JSON data
                    print("Warning: Corrupt extracurriculars JSON data")
                    return render_template('details.html')
            return render_template('details.html')

        elif request.method == 'POST':
            # Get form data for other fields
            fullname = request.form.get('fullname')
            email = request.form.get('email')
            linkedin = request.form.get('linkedin')
            github = request.form.get('github')
            school_name = request.form.get('school_name')
            course = request.form.get('course')
            duration = request.form.get('duration')
            programming_languages = request.form.get('programming_languages')
            libraries = request.form.get('libraries')
            tools = request.form.get('tools')

            # Handle extracurricular activities with improved validation
            activities = []
            descriptions = []
            
            for i in range(4):
                activity = request.form.get(f'extracurricular_activities[{i}]', '').strip()
                description = request.form.get(f'extracurriculars_about[{i}]', '').strip()
                
                # Only add pairs where both activity and description are provided
                if activity and description:
                    activities.append(activity)
                    descriptions.append(description)
                # Handle case where only one field is filled
                elif activity or description:
                    flash(f'Activity {i+1} requires both name and description', 'warning')
                    # You might want to preserve the form data here
                    return redirect(url_for('details'))

            # If no activities were added, store empty arrays
            extracurriculars = json.dumps({
                'activities': activities,
                'descriptions': descriptions
            }) if activities else json.dumps({'activities': [], 'descriptions': []})

            if not user:
                user = User(username=session['username'])
                db.session.add(user)

            # Update user details
            try:
                user.fullname = fullname
                user.email = email
                user.linkedin = linkedin
                user.github = github
                user.school_name = school_name
                user.course = course
                user.duration = duration
                user.programming_languages = programming_languages
                user.libraries = libraries
                user.tools = tools
                user.extracurriculars = extracurriculars

                db.session.commit()
                flash('Details updated successfully!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash('Error updating details. Please try again.', 'error')
                print(f"Database error: {e}")
                return redirect(url_for('details'))
        
        
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


        
    @app.route('/compare', methods=['GET'])
    def compare():
        """Initial comparison method selection page"""
        if not session.get('username'):
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return render_template('compare_choice.html')

    @app.route('/compare/manual', methods=['GET', 'POST'])
    def manual_compare():
        """Original compare functionality"""
        if not session.get('username'):
            flash('Please login first', 'error')
            return redirect(url_for('login'))

        if request.method == 'GET':
            return render_template('compare.html')

        # Handle file upload and text input
        jd_text = ""
        if 'jd_file' in request.files:
            file = request.files['jd_file']
            if file and allowed_file(file.filename):
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                jd_text = process_pdf(file_path)

        if not jd_text:
            jd_text = process_text(request.form.get('jd_text', ''))

        if not jd_text:
            flash("Please provide a job description.", "warning")
            return redirect(url_for('manual_compare'))

        projects = load_data()
        if not projects:
            flash("No projects found.", "info")
            return redirect(url_for('manual_compare'))

        top_projects = compare_jd(jd_text, projects)
        return render_template('compare_results.html', projects=top_projects)

    @app.route('/compare/automated', methods=['GET', 'POST'])
    def automated_compare():
        """New automated comparison route"""
        if not session.get('username'):
            flash('Please login first', 'error')
            return redirect(url_for('login'))

        if request.method == 'GET':
            return render_template('compare.html')  # Reuse the same form template

        jd_text = ""
        if 'jd_file' in request.files:
            file = request.files['jd_file']
            if file and allowed_file(file.filename):
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(file_path)
                jd_text = process_pdf(file_path)

        if not jd_text:
            jd_text = process_text(request.form.get('jd_text', ''))

        if not jd_text:
            flash("Please provide a job description.", "warning")
            return redirect(url_for('automated_compare'))

        projects = load_data()
        if not projects:
            flash("No projects found.", "info")
            return redirect(url_for('automated_compare'))

        # Get top projects
        top_projects = compare_jd(jd_text, projects)
        
        # Get descriptions for top projects
        descriptions = get_descriptions(top_projects)
        
        # Generate bullets directly
        bullet_results = generate_bullets(descriptions)

        # Save bullets to database
        for project_name, bullets in bullet_results.items():
            project = Projects.query.filter_by(
                username=session.get("username"),
                projectname=project_name
            ).first()
            if project:
                project.bulletpoints = json.dumps(bullets)

        try:
            db.session.commit()
            flash("Bullet points automatically generated and saved!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Error saving bullet points.", "error")
            print(f"Database error: {e}")

        return render_template("bullet_results.html", bullets=bullet_results)
    

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
                return redirect(url_for('signup'))  # Redirect to signup after deletion
            else:
                flash("User not found!", "error")
                return redirect(url_for('delete_user'))  # Stay on delete page if user not found

    """ 
        Placeholder for a tracking feature. Intended for future implementation
        of project tracking functionality.
    """
    

    @app.route('/edit_project',methods=['POST','GET'])
    def edit_project():
        if request.method == 'GET':
            project_name = request.args.get('name')
            username = session["username"]
            bullets_tup = db.session.query(Projects.bulletpoints).filter(Projects.username == username, Projects.projectname == project_name).first()
            bullets= json.loads(bullets_tup[0])
            return render_template("edit.html", project_name=project_name, bullets=bullets)
        
        elif request.method == 'POST':
            project_name = request.form.get("project_name")
            username = session.get("username")
            bullets = request.form.getlist("bullets")  # Comes from multiple inputs with name="bullets"

            project = db.session.query(Projects).filter_by(username=username, projectname=project_name).first()
            final_bullets = []
            for i in bullets:
                if i != "":
                    final_bullets.append(i)
            if project:
                project.bulletpoints = json.dumps(final_bullets)

            try:
                db.session.commit()
                flash("Bullet points successfully updated!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Error saving bullet points.", "error")
                print("Error:", e)

            return redirect(url_for("view"))


    @app.route('/add_bullet',methods = ['POST','GET'])
    def add_bullet():
        if request.method == 'GET':
            project_name = request.args.get('name')
            username = session["username"]
            description_tup = db.session.query(Projects.description).filter(Projects.username == username, Projects.projectname == project_name).first()
            description = description_tup[0]
            return render_template("Generate_single_proj.html",project_name=project_name,description=description)
        
        elif request.method == 'POST':
            username = session.get("username")
            project_name = request.form.get("project_name")
            description = request.form.get("project_info")

            # Generating bullet points
            input_for_propmpt = f"{project_name} : {description}"
            bullets_dict = generate_bullets(input_for_propmpt)
            bullets = bullets_dict[project_name]

            #Adding to database
            project = db.session.query(Projects).filter_by(username=username, projectname=project_name).first()
            if project:
                project.bulletpoints = json.dumps(bullets)

            try:
                db.session.commit()
                flash("Bullet points successfully updated!", "success")
            except Exception as e:
                db.session.rollback()
                flash("Error saving bullet points.", "error")
                print("Error:", e)

            return redirect(url_for("edit_project",name=project_name))
            

