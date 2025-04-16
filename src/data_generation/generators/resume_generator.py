from pathlib import Path
from typing import Dict, Any, List
import json
import random
import datetime
from .base_generator import BaseGenerator
from ..skill_taxonomy import SKILLS, DOMAINS, CATEGORIES, PROFICIENCY_LEVELS, get_skill_by_name, get_domain_skills

class ResumeGenerator(BaseGenerator):
    """Generator for resume data with knowledge graph structure."""
    
    # Canadian cities for locations (narrowed for MVP)
    CANADIAN_CITIES = [
        # Ontario
        "Toronto, ON", "Ottawa, ON", "Waterloo, ON", 
        # British Columbia
        "Vancouver, BC", "Victoria, BC", 
        # Quebec
        "Montreal, QC", "Quebec City, QC", 
        # Alberta
        "Calgary, AB", "Edmonton, AB"
    ]
    
    # Canadian universities (narrowed for MVP)
    CANADIAN_UNIVERSITIES = [
        # Top tech/data science universities
        "University of Toronto", "University of Waterloo", "University of British Columbia",
        "McGill University", "University of Alberta", "University of Montreal", 
        "Simon Fraser University", "University of Calgary", "Queen's University",
        "McMaster University", "Carleton University"
    ]
    
    # First names pool (narrowed for focus domains)
    FIRST_NAMES = [
        "Emma", "Liam", "Olivia", "Noah", "Sophia", "Michael", "Isabella", "James",
        "Wei", "Ming", "Li", "Priya", "Rohan", "Ananya", "Ahmed", "Sara"
    ]
    
    # Last names pool (narrowed for focus domains)
    LAST_NAMES = [
        "Smith", "Johnson", "Brown", "Taylor", "Lee", "Wang", "Chen", "Zhang",
        "Patel", "Kumar", "Singh", "Tremblay", "Roy", "Côté", "Nguyen", "Kim"
    ]
    
    # Focused domains for the MVP
    FOCUS_DOMAINS = ["software_engineering", "data_science"]
    
    def __init__(self, output_dir: str = "data/generated"):
        """Initialize the resume generator."""
        super().__init__(output_dir)
        self.template = self._load_template()
    
    def _load_template(self) -> Dict[str, Any]:
        """Load the resume template from the data directory."""
        template_path = Path(__file__).parent.parent.parent.parent / "data" / "sample_resume.json"
        with open(template_path, "r") as f:
            return json.load(f)
    
    def _generate_name(self) -> str:
        """Generate a realistic name."""
        return f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}"
    
    def _generate_email(self, name: str) -> str:
        """Generate a realistic email address."""
        # Remove spaces and convert to lowercase
        name = name.lower().replace(" ", "")
        
        # Create email
        domains = ["gmail.com", "outlook.com", "protonmail.com", "yahoo.ca", "icloud.com"]
        return f"{name}@{random.choice(domains)}"
    
    def _generate_phone(self) -> str:
        """Generate a realistic Canadian phone number."""
        # Canadian area codes
        area_codes = ["416", "647", "905", "604", "778", "403", "587", "780", "514", "438", "613"]
        
        # Generate a random phone number
        area_code = random.choice(area_codes)
        prefix = random.randint(100, 999)
        line_number = random.randint(1000, 9999)
        
        return f"+1-{area_code}-{prefix}-{line_number}"
    
    def _select_domain_with_background(self) -> Dict[str, Any]:
        """
        Select a domain and generate a background for the resume.
        
        Returns:
            Dictionary with domain and background info
        """
        domain = random.choice(self.FOCUS_DOMAINS)
        
        if domain == "software_engineering":
            degrees = ["Computer Science", "Software Engineering", "Computer Engineering", 
                      "Information Technology", "Web Development"]
            job_titles = ["Software Engineer", "Full Stack Developer", "Frontend Developer",
                         "Backend Developer", "DevOps Engineer", "Mobile Developer"]
        else:  # data_science
            degrees = ["Data Science", "Statistics", "Computer Science", "Mathematics", 
                      "Analytics", "Machine Learning"]
            job_titles = ["Data Scientist", "Data Analyst", "Machine Learning Engineer", 
                         "Business Intelligence Analyst", "Research Scientist"]
            
        # Generate background
        background = {
            "domain": domain,
            "degree": random.choice(degrees),
            "job_title": random.choice(job_titles),
            "university": random.choice(self.CANADIAN_UNIVERSITIES),
            "graduation_year": random.randint(2010, 2023)
        }
        
        return background
    
    def _select_candidate_skills(self, domain: str, experience_level: str = "mid") -> Dict[str, List[Dict]]:
        """
        Select skills for a candidate with proficiency levels and experience durations.
        
        Args:
            domain: The domain to select skills from
            experience_level: junior, mid, or senior
            
        Returns:
            Dictionary with core and secondary skills, including proficiency and experience data
        """
        domain_skills = list(get_domain_skills(domain).items())
        
        # Set number of skills based on experience level
        if experience_level == "junior":
            num_core = random.randint(3, 5)
            num_secondary = random.randint(2, 4)
            experience_range = (0.5, 2)  # 6 months to 2 years
            proficiency_options = ["beginner", "intermediate"]
        elif experience_level == "senior":
            num_core = random.randint(6, 8)
            num_secondary = random.randint(5, 8)
            experience_range = (5, 15)  # 5-15 years
            proficiency_options = ["advanced", "expert"]
        else:  # mid
            num_core = random.randint(5, 7)
            num_secondary = random.randint(3, 6)
            experience_range = (2, 5)  # 2-5 years
            proficiency_options = ["intermediate", "advanced"]
        
        # Select core skills (high proficiency)
        core_skills = []
        if len(domain_skills) >= num_core:
            selected_core = random.sample(domain_skills, num_core)
            for skill_id, skill_data in selected_core:
                # Add proficiency and experience duration
                proficiency = random.choice(proficiency_options)
                experience_years = round(random.uniform(*experience_range), 1)
                
                skill_info = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "category": skill_data["category"],
                    "proficiency": proficiency,
                    "experience_years": experience_years,
                    "is_core": True
                }
                core_skills.append(skill_info)
        
        # Select secondary skills (lower proficiency)
        secondary_skills = []
        remaining_skills = [s for s in domain_skills if s[0] not in [cs["skill_id"] for cs in core_skills]]
        
        if len(remaining_skills) >= num_secondary:
            selected_secondary = random.sample(remaining_skills, num_secondary)
            for skill_id, skill_data in selected_secondary:
                # Add proficiency (lower than core skills)
                if experience_level == "junior":
                    proficiency = "beginner"
                elif experience_level == "senior":
                    proficiency = random.choice(["intermediate", "advanced"])
                else:
                    proficiency = random.choice(["beginner", "intermediate"])
                
                # Shorter experience
                experience_years = round(random.uniform(0.5, experience_range[0]), 1)
                
                skill_info = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "category": skill_data["category"],
                    "proficiency": proficiency,
                    "experience_years": experience_years,
                    "is_core": False
                }
                secondary_skills.append(skill_info)
        
        # Add soft skills
        soft_skills = [s for s in SKILLS.items() if s[1]["category"] == "soft"]
        if soft_skills:
            # Always include communication and teamwork for all candidates
            selected_soft = random.sample(soft_skills, min(3, len(soft_skills)))
            for skill_id, skill_data in selected_soft:
                soft_proficiency = random.choice(proficiency_options)
                skill_info = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "category": "soft",
                    "proficiency": soft_proficiency,
                    "experience_years": round(random.uniform(*experience_range), 1),
                    "is_core": False
                }
                secondary_skills.append(skill_info)
        
        return {
            "core_skills": core_skills,
            "secondary_skills": secondary_skills
        }
    
    def _extract_skill_relationships(self, skills_data: Dict) -> List[Dict]:
        """Extract relationships between skills for the knowledge graph."""
        relationships = []
        
        # Combine all skills
        all_skills = skills_data["core_skills"] + skills_data["secondary_skills"]
        skill_ids = [skill["skill_id"] for skill in all_skills]
        
        # Find relationships defined in our taxonomy
        for skill1 in all_skills:
            skill_id1 = skill1["skill_id"]
            if skill_id1 in SKILLS:
                # Add direct relationships from taxonomy
                if "relationships" in SKILLS[skill_id1]:
                    for rel_type, related_skills in SKILLS[skill_id1]["relationships"].items():
                        for related_id in related_skills:
                            # Only include if the related skill is also in the resume
                            if related_id in skill_ids:
                                # Weight the relationship by experience
                                weight = 0.5 + (skill1["experience_years"] / 10)  # Max weight of 1.5 for 10+ years
                                weight = min(1.0, weight)  # Cap at 1.0
                                
                                relationships.append({
                                    "source": skill_id1,
                                    "target": related_id,
                                    "type": rel_type,
                                    "weight": weight
                                })
        
        return relationships
    
    def _generate_work_experience(self, background: Dict, skills_data: Dict) -> List[Dict]:
        """Generate realistic work experience based on skills."""
        experience_entries = []
        
        # Tech companies
        companies = [
            "Quantum Software", "DataTech Solutions", "InnovateAI", "CodeByte Inc.",
            "Neural Systems", "CloudScale Technologies", "Analytics Insight",
            "Maple Analytics", "Northern Code", "Vector AI", "Nexus Software"
        ]
        
        # Calculate total experience based on skills
        max_experience = max([s["experience_years"] for s in skills_data["core_skills"] + skills_data["secondary_skills"]])
        
        # Generate 2-3 work experiences
        num_experiences = min(3, max(2, int(max_experience / 2)))
        
        # Current year
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        
        end_year = current_year
        end_month = current_month
        
        for i in range(num_experiences):
            # Duration for this role (more recent roles are longer)
            if i == 0:  # Current role
                duration_years = round(random.uniform(1, max_experience/2), 1)
            else:
                duration_years = round(random.uniform(1, 3), 1)
            
            # Calculate start date
            start_year = end_year
            start_month = end_month - (duration_years % 1) * 12
            if start_month <= 0:
                start_month += 12
                start_year -= 1
            start_year -= int(duration_years)
            
            # Format dates
            start_date = f"{start_year}-{int(start_month):02d}"
            if i == 0:
                end_date = "Present"
            else:
                end_date = f"{end_year}-{int(end_month):02d}"
            
            # Next role's end date is before this role's start date
            end_year = start_year
            end_month = start_month - 1
            if end_month <= 0:
                end_month += 12
                end_year -= 1
            
            # Select skills used in this role
            role_core_skills = random.sample(skills_data["core_skills"], min(3, len(skills_data["core_skills"])))
            role_secondary_skills = random.sample(skills_data["secondary_skills"], min(2, len(skills_data["secondary_skills"])))
            role_skills = [s["name"] for s in role_core_skills + role_secondary_skills]
            
            # Generate descriptions based on skills
            descriptions = []
            for skill in role_core_skills:
                if skill["category"] == "languages":
                    descriptions.append(f"Developed and maintained applications using {skill['name']}")
                elif skill["category"] == "frameworks":
                    descriptions.append(f"Built and optimized solutions using {skill['name']}")
                elif skill["category"] == "tools":
                    descriptions.append(f"Utilized {skill['name']} for {random.choice(['development', 'deployment', 'testing', 'analysis'])}")
                elif skill["category"] == "domain":
                    descriptions.append(f"Led {skill['name']} initiatives resulting in improved performance")
            
            # Add generic descriptions if needed
            if background["domain"] == "software_engineering":
                generic_descriptions = [
                    "Collaborated with cross-functional teams to deliver high-quality software products",
                    "Participated in code reviews and implemented best practices",
                    "Resolved complex technical issues and improved system performance"
                ]
            else:  # data_science
                generic_descriptions = [
                    "Analyzed large datasets to extract valuable insights",
                    "Developed predictive models to support business decisions",
                    "Created data visualizations and presentations for stakeholders"
                ]
            
            descriptions.extend(random.sample(generic_descriptions, min(2, len(generic_descriptions))))
            
            # Create job entry
            job_title = background["job_title"]
            if i > 0:
                # Adjust title for previous roles
                if "Senior" in job_title:
                    job_title = job_title.replace("Senior", "")
                elif "Lead" in job_title:
                    job_title = job_title.replace("Lead", "")
                elif i > 1:
                    job_title = "Junior " + job_title
            
            experience = {
                "job_title": job_title,
                "company": random.choice(companies),
                "start_date": start_date,
                "end_date": end_date,
                "description": descriptions,
                "skills_used": role_skills
            }
            
            experience_entries.append(experience)
            
            # Don't reuse company names
            companies.remove(experience["company"])
        
        return experience_entries
    
    def generate_single(self, index: int) -> Dict[str, Any]:
        """Generate a single resume with knowledge graph structure."""
        # Generate basic profile
        name = self._generate_name()
        location = random.choice(self.CANADIAN_CITIES)
        email = self._generate_email(name)
        phone = self._generate_phone()
        
        # Select domain and background
        background = self._select_domain_with_background()
        
        # Random experience level
        experience_level = random.choice(["junior", "mid", "mid", "senior"])
        
        # Select skills with graph relationships
        skills_data = self._select_candidate_skills(background["domain"], experience_level)
        
        # Generate work experience based on skills
        experience = self._generate_work_experience(background, skills_data)
        
        # Create skill lists for prompt
        core_skills_list = [f"{s['name']} ({s['proficiency']}, {s['experience_years']} years)" 
                           for s in skills_data["core_skills"]]
        secondary_skills_list = [f"{s['name']} ({s['proficiency']}, {s['experience_years']} years)" 
                                for s in skills_data["secondary_skills"]]
        
        print(f"Generating resume #{index} for {name} in {background['domain']}...")
        
        prompt = f"""
        Generate a realistic resume for a Canadian professional based on the following information:
        
        Personal Information:
        - Name: {name}
        - Location: {location}
        - Email: {email}
        - Phone: {phone}
        
        Background:
        - Domain: {DOMAINS[background['domain']]}
        - Job Title: {background['job_title']}
        - Experience Level: {experience_level}
        - Degree: {background['degree']}
        - University: {background['university']}
        - Graduation Year: {background['graduation_year']}
        
        Core Skills:
        {', '.join(core_skills_list)}
        
        Secondary Skills:
        {', '.join(secondary_skills_list)}
        
        Work Experience:
        {json.dumps(experience, indent=2)}
        
        The output should be in JSON format with the following structure:
        {{
          "resume_id": "resume_{index}",
          "name": "{name}",
          "email": "{email}",
          "phone": "{phone}",
          "location": "{location}",
          "title": "{background['job_title']}",
          "summary": "Professional summary paragraph",
          "experience": [
            Work experience entries as provided
          ],
          "education": [
            {{
              "degree": "{background['degree']}",
              "institution": "{background['university']}",
              "graduation_year": {background['graduation_year']}
            }}
          ],
          "certifications": [
            "Relevant certification 1",
            "Relevant certification 2"
          ]
        }}
        
        Make the summary highlight the candidate's expertise and experience level.
        Do not include the skills section as I will add that separately.
        Include 1-3 relevant certifications that would be realistic for this profile.
        """
        
        # Generate the resume
        resume = self._call_openai_api(
            prompt=prompt,
            system_message="You are a helpful assistant that generates realistic Canadian resumes in JSON format."
        )
        
        # Add the skills data with knowledge graph structure
        resume["skills"] = {
            "core": skills_data["core_skills"],
            "secondary": skills_data["secondary_skills"],
            "domain": background["domain"]
        }
        
        # Add skill relationships for graph visualization
        resume["skill_relationships"] = self._extract_skill_relationships(skills_data)
        
        return resume
    
    def create_default(self, index: int) -> Dict[str, Any]:
        """Create a default resume if generation fails."""
        # Generate basic profile
        name = self._generate_name()
        location = random.choice(self.CANADIAN_CITIES)
        email = self._generate_email(name)
        phone = self._generate_phone()
        
        # Select domain and background
        background = self._select_domain_with_background()
        
        # Select skills with graph relationships
        skills_data = self._select_candidate_skills(background["domain"], "mid")
        
        # Generate work experience based on skills
        experience = self._generate_work_experience(background, skills_data)
        
        resume = {
            "resume_id": f"resume_{index}",
            "name": name,
            "email": email,
            "phone": phone,
            "location": location,
            "title": background["job_title"],
            "summary": f"Experienced {background['job_title']} with a focus on {background['domain']}.",
            "experience": experience,
            "education": [{
                "degree": background["degree"],
                "institution": background["university"],
                "graduation_year": background["graduation_year"]
            }],
            "certifications": [],
            "skills": {
                "core": skills_data["core_skills"],
                "secondary": skills_data["secondary_skills"],
                "domain": background["domain"]
            },
            "skill_relationships": self._extract_skill_relationships(skills_data)
        }
        
        return resume 