"""
Skill taxonomy and relationships for knowledge graph-based matching.
This module defines the skill hierarchies and relationships that will be used
to generate structured data for the knowledge graph approach.
"""

# Main skill domains
DOMAINS = {
    "software_engineering": "Software Engineering",
    "data_science": "Data Science",
    "design": "Design",
    "business": "Business",
    "marketing": "Marketing"
}

# Skill categories within domains
CATEGORIES = {
    "technical": "Technical Skills",
    "soft": "Soft Skills",
    "domain": "Domain Knowledge",
    "tools": "Tools & Technologies",
    "methodologies": "Methodologies & Practices",
    "languages": "Programming Languages",
    "frameworks": "Frameworks & Libraries",
    "platforms": "Platforms & Systems"
}

# Relationship types
RELATIONSHIPS = {
    "requires": "Requires",
    "related_to": "Related To",
    "subset_of": "Subset Of",
    "complementary_to": "Complementary To"
}

# Skill definitions with relationships
# Structure:
# {
#     "skill_id": {
#         "name": "Skill Name",
#         "domain": "domain_id",
#         "category": "category_id",
#         "relationships": {
#             "relationship_type": ["related_skill_id1", "related_skill_id2", ...]
#         }
#     }
# }

SKILLS = {
    # Software Engineering Skills
    "python": {
        "name": "Python",
        "domain": "software_engineering",
        "category": "languages",
        "relationships": {
            "related_to": ["data_analysis", "backend_dev", "automation"],
            "subset_of": ["programming"]
        }
    },
    "javascript": {
        "name": "JavaScript",
        "domain": "software_engineering",
        "category": "languages",
        "relationships": {
            "related_to": ["frontend_dev", "web_dev"],
            "subset_of": ["programming"]
        }
    },
    "java": {
        "name": "Java",
        "domain": "software_engineering",
        "category": "languages",
        "relationships": {
            "related_to": ["backend_dev", "enterprise_dev"],
            "subset_of": ["programming"]
        }
    },
    "react": {
        "name": "React",
        "domain": "software_engineering",
        "category": "frameworks",
        "relationships": {
            "requires": ["javascript"],
            "related_to": ["frontend_dev", "ui_dev"],
            "subset_of": ["web_frameworks"]
        }
    },
    "nodejs": {
        "name": "Node.js",
        "domain": "software_engineering",
        "category": "frameworks",
        "relationships": {
            "requires": ["javascript"],
            "related_to": ["backend_dev", "server_side"],
            "subset_of": ["web_frameworks"]
        }
    },
    "docker": {
        "name": "Docker",
        "domain": "software_engineering",
        "category": "tools",
        "relationships": {
            "related_to": ["devops", "containerization", "deployment"],
            "complementary_to": ["kubernetes", "ci_cd"]
        }
    },
    "ci_cd": {
        "name": "CI/CD",
        "domain": "software_engineering",
        "category": "methodologies",
        "relationships": {
            "related_to": ["devops", "automation"],
            "complementary_to": ["docker", "git"]
        }
    },
    "git": {
        "name": "Git",
        "domain": "software_engineering",
        "category": "tools",
        "relationships": {
            "related_to": ["version_control", "collaboration"],
            "complementary_to": ["ci_cd"]
        }
    },
    "frontend_dev": {
        "name": "Frontend Development",
        "domain": "software_engineering",
        "category": "domain",
        "relationships": {
            "requires": ["html", "css", "javascript"],
            "related_to": ["ui_design", "web_dev"],
            "complementary_to": ["backend_dev", "ux_design"]
        }
    },
    "backend_dev": {
        "name": "Backend Development",
        "domain": "software_engineering",
        "category": "domain",
        "relationships": {
            "related_to": ["server_side", "databases", "apis"],
            "complementary_to": ["frontend_dev"]
        }
    },
    "devops": {
        "name": "DevOps",
        "domain": "software_engineering",
        "category": "domain",
        "relationships": {
            "related_to": ["infrastructure", "automation", "ci_cd"],
            "requires": ["linux", "scripting"]
        }
    },
    
    # Data Science Skills
    "data_analysis": {
        "name": "Data Analysis",
        "domain": "data_science",
        "category": "domain",
        "relationships": {
            "related_to": ["statistics", "data_visualization"],
            "subset_of": ["data_science"]
        }
    },
    "machine_learning": {
        "name": "Machine Learning",
        "domain": "data_science",
        "category": "domain",
        "relationships": {
            "requires": ["statistics", "programming"],
            "related_to": ["ai", "deep_learning", "data_analysis"],
            "subset_of": ["data_science"]
        }
    },
    "deep_learning": {
        "name": "Deep Learning",
        "domain": "data_science",
        "category": "domain",
        "relationships": {
            "requires": ["machine_learning", "neural_networks"],
            "subset_of": ["machine_learning"]
        }
    },
    "data_visualization": {
        "name": "Data Visualization",
        "domain": "data_science",
        "category": "domain",
        "relationships": {
            "related_to": ["data_analysis", "bi"],
            "complementary_to": ["statistics", "communication"]
        }
    },
    "sql": {
        "name": "SQL",
        "domain": "data_science",
        "category": "languages",
        "relationships": {
            "related_to": ["databases", "data_analysis"],
            "complementary_to": ["data_modeling"]
        }
    },
    "r": {
        "name": "R",
        "domain": "data_science",
        "category": "languages",
        "relationships": {
            "related_to": ["statistics", "data_analysis"],
            "subset_of": ["programming"]
        }
    },
    "pandas": {
        "name": "Pandas",
        "domain": "data_science",
        "category": "frameworks",
        "relationships": {
            "requires": ["python"],
            "related_to": ["data_analysis", "data_manipulation"],
            "complementary_to": ["numpy", "matplotlib"]
        }
    },
    "tensorflow": {
        "name": "TensorFlow",
        "domain": "data_science",
        "category": "frameworks",
        "relationships": {
            "requires": ["python", "machine_learning"],
            "related_to": ["deep_learning", "neural_networks"],
            "complementary_to": ["keras", "pytorch"]
        }
    },
    "tableau": {
        "name": "Tableau",
        "domain": "data_science",
        "category": "tools",
        "relationships": {
            "related_to": ["data_visualization", "bi"],
            "complementary_to": ["sql", "data_analysis"]
        }
    },
    
    # Design Skills
    "ui_design": {
        "name": "UI Design",
        "domain": "design",
        "category": "domain",
        "relationships": {
            "related_to": ["ux_design", "visual_design"],
            "complementary_to": ["frontend_dev"]
        }
    },
    "ux_design": {
        "name": "UX Design",
        "domain": "design",
        "category": "domain",
        "relationships": {
            "related_to": ["ui_design", "user_research"],
            "complementary_to": ["frontend_dev", "product_management"]
        }
    },
    "graphic_design": {
        "name": "Graphic Design",
        "domain": "design",
        "category": "domain",
        "relationships": {
            "related_to": ["visual_design", "branding"],
            "complementary_to": ["marketing"]
        }
    },
    "figma": {
        "name": "Figma",
        "domain": "design",
        "category": "tools",
        "relationships": {
            "related_to": ["ui_design", "prototyping"],
            "complementary_to": ["adobe_xd", "sketch"]
        }
    },
    
    # Business Skills
    "project_management": {
        "name": "Project Management",
        "domain": "business",
        "category": "domain",
        "relationships": {
            "related_to": ["leadership", "planning", "team_management"],
            "complementary_to": ["communication", "problem_solving"]
        }
    },
    "product_management": {
        "name": "Product Management",
        "domain": "business",
        "category": "domain",
        "relationships": {
            "related_to": ["user_research", "strategy", "roadmapping"],
            "complementary_to": ["project_management", "ux_design"]
        }
    },
    "agile": {
        "name": "Agile Methodology",
        "domain": "business",
        "category": "methodologies",
        "relationships": {
            "subset_of": ["project_management"],
            "related_to": ["scrum", "kanban"],
            "complementary_to": ["team_management"]
        }
    },
    
    # Soft Skills
    "communication": {
        "name": "Communication",
        "domain": "business",
        "category": "soft",
        "relationships": {
            "complementary_to": ["teamwork", "leadership"],
            "related_to": ["presentation", "writing"]
        }
    },
    "teamwork": {
        "name": "Teamwork",
        "domain": "business",
        "category": "soft",
        "relationships": {
            "complementary_to": ["communication", "leadership"],
            "related_to": ["collaboration"]
        }
    },
    "problem_solving": {
        "name": "Problem Solving",
        "domain": "business",
        "category": "soft",
        "relationships": {
            "complementary_to": ["critical_thinking", "creativity"],
            "related_to": ["analytical_thinking"]
        }
    }
}

# Proficiency levels for skills
PROFICIENCY_LEVELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "expert": "Expert"
}

# Helper functions to work with the skill taxonomy
def get_skill_by_name(name):
    """Get a skill by its name (case-insensitive)."""
    name_lower = name.lower()
    for skill_id, skill in SKILLS.items():
        if skill["name"].lower() == name_lower:
            return skill_id, skill
    return None, None

def get_related_skills(skill_id):
    """Get all skills related to a given skill."""
    if skill_id not in SKILLS:
        return []
    
    related = []
    skill = SKILLS[skill_id]
    
    # Add directly related skills
    for rel_type, rel_skills in skill.get("relationships", {}).items():
        for rel_skill in rel_skills:
            if rel_skill in SKILLS:
                related.append((rel_skill, SKILLS[rel_skill], rel_type))
    
    return related

def get_domain_skills(domain):
    """Get all skills in a specific domain."""
    return {skill_id: skill for skill_id, skill in SKILLS.items() 
            if skill.get("domain") == domain}

def get_skills_by_category(category):
    """Get all skills in a specific category."""
    return {skill_id: skill for skill_id, skill in SKILLS.items() 
            if skill.get("category") == category} 