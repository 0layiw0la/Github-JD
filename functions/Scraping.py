from bs4 import BeautifulSoup as BS4
import requests


def scrape_full_details(username: str, top_3: list) -> dict:
    """
    Scrapes the full descriptions and topic list from the user's GitHub repositories.
    The descriptions available on the repositories tab are truncated, so this function retrieves the full details.
    """
    
    result = {} 

    for project in top_3:
        project = project.strip() #To remove whitespaces or new lines that may come along.
        project_url = f"https://github.com/{username}/{project}"
        response = requests.get(project_url)

        if response.status_code != 200: #Some projects have no description so to handle that
            result[project] = None      #we simply store as none
            continue
        
        soup = BS4(response.text, "html.parser")
        desc_tag = soup.find("p", class_="f4 my-3")
        description = desc_tag.get_text(strip=True) if desc_tag else "No description found!"


        # Extract project topics/tags
        topic_tags = soup.find_all("a", class_="topic-tag topic-tag-link")
        tags = [tag_elem.get_text(strip=True) for tag_elem in topic_tags]
        topics = ",".join(tags)
        about = f"{description}. The topics this project touches are: {topics}"

        result[project] = about

    return result



def ScrapeProjects(username: str) -> list:

    """
    Scrapes the list of public repositories for a given GitHub user.
    It retrieves the project name, description, and handles pagination if there are multiple pages.
    """

    github_url = f"https://github.com/{username}?tab=repositories"
    next_page_url = github_url   # Variable to track the next page URL
    scraped_projects = []  

    while next_page_url:
        response = requests.get(next_page_url)
        soup = BS4(response.text, "html.parser")
        repositories = soup.find_all("li", class_="col-12 d-flex flex-justify-between width-full py-4 border-bottom color-border-muted public source")

        for repo in repositories:
            name_tag = repo.find("a", itemprop="name codeRepository")
            name = name_tag.text.strip() if name_tag else None

            description_tag = repo.find("p", itemprop="description")
            description = description_tag.text.strip() if description_tag else None

            if name:  # Only add valid projects
                scraped_projects.append({
                    "username": username,
                    "projectname": name,
                    "description": description
                })

        # Check for pagination: find the "Next Page" link
        pagination_div = soup.find("div", class_="paginate-container")
        if pagination_div:
            next_page_link = pagination_div.find("a", class_="next_page")
            next_page_url = f"https://github.com{next_page_link['href']}" if next_page_link else None
        else:
            next_page_url = None

    return scraped_projects  # Return list of scraped projects


