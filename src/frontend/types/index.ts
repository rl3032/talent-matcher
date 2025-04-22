export interface Job {
  job_id: string;
  title: string;
  company: string;
  location: string;
  domain: string;
  description?: string;
  responsibilities?: string[];
  qualifications?: string[];
  salary_range?: string;
  job_type?: string;
  employment_type?: string;
  industry?: string;
  owner_email?: string;
}

export interface JobWithSkills extends Job {
  skills: JobSkill[];
}

export interface Candidate {
  resume_id: string;
  name: string;
  title: string;
  location: string;
  domain: string;
  email?: string;
  summary?: string;
  experience?: {
    title: string;
    company: string;
    period: string;
    description: string[];
    skills?: {
      skill_id: string;
      name: string;
      category: string;
    }[];
  }[];
  education?: {
    institution: string;
    degree: string;
    field: string;
    year: string;
  }[];
  certifications?: {
    name: string;
    issuer: string;
    date: string;
  }[];
  languages?: string[];
}

export interface CandidateWithSkills extends Candidate {
  skills: CandidateSkill[];
}

export interface Skill {
  skill_id: string;
  name: string;
  category: string;
}

export interface JobSkill extends Skill {
  level: number;
  relationship_type: string;
  proficiency: string;
  importance: number;
}

export interface CandidateSkill extends Skill {
  level: number;
  years: number;
}

export interface MatchResult {
  resume_id?: string;
  job_id?: string;
  name?: string;
  title?: string;
  company?: string;
  match_percentage: number;
  graph_percentage: number;
  text_percentage: number;
  matching_skills: Skill[];
  missing_skills: Skill[];
}

export interface SkillGapAnalysis {
  matching_skills: Skill[];
  missing_skills: Skill[];
  exceeding_skills: Skill[];
}

export interface SkillRecommendation {
  skill_id: string;
  name: string;
  category: string;
  relevance_score: number;
  difficulty: number;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface SkillGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
