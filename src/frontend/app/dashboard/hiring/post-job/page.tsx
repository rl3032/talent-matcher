"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../../components/Layout";

interface Skill {
  skill_id: string;
  name: string;
  category: string;
  level?: number;
  proficiency?: string;
  importance?: number;
}

export default function PostJob() {
  const { user, loading } = useAuth();
  const router = useRouter();

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

  // Redirect if not logged in or not a hiring manager or admin
  useEffect(() => {
    if (
      !loading &&
      (!user || (user.role !== "hiring_manager" && user.role !== "admin"))
    ) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Set company name from user data
  useEffect(() => {
    if (user) {
      setCompany(user.name);
    }
  }, [user]);

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
      description: summary,
      responsibilities: responsibilitiesArray,
      qualifications: qualificationsArray,
      salary_range: salaryRange || "Competitive",
      skills: {
        primary: primarySkills.map((skill) => ({
          skill_id: skill.skill_id,
          proficiency: skill.proficiency || "Intermediate",
          importance: skill.importance || 0.7,
        })),
        secondary: secondarySkills.map((skill) => ({
          skill_id: skill.skill_id,
          proficiency: skill.proficiency || "Beginner",
          importance: skill.importance || 0.4,
        })),
      },
    };

    try {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        setError("You must be logged in to post a job");
        setSubmitting(false);
        return;
      }

      const response = await fetch("/api/jobs/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(jobData),
      });

      const data = await response.json();

      if (response.ok) {
        // Navigate to the job page
        router.push(`/jobs/${data.job_id}`);
      } else {
        setError(data.error || "Failed to create job. Please try again.");
      }
    } catch (error) {
      console.error("Error creating job:", error);
      setError("An error occurred. Please try again.");
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

  return (
    <Layout>
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Post a New Job
        </h1>

        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="title">
                Job Title*
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="company">
                Company*
              </label>
              <input
                id="company"
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100"
                readOnly
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="location">
                Location*
              </label>
              <input
                id="location"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                placeholder="e.g. New York, NY"
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="domain">
                Domain*
              </label>
              <select
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select Domain</option>
                <option value="software_development">
                  Software Development
                </option>
                <option value="data_science">Data Science</option>
                <option value="web_development">Web Development</option>
                <option value="cybersecurity">Cybersecurity</option>
                <option value="design">Design</option>
                <option value="marketing">Marketing</option>
                <option value="finance">Finance</option>
                <option value="healthcare">Healthcare</option>
                <option value="education">Education</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="jobType">
                Job Type
              </label>
              <select
                id="jobType"
                value={jobType}
                onChange={(e) => setJobType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
                <option value="Temporary">Temporary</option>
                <option value="Internship">Internship</option>
              </select>
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="salaryRange">
                Salary Range
              </label>
              <input
                id="salaryRange"
                type="text"
                value={salaryRange}
                onChange={(e) => setSalaryRange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. $80,000 - $100,000/year"
              />
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 mb-2" htmlFor="summary">
              Job Summary*
            </label>
            <textarea
              id="summary"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              required
            />
          </div>

          <div className="mb-6">
            <label
              className="block text-gray-700 mb-2"
              htmlFor="responsibilities"
            >
              Responsibilities* (one per line)
            </label>
            <textarea
              id="responsibilities"
              value={responsibilities}
              onChange={(e) => setResponsibilities(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={5}
              required
              placeholder="Lead and manage a team of software engineers&#10;Design and implement complex software systems&#10;Collaborate with stakeholders to define requirements"
            />
          </div>

          <div className="mb-6">
            <label
              className="block text-gray-700 mb-2"
              htmlFor="qualifications"
            >
              Qualifications* (one per line)
            </label>
            <textarea
              id="qualifications"
              value={qualifications}
              onChange={(e) => setQualifications(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={5}
              required
              placeholder="Bachelor's degree in Computer Science or related field&#10;5+ years of experience in software development&#10;Strong knowledge of JavaScript and React"
            />
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4">Required Skills</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
              <div>
                <label
                  className="block text-gray-700 mb-2"
                  htmlFor="selectedSkill"
                >
                  Skill
                </label>
                <select
                  id="selectedSkill"
                  value={selectedSkill}
                  onChange={(e) => setSelectedSkill(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loadingSkills}
                >
                  <option value="">Select a skill</option>
                  {availableSkills.map((skill) => (
                    <option key={skill.skill_id} value={skill.skill_id}>
                      {skill.name} ({skill.category})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  className="block text-gray-700 mb-2"
                  htmlFor="skillProficiency"
                >
                  Proficiency
                </label>
                <select
                  id="skillProficiency"
                  value={skillProficiency}
                  onChange={(e) => setSkillProficiency(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Beginner">Beginner</option>
                  <option value="Intermediate">Intermediate</option>
                  <option value="Advanced">Advanced</option>
                  <option value="Expert">Expert</option>
                </select>
              </div>

              <div>
                <label
                  className="block text-gray-700 mb-2"
                  htmlFor="skillImportance"
                >
                  Importance: {skillImportance}%
                </label>
                <input
                  id="skillImportance"
                  type="range"
                  min="10"
                  max="100"
                  step="10"
                  value={skillImportance}
                  onChange={(e) => setSkillImportance(parseInt(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>

            <div className="flex space-x-4 mb-6">
              <button
                type="button"
                onClick={addPrimarySkill}
                disabled={!selectedSkill}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Add as Primary Skill
              </button>
              <button
                type="button"
                onClick={addSecondarySkill}
                disabled={!selectedSkill}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
              >
                Add as Secondary Skill
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-2">Primary Skills</h3>
                {primarySkills.length > 0 ? (
                  <ul className="space-y-2">
                    {primarySkills.map((skill) => (
                      <li
                        key={skill.skill_id}
                        className="flex justify-between items-center p-2 bg-blue-50 rounded"
                      >
                        <div>
                          <span className="font-medium">{skill.name}</span>
                          <span className="ml-2 text-sm text-gray-600">
                            ({skill.proficiency})
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeSkill(skill.skill_id, true)}
                          className="text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No primary skills added</p>
                )}
              </div>

              <div>
                <h3 className="font-medium mb-2">Secondary Skills</h3>
                {secondarySkills.length > 0 ? (
                  <ul className="space-y-2">
                    {secondarySkills.map((skill) => (
                      <li
                        key={skill.skill_id}
                        className="flex justify-between items-center p-2 bg-gray-50 rounded"
                      >
                        <div>
                          <span className="font-medium">{skill.name}</span>
                          <span className="ml-2 text-sm text-gray-600">
                            ({skill.proficiency})
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeSkill(skill.skill_id, false)}
                          className="text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500">No secondary skills added</p>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {submitting ? "Posting..." : "Post Job"}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
