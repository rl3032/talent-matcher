import {
  Job,
  JobWithSkills,
  Candidate,
  CandidateWithSkills,
  MatchResult,
  SkillGapAnalysis,
  SkillRecommendation,
  SkillGraphData,
} from "../types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const apiClient = {
  // Job endpoints
  getAllJobs: () => fetch(`${API_BASE_URL}/jobs`).then((res) => res.json()),

  async getJob(jobId: string): Promise<JobWithSkills> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!response.ok) throw new Error("Failed to fetch job details");
    const data = await response.json();

    // Return the complete job data with enhanced fields and skills
    return {
      ...data.job,
      skills: data.skills || [],
    };
  },

  // Basic job matching - used for compatibility
  getJobMatches: (jobId: string, limit = 10, minScore = 0) =>
    fetch(
      `${API_BASE_URL}/jobs/${jobId}/matches?limit=${limit}&min_score=${minScore}`
    ).then((res) => res.json()),

  // Find matching candidates for a job (basic version)
  getBasicJobMatches: (jobId: string, limit = 10) =>
    fetch(`${API_BASE_URL}/jobs/${jobId}/candidates?limit=${limit}`).then(
      (res) => {
        if (!res.ok) throw new Error("Failed to fetch matching candidates");
        return res.json();
      }
    ),

  // Find matching candidates with enhanced algorithm
  async getJobMatchesEnhanced(
    jobId: string,
    options: {
      limit?: number;
      skillsWeight?: number;
      locationWeight?: number;
      semanticWeight?: number;
    } = {}
  ) {
    const {
      limit = 10,
      skillsWeight = 0.75,
      locationWeight = 0.15,
      semanticWeight = 0.1,
    } = options;

    try {
      const url = new URL(`${API_BASE_URL}/jobs/${jobId}/candidates/enhanced`);
      url.searchParams.append("limit", limit.toString());
      url.searchParams.append("skills_weight", skillsWeight.toString());
      url.searchParams.append("location_weight", locationWeight.toString());
      url.searchParams.append("semantic_weight", semanticWeight.toString());

      // Get token from localStorage
      const token = localStorage.getItem("accessToken");

      const response = await fetch(url.toString(), {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });

      if (!response.ok)
        throw new Error("Failed to fetch enhanced candidate matches");
      return await response.json();
    } catch (error) {
      console.error("Error fetching enhanced candidate matches:", error);
      throw error;
    }
  },

  // Candidate endpoints
  getAllCandidates: () => {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    return fetch(`${API_BASE_URL}/candidates`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }).then((res) => res.json());
  },

  async getCandidate(resumeId: string): Promise<CandidateWithSkills> {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    const response = await fetch(`${API_BASE_URL}/candidates/${resumeId}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) throw new Error("Failed to fetch candidate details");
    const data = await response.json();

    // Return the complete candidate data with enhanced fields and skills
    return {
      ...data.candidate,
      skills: data.skills || [],
    };
  },

  // Update candidate profile
  async updateResume(resumeId: string, resumeData: any): Promise<any> {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    if (!token) {
      throw new Error("You must be logged in to update a resume");
    }

    const response = await fetch(
      `${API_BASE_URL}/candidates/${resumeId}/update`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(resumeData),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to update resume");
    }

    return response.json();
  },

  // Update job posting
  async updateJob(jobId: string, jobData: any): Promise<any> {
    const token = localStorage.getItem("accessToken");
    if (!token) throw new Error("Authentication required");

    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(jobData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to update job");
    }

    return response.json();
  },

  // Find matching jobs for a candidate
  async getCandidateMatches(resumeId: string, limit = 10) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/candidates/${resumeId}/jobs?limit=${limit}`
      );
      if (!response.ok) throw new Error("Failed to fetch matching jobs");
      return await response.json();
    } catch (error) {
      console.error("Error fetching matching jobs:", error);
      throw error;
    }
  },

  // Find matching jobs with enhanced algorithm
  async getCandidateMatchesEnhanced(
    resumeId: string,
    options: {
      limit?: number;
      skillsWeight?: number;
      locationWeight?: number;
      semanticWeight?: number;
    } = {}
  ) {
    const {
      limit = 10,
      skillsWeight = 0.75,
      locationWeight = 0.15,
      semanticWeight = 0.1,
    } = options;

    try {
      const url = new URL(
        `${API_BASE_URL}/candidates/${resumeId}/jobs/enhanced`
      );
      url.searchParams.append("limit", limit.toString());
      url.searchParams.append("skills_weight", skillsWeight.toString());
      url.searchParams.append("location_weight", locationWeight.toString());
      url.searchParams.append("semantic_weight", semanticWeight.toString());

      const response = await fetch(url.toString());
      if (!response.ok) throw new Error("Failed to fetch enhanced job matches");
      return await response.json();
    } catch (error) {
      console.error("Error fetching enhanced job matches:", error);
      throw error;
    }
  },

  // Skill gap analysis
  async getSkillGap(candidateId: string, jobId: string): Promise<any> {
    const token = localStorage.getItem("accessToken");
    if (!token) throw new Error("Authentication required");

    const response = await fetch(
      `${API_BASE_URL}/analysis/skill-gap/${candidateId}/${jobId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch skill gap analysis");
    }

    return response.json();
  },

  // Recommendations
  getSkillRecommendations: (
    resumeId: string,
    jobId: string,
    count = 5
  ): Promise<SkillRecommendation[]> =>
    fetch(
      `${API_BASE_URL}/skills/recommendations?resume_id=${resumeId}&job_id=${jobId}&count=${count}`
    ).then((res) => {
      if (!res.ok) throw new Error("Failed to fetch skill recommendations");
      return res.json();
    }),

  // Skills related endpoints
  getAllSkills: () => fetch(`${API_BASE_URL}/skills`).then((res) => res.json()),

  getSkill: (skillId: string) =>
    fetch(`${API_BASE_URL}/skills/${skillId}`).then((res) => res.json()),

  getRelatedSkills: (skillId: string) =>
    fetch(`${API_BASE_URL}/skills/${skillId}/related`).then((res) =>
      res.json()
    ),

  getSkillPath: (startSkill: string, endSkill: string, maxDepth?: number) =>
    fetch(
      `${API_BASE_URL}/skills/path?start=${startSkill}&end=${endSkill}&max_depth=${
        maxDepth || 3
      }`
    ).then((res) => res.json()),

  // Skill graph data
  getSkillGraphData: (skillId: string): Promise<SkillGraphData> =>
    fetch(`${API_BASE_URL}/graph/skill/${skillId}`).then((res) => {
      if (!res.ok) throw new Error("Failed to fetch skill graph data");
      return res.json();
    }),

  // Get complete skills network for visualization
  getSkillsNetwork: (): Promise<SkillGraphData> =>
    fetch(`${API_BASE_URL}/graph/skills-network`).then((res) => {
      if (!res.ok) throw new Error("Failed to fetch skills network");
      return res.json();
    }),
};
