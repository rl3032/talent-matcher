"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../../../components/Layout";
import { apiClient } from "../../../../../lib/api";

interface Skill {
  skill_id: string;
  name: string;
  category: string;
  level?: number;
  proficiency?: string;
  importance?: number;
  is_primary?: boolean;
}

export default function EditJob({ params }: { params: { jobId: string } }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const jobId = params.jobId;

  // Job form state
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [location, setLocation] = useState("");
  const [domain, setDomain] = useState("");
  const [jobType, setJobType] = useState("Full-time");
  const [summary, setSummary] = useState("");
  const [responsibilities, setResponsibilities] = useState("");
  const [qualifications, setQualifications] = useState("");
  const [salaryRange, setSalaryRange] = useState("");

  // Skills state
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [primarySkills, setPrimarySkills] = useState<Skill[]>([]);
  const [secondarySkills, setSecondarySkills] = useState<Skill[]>([]);
  const [selectedSkill, setSelectedSkill] = useState("");
  const [skillProficiency, setSkillProficiency] = useState("Intermediate");
  const [skillImportance, setSkillImportance] = useState(70);

  // Form state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingSkills, setLoadingSkills] = useState(true);
  const [loadingJob, setLoadingJob] = useState(true);

  // Format a domain for display (convert snake_case to Title Case)
  const formatDomain = (domain: string): string => {
    if (!domain) return "";
    return domain
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Redirect if not logged in or not a hiring manager or admin
  useEffect(() => {
    if (
      !loading &&
      (!user || (user.role !== "hiring_manager" && user.role !== "admin"))
    ) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Fetch job data
  useEffect(() => {
    const fetchJobData = async () => {
      if (!jobId) return;

      try {
        setLoadingJob(true);
        const jobData = await apiClient.getJob(jobId);

        // Set basic information
        setTitle(jobData.title || "");
        setCompany(jobData.company || "");
        setLocation(jobData.location || "");
        setDomain(jobData.domain || "");
        setJobType(jobData.job_type || "Full-time");
        setSummary(jobData.summary || "");
        setSalaryRange(jobData.salary_range || "");

        // Set responsibilities and qualifications
        if (jobData.responsibilities) {
          setResponsibilities(jobData.responsibilities.join("\n"));
        }

        if (jobData.qualifications) {
          setQualifications(jobData.qualifications.join("\n"));
        }

        // Set skills
        if (jobData.skills && jobData.skills.length > 0) {
          const primary = jobData.skills.filter((s) => s.is_primary);
          const secondary = jobData.skills.filter((s) => !s.is_primary);
          setPrimarySkills(primary);
          setSecondarySkills(secondary);
        }
      } catch (error) {
        console.error("Error fetching job data:", error);
        setError("Failed to load job data. Please try again.");
      } finally {
        setLoadingJob(false);
      }
    };

    fetchJobData();
  }, [jobId]);

  // Fetch available skills
  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const response = await fetch("/api/skills");
        if (response.ok) {
          const data = await response.json();
          setAvailableSkills(data.skills || []);
        }
      } catch (error) {
        console.error("Error fetching skills:", error);
      }
      setLoadingSkills(false);
    };

    fetchSkills();
  }, []);

  // Handle adding a primary skill
  const addPrimarySkill = () => {
    if (!selectedSkill) return;

    const skill = availableSkills.find((s) => s.skill_id === selectedSkill);
    if (!skill) return;

    // Check if skill is already added
    if (
      primarySkills.some((s) => s.skill_id === selectedSkill) ||
      secondarySkills.some((s) => s.skill_id === selectedSkill)
    ) {
      setError("This skill is already added to the job");
      return;
    }

    const newSkill = {
      ...skill,
      level: Math.round(skillImportance / 10),
      proficiency: skillProficiency,
      importance: skillImportance / 100,
      is_primary: true,
    };

    setPrimarySkills([...primarySkills, newSkill]);
    setSelectedSkill("");
    setError(null);
  };

  // Handle adding a secondary skill
  const addSecondarySkill = () => {
    if (!selectedSkill) return;

    const skill = availableSkills.find((s) => s.skill_id === selectedSkill);
    if (!skill) return;

    // Check if skill is already added
    if (
      primarySkills.some((s) => s.skill_id === selectedSkill) ||
      secondarySkills.some((s) => s.skill_id === selectedSkill)
    ) {
      setError("This skill is already added to the job");
      return;
    }

    const newSkill = {
      ...skill,
      level: Math.round(skillImportance / 10),
      proficiency: skillProficiency,
      importance: skillImportance / 100,
      is_primary: false,
    };

    setSecondarySkills([...secondarySkills, newSkill]);
    setSelectedSkill("");
    setError(null);
  };

  // Remove a skill
  const removeSkill = (skillId: string, isPrimary: boolean) => {
    if (isPrimary) {
      setPrimarySkills(primarySkills.filter((s) => s.skill_id !== skillId));
    } else {
      setSecondarySkills(secondarySkills.filter((s) => s.skill_id !== skillId));
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    // Validate form
    if (
      !title ||
      !company ||
      !location ||
      !domain ||
      !summary ||
      !responsibilities ||
      !qualifications ||
      primarySkills.length === 0
    ) {
      setError(
        "Please fill in all required fields and add at least one primary skill"
      );
      setSubmitting(false);
      return;
    }

    // Process responsibilities and qualifications as arrays
    const responsibilitiesArray = responsibilities
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    const qualificationsArray = qualifications
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    // Prepare job data
    const jobData = {
      title,
      company,
      location,
      domain,
      job_type: jobType,
      summary,
      responsibilities: responsibilitiesArray,
      qualifications: qualificationsArray,
      salary_range: salaryRange || "Competitive",
      primary_skills: primarySkills,
      secondary_skills: secondarySkills,
    };

    try {
      await apiClient.updateJob(jobId, jobData);

      // Navigate to the job page
      router.push(`/jobs/${jobId}`);
    } catch (error: any) {
      console.error("Error updating job:", error);
      setError(error.message || "An error occurred. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !user) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  if (loadingJob) {
    return (
      <Layout>
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Edit Job Posting
          </h1>
          <div className="flex justify-center items-center py-10">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
            <span className="ml-3 text-gray-600">Loading job data...</span>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Edit Job Posting
        </h1>

        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Job Title*
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                required
                placeholder="e.g. Senior Software Engineer"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company*
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location*
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                required
                placeholder="e.g. San Francisco, CA"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Industry/Domain*
              </label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select Domain</option>
                <option value="technology">Technology</option>
                <option value="healthcare">Healthcare</option>
                <option value="finance">Finance</option>
                <option value="education">Education</option>
                <option value="manufacturing">Manufacturing</option>
                <option value="retail">Retail</option>
                <option value="marketing">Marketing</option>
                <option value="consulting">Consulting</option>
                <option value="government">Government</option>
                <option value="nonprofit">Nonprofit</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Job Type
              </label>
              <select
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
                <option value="Temporary">Temporary</option>
                <option value="Internship">Internship</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Salary Range
              </label>
              <input
                type="text"
                value={salaryRange}
                onChange={(e) => setSalaryRange(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g. $100,000 - $130,000"
              />
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Job Summary*
            </label>
            <textarea
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              rows={4}
              required
              placeholder="Provide a brief overview of the job and your company..."
            ></textarea>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Responsibilities*
            </label>
            <p className="text-xs text-gray-500 mb-1">
              Enter each responsibility on a new line
            </p>
            <textarea
              value={responsibilities}
              onChange={(e) => setResponsibilities(e.target.value)}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              rows={6}
              required
              placeholder="• Design and develop software applications&#10;• Collaborate with cross-functional teams&#10;• Debug and fix issues in existing systems"
            ></textarea>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Qualifications*
            </label>
            <p className="text-xs text-gray-500 mb-1">
              Enter each qualification on a new line
            </p>
            <textarea
              value={qualifications}
              onChange={(e) => setQualifications(e.target.value)}
              className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
              rows={6}
              required
              placeholder="• Bachelor's degree in Computer Science or related field&#10;• 3+ years of experience with JavaScript and React&#10;• Excellent communication skills"
            ></textarea>
          </div>

          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Skills Required</h2>

            {/* Skill Selection Form */}
            <div className="bg-gray-50 p-4 rounded mb-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Skill
                  </label>
                  <select
                    value={selectedSkill}
                    onChange={(e) => setSelectedSkill(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                    disabled={loadingSkills}
                  >
                    <option value="">Select a skill</option>
                    {availableSkills.map((skill) => (
                      <option key={skill.skill_id} value={skill.skill_id}>
                        {skill.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Proficiency Required
                  </label>
                  <select
                    value={skillProficiency}
                    onChange={(e) => setSkillProficiency(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="Beginner">Beginner</option>
                    <option value="Intermediate">Intermediate</option>
                    <option value="Advanced">Advanced</option>
                    <option value="Expert">Expert</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Importance (%)
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="10"
                    value={skillImportance}
                    onChange={(e) =>
                      setSkillImportance(parseInt(e.target.value))
                    }
                    className="w-full"
                  />
                  <div className="text-sm text-center">{skillImportance}%</div>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={addPrimarySkill}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                  disabled={!selectedSkill}
                >
                  Add as Primary Skill
                </button>
                <button
                  type="button"
                  onClick={addSecondarySkill}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:bg-gray-300"
                  disabled={!selectedSkill}
                >
                  Add as Secondary Skill
                </button>
              </div>
            </div>

            {/* Primary Skills Display */}
            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2">Primary Skills</h3>
              {primarySkills.length === 0 ? (
                <p className="text-gray-500 italic">
                  No primary skills added yet. These are the most important
                  skills for the job.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {primarySkills.map((skill) => (
                    <div
                      key={skill.skill_id}
                      className="bg-blue-100 border border-blue-300 rounded-full px-3 py-1 flex items-center"
                    >
                      <span className="text-blue-800 mr-1">{skill.name}</span>
                      <span className="text-xs text-blue-600 mr-2">
                        ({skill.proficiency} -{" "}
                        {Math.round((skill.importance || 0) * 100)}%)
                      </span>
                      <button
                        type="button"
                        onClick={() => removeSkill(skill.skill_id, true)}
                        className="text-blue-700 hover:text-blue-900"
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Secondary Skills Display */}
            <div>
              <h3 className="text-lg font-medium mb-2">Secondary Skills</h3>
              {secondarySkills.length === 0 ? (
                <p className="text-gray-500 italic">
                  No secondary skills added yet. These are nice-to-have skills.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {secondarySkills.map((skill) => (
                    <div
                      key={skill.skill_id}
                      className="bg-gray-100 border border-gray-300 rounded-full px-3 py-1 flex items-center"
                    >
                      <span className="text-gray-800 mr-1">{skill.name}</span>
                      <span className="text-xs text-gray-600 mr-2">
                        ({skill.proficiency} -{" "}
                        {Math.round((skill.importance || 0) * 100)}%)
                      </span>
                      <button
                        type="button"
                        onClick={() => removeSkill(skill.skill_id, false)}
                        className="text-gray-700 hover:text-gray-900"
                      >
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              disabled={submitting}
            >
              {submitting ? "Updating..." : "Update Job"}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
