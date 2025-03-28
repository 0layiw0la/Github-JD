import google.generativeai as genai
from flask import session
from models import Projects
import pandas as pd
import json
from dotenv import load_dotenv
import re
import os


load_dotenv() 

SECRET_KEY = os.environ.get("GEMINI_API_KEY")

def get_descriptions(project_names):
    """Fetch descriptions for the given project names from the database."""
    
    username = session.get("username")
    if not username:
        return {}

    projects = Projects.query.filter(Projects.projectname.in_(project_names), Projects.username == username).all()
    return {p.projectname: (p.description or "").strip() for p in projects}  # Ensure no `None` values




def load_data():
    """Returns the all the projects and their descriptions as one text in a list for prompting"""
    username = session.get('username')
    if not username:
        return []

    projects = Projects.query.filter_by(username=username).all()
    return [f"{project.projectname} -> {project.description}" for project in projects]




genai.configure(api_key=SECRET_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")

def compare_jd(jd,projects):
    COMPARISON_PROMPT = f"""You've been given a job description: \n
                         {jd} \n
                         and these projects \n
                        {projects} \n
                        and you are to compare the projects thinking about what could be used in building them from
                        the description and rate it from 1 to 10 based of the job description, eg are any technologies
                        in the job description mentioned in its description or would they or similar technologies
                        be used? after doing this return only the top 3 projects. i know my projects no need for description.
                        output should look like this NO ADDITIONS (i inted to split as a list so NO ADDITIONS): project1_name_only,project2_name_only,project3_name_only"""
    
    try:
        print("prompting")
        response = model.generate_content(COMPARISON_PROMPT)
        top_3 = response.text
        print(top_3)
        selection = str(top_3).split(',')
        print("prompted")
        

        return selection
    except:
        return "error"
    

def generate_bullets(project_data):
    """
    Generates bullet points to match the OUTPUT_FORMAT constant
    """


    OUTPUT_FORMAT = "{projectname:[point1, point2, point3, point4], projectname:[point1, point2, ...]}"
    PROMPT = f"""
        Generate up to four STAR-format bullet points per project in {project_data}, using strong action verbs and concise resume-style phrasing. Output strictly in this format:
        ({OUTPUT_FORMAT}).
    """

    try:
        print("prompting")
        response = model.generate_content(PROMPT)

        # Extract dictionary content (everything between the first '{' and last '}')
        match = re.search(r"\{(.*)\}", response.text, re.DOTALL)
        if match:
            extracted_dict = "{" + match.group(1) + "}"  # Reconstruct valid JSON
            return json.loads(extracted_dict)  # Convert to Python dictionary
        
        print("No valid dictionary found in response")
        return None
    except Exception as e:
        print(f"Error generating bullets: {e}")
        return None
        
    
