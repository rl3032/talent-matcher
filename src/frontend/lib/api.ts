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

// Always use the full backend URL instead of relying on rewrites
const API_BASE_URL = "http://localhost:8000/api";

export const apiClient = {
  // Job endpoints
  getAllJobs: () => fetch(`${API_BASE_URL}/jobs`).then((res) => res.json()),

  async getJob(jobId: string): Promise<JobWithSkills> {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) throw new Error("Failed to fetch job details");
    const data = await response.json();

    // Handle the new backend response structure
    if (data.success && data.job) {
      // Format the job data to match the expected structure
      const jobData = data.job;

      // Map description to summary for frontend compatibility
      if (jobData.description && !jobData.summary) {
        jobData.summary = jobData.description;
      }

      // Parse the responsibilities and qualifications if they're strings
      try {
        if (typeof jobData.responsibilities === "string") {
          jobData.responsibilities = JSON.parse(jobData.responsibilities);
        }
        if (typeof jobData.qualifications === "string") {
          jobData.qualifications = JSON.parse(jobData.qualifications);
        }
      } catch (err) {
        console.error("Error parsing job data:", err);
      }

      // Process skills to add is_primary flag based on relationship_type
      const processedSkills = (data.skills || []).map((skill) => ({
        ...skill,
        is_primary: skill.relationship_type === "REQUIRES_PRIMARY",
      }));

      // Add skills field, using data.skills from the response
      return {
        ...jobData,
        skills: processedSkills,
      };
    }

    // Legacy fallback structure
    const jobData = data.job || {};

    // Map description to summary for frontend compatibility
    if (jobData.description && !jobData.summary) {
      jobData.summary = jobData.description;
    }

    // Process skills to add is_primary flag based on relationship_type
    const processedSkills = (data.skills || []).map((skill) => ({
      ...skill,
      is_primary: skill.relationship_type === "REQUIRES_PRIMARY",
    }));

    return {
      ...jobData,
      skills: processedSkills,
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
  getAllCandidates: async () => {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    if (!token) {
      throw new Error("Authentication required to fetch candidates");
    }

    try {
      console.log(
        "Fetching candidates with token:",
        token.substring(0, 15) + "..."
      );

      const response = await fetch(`${API_BASE_URL}/candidates`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log("Response status:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response text:", errorText);

        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          console.error("Error parsing JSON response:", e);
          errorData = { error: errorText };
        }

        if (response.status === 401) {
          console.error("Authentication failed. Token might be invalid.");
          throw new Error("Authentication failed. Please log in again.");
        } else if (response.status === 403) {
          console.error("Authorization failed. User doesn't have permission.");
          throw new Error("You don't have permission to view candidates.");
        }

        throw new Error(
          errorData.error || errorData.msg || "Failed to fetch candidates"
        );
      }

      const data = await response.json();
      console.log("Candidates data received:", data ? "success" : "empty");
      return data;
    } catch (error) {
      console.error("Error fetching candidates:", error);
      throw error;
    }
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

    // Check if we have the new response structure (success + candidate with nested skills)
    if (data.success && data.candidate && data.candidate.skills) {
      // Process skills data to conform to CandidateWithSkills interface
      const candidateData = { ...data.candidate };
      const coreSkills = data.candidate.skills.core || [];
      const secondarySkills = data.candidate.skills.secondary || [];

      // Flatten and enhance skills for the frontend, adding skill_type to distinguish between core and secondary
      const allSkills = [
        ...coreSkills.map((skill) => ({
          ...skill,
          skill_type: "core",
          level:
            skill.level ||
            (skill.proficiency === "Expert"
              ? 9
              : skill.proficiency === "Advanced"
              ? 7
              : skill.proficiency === "Intermediate"
              ? 5
              : 3),
          years: skill.years || skill.experience_years || 0,
        })),
        ...secondarySkills.map((skill) => ({
          ...skill,
          skill_type: "secondary",
          level:
            skill.level ||
            (skill.proficiency === "Expert"
              ? 9
              : skill.proficiency === "Advanced"
              ? 7
              : skill.proficiency === "Intermediate"
              ? 5
              : 3),
          years: skill.years || skill.experience_years || 0,
        })),
      ];

      // Return processed data
      return {
        ...candidateData,
        skills: allSkills,
      };
    }

    // Handle legacy structure (for backward compatibility)
    return {
      ...data.candidate,
      skills: data.skills || [],
    };
  },

  // Update candidate profile - Updated to match new backend endpoint
  async updateResume(resumeId: string, resumeData: any): Promise<any> {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    if (!token) {
      throw new Error("You must be logged in to update a resume");
    }

    const response = await fetch(`${API_BASE_URL}/candidates/${resumeId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(resumeData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to update resume");
    }

    return response.json();
  },

  // Upload new resume
  async uploadResume(resumeData: any): Promise<any> {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");

    if (!token) {
      throw new Error("You must be logged in to upload a resume");
    }

    const response = await fetch(`${API_BASE_URL}/candidates/resume/upload`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(resumeData),
    });

    // Get the response content
    const responseText = await response.text();
    let parsedResponse;

    try {
      // Try to parse as JSON
      parsedResponse = responseText ? JSON.parse(responseText) : {};
    } catch (e) {
      console.error("Error parsing response:", e);
      parsedResponse = { error: responseText || "Unknown error" };
    }

    if (!response.ok) {
      console.error("Upload resume failed:", response.status, parsedResponse);
      throw new Error(
        parsedResponse.error ||
          "Failed to upload resume. Server returned status: " + response.status
      );
    }

    return parsedResponse;
  },

  // Update job posting
  async updateJob(jobId: string, jobData: any): Promise<any> {
    const token = localStorage.getItem("accessToken");
    if (!token) throw new Error("Authentication required");

    // Format job data to match backend expectations
    const formattedJobData = {
      ...jobData,
      // Convert responsibilities and qualifications arrays to strings if they're not already
      responsibilities: Array.isArray(jobData.responsibilities)
        ? jobData.responsibilities
        : [],
      qualifications: Array.isArray(jobData.qualifications)
        ? jobData.qualifications
        : [],
      // Make sure summary is mapped to description for the backend
      description: jobData.summary,
      // Ensure domain is included
      domain: jobData.domain,
      // Format skills for the new API structure
      skills: {
        primary: jobData.primary_skills || [],
        secondary: jobData.secondary_skills || [],
      },
    };

    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(formattedJobData),
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
      // Get authentication token
      const token = localStorage.getItem("accessToken");
      if (!token) {
        throw new Error("Authentication required to fetch candidate matches");
      }

      const response = await fetch(
        `${API_BASE_URL}/candidates/${resumeId}/jobs?limit=${limit}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response for job matches:", errorText);
        throw new Error("Failed to fetch matching jobs");
      }
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
      // Get authentication token
      const token = localStorage.getItem("accessToken");
      if (!token) {
        throw new Error("Authentication required to fetch candidate matches");
      }

      const url = new URL(
        `${API_BASE_URL}/candidates/${resumeId}/jobs/enhanced`
      );
      url.searchParams.append("limit", limit.toString());
      url.searchParams.append("skills_weight", skillsWeight.toString());
      url.searchParams.append("location_weight", locationWeight.toString());
      url.searchParams.append("semantic_weight", semanticWeight.toString());

      console.log("Fetching enhanced job matches with authentication");
      const response = await fetch(url.toString(), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      console.log("Enhanced job matches response status:", response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response for job matches:", errorText);
        throw new Error("Failed to fetch enhanced job matches");
      }
      const data = await response.json();
      console.log("Job matches found:", data ? data.length : 0);
      return data;
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
      `${API_BASE_URL}/analytics/skill-gap/${candidateId}/${jobId}`,
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

  // Recommendations - Updated to match new backend endpoint
  async getSkillRecommendations(
    resumeId: string,
    jobId: string,
    count = 5
  ): Promise<SkillRecommendation[]> {
    const token = localStorage.getItem("accessToken");
    if (!token) throw new Error("Authentication required");

    const response = await fetch(
      `${API_BASE_URL}/analytics/recommendations/${resumeId}/${jobId}?limit=${count}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch skill recommendations");
    }

    return response.json();
  },

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

  // Authentication methods
  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Login failed");
    }

    return response.json();
  },

  async register(userData: any) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Registration failed");
    }

    return response.json();
  },

  async getUserProfile() {
    const token = localStorage.getItem("accessToken");
    if (!token) throw new Error("Not authenticated");

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to get user profile");
    }

    return response.json();
  },
};
