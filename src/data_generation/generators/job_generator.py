from typing import Dict, Any, List
import random
import json
from .base_generator import BaseGenerator
from ..skill_taxonomy import SKILLS, DOMAINS, CATEGORIES, get_domain_skills, get_skill_by_name

class JobGenerator(BaseGenerator):
    """Generator for job description data with knowledge graph structure."""
    
    # Canadian cities for job locations
    CANADIAN_CITIES = [
        # Ontario
        "Toronto, ON", "Ottawa, ON", "Hamilton, ON", "London, ON", "Waterloo, ON",
        # British Columbia
        "Vancouver, BC", "Victoria, BC", "Burnaby, BC",
        # Quebec
        "Montreal, QC", "Quebec City, QC", 
        # Alberta
        "Calgary, AB", "Edmonton, AB"
    ]
    
    # Company name components for tech and data science companies
    COMPANY_PREFIXES = [
        # Tech-themed
        "Tech", "Digital", "Cyber", "Data", "Cloud", "Net", "Web", "Byte", "Code", "Logic",
        "AI", "Quantum", "Nexus", "Vertex", "Vector", "Signal", "Neural", "Insight", "Algo"
    ]
    
    COMPANY_SUFFIXES = [
        # Tech-specific
        "Technologies", "Solutions", "Systems", "Software", "Digital", "Tech", "Innovations", 
        "Labs", "Analytics", "Data", "AI", "Learning", "Insights", "Science"
    ]
    
    # Limit to these domains for the MVP
    FOCUS_DOMAINS = ["software_engineering", "data_science"]
    
    def __init__(self, output_dir: str = "data/generated"):
        """Initialize the job generator."""
        super().__init__(output_dir)
    
    def _generate_company_name(self) -> str:
        """Generate a realistic tech or data company name."""
        name_patterns = [
            f"{random.choice(self.COMPANY_PREFIXES)} {random.choice(self.COMPANY_SUFFIXES)}",
            f"{random.choice(self.COMPANY_PREFIXES)}{random.choice(self.COMPANY_PREFIXES)} {random.choice(self.COMPANY_SUFFIXES)}",
            f"{random.choice(self.COMPANY_PREFIXES)} {random.choice(self.COMPANY_PREFIXES)} {random.choice(self.COMPANY_SUFFIXES)}"
        ]
        return random.choice(name_patterns)
    
    def _get_job_title_for_domain(self, domain: str) -> str:
        """Get a job title relevant to the specified domain."""
        if domain == "software_engineering":
            titles = [
                "Software Engineer", "Full Stack Developer", "Frontend Developer",
                "Backend Developer", "DevOps Engineer", "Site Reliability Engineer",
                "Mobile Developer", "Software Architect", "Engineering Manager"
            ]
        elif domain == "data_science":
            titles = [
                "Data Scientist", "Machine Learning Engineer", "Data Analyst",
                "Business Intelligence Analyst", "Data Engineer", "Research Scientist",
                "Data Science Manager", "AI Specialist", "Data Visualization Specialist"
            ]
        else:
            titles = ["Product Manager", "Project Manager", "Technical Lead"]
            
        return random.choice(titles)
    
    def _select_domain_skills(self, domain: str, num_primary: int = 5, num_secondary: int = 3) -> Dict[str, List[Dict]]:
        """
        Select skills from the domain with primary and secondary categorization.
        
        Args:
            domain: The domain to select skills from
            num_primary: Number of primary skills to select
            num_secondary: Number of secondary skills to select
            
        Returns:
            Dictionary with primary and secondary skills, including relationship data
        """
        domain_skills = list(get_domain_skills(domain).items())
        
        # Select primary skills (required)
        primary_skills = []
        if len(domain_skills) >= num_primary:
            selected_primary = random.sample(domain_skills, num_primary)
            for skill_id, skill_data in selected_primary:
                # Add proficiency requirement
                proficiency = random.choice(["intermediate", "advanced", "expert"])
                
                skill_info = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "category": skill_data["category"],
                    "proficiency": proficiency,
                    "is_primary": True,
                    "importance": random.uniform(0.8, 1.0)
                }
                primary_skills.append(skill_info)
        
        # Select secondary skills (preferred)
        secondary_skills = []
        remaining_skills = [s for s in domain_skills if s[0] not in [ps["skill_id"] for ps in primary_skills]]
        
        if len(remaining_skills) >= num_secondary:
            selected_secondary = random.sample(remaining_skills, num_secondary)
            for skill_id, skill_data in selected_secondary:
                # Add proficiency requirement
                proficiency = random.choice(["beginner", "intermediate", "advanced"])
                
                skill_info = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "category": skill_data["category"],
                    "proficiency": proficiency,
                    "is_primary": False,
                    "importance": random.uniform(0.4, 0.7)
                }
                secondary_skills.append(skill_info)
        
        # Add soft skills (always secondary)
        soft_skills = [s for s in SKILLS.items() if s[1]["category"] == "soft"]
        if soft_skills:
            selected_soft = random.sample(soft_skills, min(2, len(soft_skills)))
            for skill_id, skill_data in selected_soft:
                skill_info = {
                    "skill_id": skill_id,
                    "name": skill_data["name"],
                    "category": "soft",
                    "proficiency": "intermediate",
                    "is_primary": False,
                    "importance": random.uniform(0.3, 0.6)
                }
                secondary_skills.append(skill_info)
        
        return {
            "primary_skills": primary_skills,
            "secondary_skills": secondary_skills
        }
    
    def generate_single(self, index: int) -> Dict[str, Any]:
        """Generate a single job description with knowledge graph structure."""
        # Select a domain for this job
        domain = random.choice(self.FOCUS_DOMAINS)
        job_title = self._get_job_title_for_domain(domain)
        location = random.choice(self.CANADIAN_CITIES)
        company = self._generate_company_name()
        
        # Generate skills with graph relationships
        skills_data = self._select_domain_skills(domain)
        
        # Create skills lists for the prompt
        primary_skills_list = [f"{s['name']} ({s['proficiency']})" for s in skills_data["primary_skills"]]
        secondary_skills_list = [f"{s['name']} ({s['proficiency']})" for s in skills_data["secondary_skills"]]
        
        print(f"Generating job #{index} for {job_title} at {company} in {location}...")
        
        prompt = f"""
        Generate a realistic job description for a {job_title} position in Canada.
        
        The job should be for a company called {company}, based in {location}.
        The job is in the domain of {DOMAINS[domain]}.
        
        Primary (required) skills:
        {', '.join(primary_skills_list)}
        
        Secondary (preferred) skills:
        {', '.join(secondary_skills_list)}
        
        The output should be in JSON format with the following structure:
        {{
          "job_id": "job_{index}",
          "title": "{job_title}",
          "company": "{company}",
          "location": "{location}",
          "domain": "{domain}",
          "job_type": "Full-time/Part-time/Contract",
          "summary": "Job summary paragraph",
          "responsibilities": [
            "Responsibility 1",
            "Responsibility 2",
            ...
          ],
          "qualifications": [
            "Qualification 1",
            "Qualification 2",
            ...
          ],
          "salary_range": "Salary range in CAD or 'Competitive'"
        }}
        
        Make it realistic and detailed, with responsibilities that utilize the specific skills listed.
        Do not include the skills section in the JSON as I will add it separately.
        """
        
        # Generate the job description
        job_desc = self._call_openai_api(
            prompt=prompt,
            system_message="You are a helpful assistant that generates realistic job descriptions for the Canadian market in JSON format."
        )
        
        # Add the skills data with knowledge graph structure
        job_desc["skills"] = {
            "primary": skills_data["primary_skills"],
            "secondary": skills_data["secondary_skills"]
        }
        
        # Add skill relationships for graph visualization
        job_desc["skill_relationships"] = self._extract_skill_relationships(skills_data)
        
        return job_desc
    
    def _extract_skill_relationships(self, skills_data: Dict) -> List[Dict]:
        """Extract relationships between skills for the knowledge graph."""
        relationships = []
        
        # Combine all skills
        all_skills = skills_data["primary_skills"] + skills_data["secondary_skills"]
        skill_ids = [skill["skill_id"] for skill in all_skills]
        
        # Find relationships defined in our taxonomy
        for i, skill1 in enumerate(all_skills):
            skill_id1 = skill1["skill_id"]
            if skill_id1 in SKILLS:
                # Add direct relationships from taxonomy
                if "relationships" in SKILLS[skill_id1]:
                    for rel_type, related_skills in SKILLS[skill_id1]["relationships"].items():
                        for related_id in related_skills:
                            # Only include if the related skill is also in our job
                            if related_id in skill_ids:
                                relationships.append({
                                    "source": skill_id1,
                                    "target": related_id,
                                    "type": rel_type,
                                    "weight": 1.0  # Default weight
                                })
                
                # Add relationships between primary skills (they should work together)
                if skill1["is_primary"]:
                    for j in range(i+1, len(all_skills)):
                        skill2 = all_skills[j]
                        if skill2["is_primary"]:
                            # Create a relationship between primary skills
                            relationships.append({
                                "source": skill_id1,
                                "target": skill2["skill_id"],
                                "type": "job_related",  # Custom relationship for the job
                                "weight": 0.7  # Lower weight for inferred relationships
                            })
        
        return relationships
    
    def create_default(self, index: int) -> Dict[str, Any]:
        """Create a default job description if generation fails."""
        domain = random.choice(self.FOCUS_DOMAINS)
        job_title = self._get_job_title_for_domain(domain)
        location = random.choice(self.CANADIAN_CITIES)
        company = self._generate_company_name()
        
        # Generate skills with graph relationships
        skills_data = self._select_domain_skills(domain)
        
        return {
            "job_id": f"job_{index}",
            "title": job_title,
            "company": company,
            "location": location,
            "domain": domain,
            "job_type": "Full-time",
            "summary": f"We are looking for a {job_title} to join our team at {company} in {location}.",
            "responsibilities": [
                "Collaborate with team members to achieve project goals",
                "Develop and implement solutions",
                "Communicate with stakeholders"
            ],
            "qualifications": [
                "Bachelor's degree in a relevant field",
                "Previous experience in a similar role",
                "Strong communication skills"
            ],
            "salary_range": "Competitive",
            "skills": {
                "primary": skills_data["primary_skills"],
                "secondary": skills_data["secondary_skills"]
            },
            "skill_relationships": self._extract_skill_relationships(skills_data)
        } 