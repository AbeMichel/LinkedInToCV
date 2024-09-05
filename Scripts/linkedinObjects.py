from time import sleep
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup

from CVs import CurriculumVitae, Project, Education, Experience


class LoginStatus(Enum):
    SUCCESS = 0
    FAIL = 1
    VERIFY = 2


class LinkedinProfile:
    def __init__(self, slug: str):
        self.profile_url = f"https://www.linkedin.com/in/{slug}"
        self.name = ""
        self.about = ""
        self.projects: list[Project] = []
        self.educations: list[Education] = []
        self.experiences: list[Experience] = []

    def create_cv(self) -> CurriculumVitae:
        return CurriculumVitae(self.name, self.experiences, self.educations, self.projects)

    def set_about(self, text: str):
        self.about = text

    def set_name(self, text: str):
        self.name = text

    def add_project(self, project: Project):
        self.projects.append(project)

    def add_education(self, education: Education):
        self.educations.append(education)

    def add_experience(self, experience: Experience):
        self.experiences.append(experience)


class LinkedinInstance:
    def __init__(self, chrome_options = None):
        self.user_id = ""
        self.user_pass = ""

        # Create a driver and open a window to login
        if chrome_options is None:
            self.driver = webdriver.Chrome()
        else:
            self.driver = webdriver.Chrome(options=chrome_options)

    def __get_education__(self, linkedin_profile: LinkedinProfile):
        # Find the elements containing education details
        education_container = self.driver.find_elements(By.CLASS_NAME, "artdeco-card.pb3")
        if len(education_container) == 0:
            return
        education_container = education_container[0]
        entries = education_container.find_elements(By.CLASS_NAME, "artdeco-list__item")

        # Extract details
        for entry in entries:
            try:
                span_elements = entry.find_elements(By.TAG_NAME, "span")
                actual_info = []
                for span in span_elements:
                    classes = span.get_attribute('class')
                    if any(cls in classes for cls in ['visually-hidden', 'white-space-pre', 't-14']):
                        continue
                    actual_info.append(span.text)

                school_name = actual_info[0]
                degree = actual_info[1]
                dates = actual_info[2].split('-')
                start_date = dates[0].strip()
                end_date = dates[1].strip()
                ecs = ""
                i = 3
                if actual_info[3].startswith("Activities and societies:"):
                    ecs = actual_info[3].replace("Activities and societies:", "").strip()
                    i += 1
                desc = ""
                while i < len(actual_info):
                    desc += actual_info[i]
                    i += 1
                edu = Education(school_name, "[LOCATION]", degree, ecs, desc, start_date, end_date)
                linkedin_profile.add_education(edu)

            except Exception as e:
                print(f"Error extracting education data: {e}")

    def __get_experience__(self, linkedin_profile: LinkedinProfile):
        # Find the elements containing education details
        experience_container = self.driver.find_elements(By.CLASS_NAME, "artdeco-card.pb3")
        if len(experience_container) == 0:
            return
        experience_container = experience_container[0]
        entries = experience_container.find_elements(By.CLASS_NAME, "artdeco-list__item")

        # Extract details
        for entry in entries:
            try:
                span_elements = entry.find_elements(By.TAG_NAME, "span")
                actual_info = []
                num_bolds = 0
                for span in span_elements:
                    classes = span.get_attribute('class')
                    if any(cls in classes for cls in ['visually-hidden', 'white-space-pre', 't-14']):
                        continue
                    if 't-bold' in span.find_element(By.XPATH, './..').get_attribute('class') or 't-bold' in classes:
                        num_bolds += 1
                    actual_info.append(span.text)
                    # print(span.text)
                if num_bolds == 1:
                    # 0 title
                    title = actual_info[0]
                    # 1 company · employment type
                    info = actual_info[1].split('·')
                    company = info[0].strip()
                    # 2 start date - end date · duration
                    info = actual_info[2].split('·')
                    dates = info[0].split('-')
                    start_date = dates[0].strip()
                    end_date = dates[1].strip()
                    # 3 location · hybrid/on-site
                    location = actual_info[3].split('·')[0].strip()
                    # 4 description
                    description = actual_info[4]
                    exp = Experience(title, description, company, location, start_date, end_date)
                    linkedin_profile.add_experience(exp)
                elif num_bolds > 1:
                    # 0 Employer
                    company = actual_info[0]
                    # 1 Employment type · duration
                    # 2 location · hybrid/on-site
                    location = actual_info[2].split('·')[0].strip()
                    jobs = []
                    current_job = []
                    for line in actual_info[3:]:
                        if line.strip() == '':
                            jobs.append(current_job)
                            current_job = []
                        else:
                            current_job.append(line)
                    if current_job and len(current_job) > 0:
                        jobs.append(current_job)
                    # 3 space
                    for job in jobs:
                        if len(job) == 0:
                            continue
                        # 0 title
                        title = job[0].strip()
                        # 1 start date - end date · duration
                        dates = job[1].split('·')[0].split('-')
                        start_date = dates[0].strip()
                        end_date = dates[1].strip()
                        # 2 description
                        description = job[2] if len(job) > 2 else ''
                        exp = Experience(title, description, company, location, start_date, end_date)
                        linkedin_profile.add_experience(exp)
                        # print("Added: " + exp.title)

                # print('-' * 40)
            except NoSuchElementException as e:
                pass

    def __get_projects__(self, linkedin_profile: LinkedinProfile):
        # Find the elements containing education details
        project_container = self.driver.find_elements(By.CLASS_NAME, "artdeco-card.pb3")
        if len(project_container) == 0:
            return
        project_container = project_container[0]
        entries = project_container.find_elements(By.CLASS_NAME, "artdeco-list__item")

        # Extract details
        for entry in entries:
            try:
                span_elements = entry.find_elements(By.TAG_NAME, "span")
                actual_info = []
                for span in span_elements:
                    classes = span.get_attribute('class')
                    if any(cls in classes for cls in ['visually-hidden', 'white-space-pre', 't-14']):
                        continue
                    actual_info.append(span.text)

                # 0 title
                title = actual_info[0].strip()
                # 1 start date - end date
                dates = actual_info[1].split('-')
                start_date = dates[0].strip()
                end_date = dates[1].strip()
                # 2 description
                description = ""
                for line in actual_info[2:]:
                    line = line.strip()
                    if line == '' or line.startswith("Associated with"):
                        continue
                    if line.startswith("Skills:"):
                        break
                    else:
                        description += line

                # .. Skills
                proj = Project(title, description, start_date, end_date)
                linkedin_profile.add_project(proj)
            except Exception as e:
                print(f"Error extracting project data: {e}")

    def scrape_profile(self, profile: LinkedinProfile):
        if profile is None:
            return
        # Navigate to profile
        self.driver.get(profile.profile_url)
        sleep(1)  # Wait for things to load
        has_experiences = False
        has_projects = False
        has_educations = False

        name_element = self.driver.find_element(By.TAG_NAME, 'h1')
        profile.set_name(name_element.text)

        # Get the about section
        about_id_element = self.driver.find_element(By.ID, "about")
        if about_id_element is not None:
            about_parent = about_id_element.find_element(By.XPATH, "./..")
            if about_parent is not None:
                spans = about_parent.find_elements(By.TAG_NAME, 'span')
                if len(spans) > 2:
                    profile.set_about(spans[2].text)

        # Check for the sections of the profile
        try:
            self.driver.find_element(By.ID, "experience")
            has_experiences = True
        except NoSuchElementException:
            print("No experiences on profile.")
        try:
            self.driver.find_element(By.ID, "education")
            has_educations = True
        except NoSuchElementException:
            print("No educations on profile.")
        try:
            self.driver.find_element(By.ID, "projects")
            has_projects = True
        except NoSuchElementException:
            print("No projects on profile.")

        # Get work experiences
        if has_experiences:
            self.driver.get(f"{profile.profile_url}/details/experience")
            sleep(2)
            self.__get_experience__(profile)
        # Get projects
        if has_projects:
            self.driver.get(f"{profile.profile_url}/details/projects")
            sleep(2)
            self.__get_projects__(profile)
            pass
        # Get educations
        if has_educations:
            self.driver.get(f"{profile.profile_url}/details/education")
            sleep(2)
            self.__get_education__(profile)

    def attempt_login(self, user_id: str, user_pass: str) -> LoginStatus:
        self.user_id = user_id
        self.user_pass = user_pass

        # navigate to linkedin
        self.driver.get('https://www.linkedin.com/login')

        # sign in
        email_field = self.driver.find_element(By.ID, 'username')
        email_field.send_keys(self.user_id)
        pass_field = self.driver.find_element(By.ID, 'password')
        pass_field.send_keys(self.user_pass)
        sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.btn__primary--large.from__button--floating')
        sign_in_btn.click()

        # incorrect username or password
        if self.driver.current_url == "https://www.linkedin.com/checkpoint/lg/login-submit":
            return LoginStatus.FAIL

        # needs to have verification
        if self.driver.current_url != "https://www.linkedin.com/feed/":
            return LoginStatus.VERIFY

        return LoginStatus.SUCCESS

    def terminate(self):
        self.driver.quit()

