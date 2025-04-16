"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../../components/Layout";
import { apiClient } from "../../../../lib/api";
import { CandidateWithSkills, CandidateSkill } from "../../../../types";

interface Skill {
  skill_id: string;
  name: string;
  category: string;
  level?: number;
  proficiency?: string;
  experience_years?: number;
  years?: number;
  is_primary?: boolean;
}

interface Education {
  degree: string;
  institution: string;
  graduation_year: number;
}

interface Experience {
  job_title: string;
  company: string;
  start_date: string;
  end_date: string;
  description: string[];
  skills_used?: string[];
}

export default function EditResume() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Resume form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [domain, setDomain] = useState("");

  // Education state
  const [educations, setEducations] = useState<Education[]>([]);
  const [degree, setDegree] = useState("");
  const [institution, setInstitution] = useState("");
  const [graduationYear, setGraduationYear] = useState<number>(
    new Date().getFullYear()
  );

  // Experience state
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [description, setDescription] = useState("");
  const [skillsUsed, setSkillsUsed] = useState("");

  // Skills state
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [coreSkills, setCoreSkills] = useState<Skill[]>([]);
  const [secondarySkills, setSecondarySkills] = useState<Skill[]>([]);
  const [selectedSkill, setSelectedSkill] = useState("");
  const [skillProficiency, setSkillProficiency] = useState("Intermediate");
  const [skillYears, setSkillYears] = useState(1);

  // Certifications and Languages
  const [certifications, setCertifications] = useState<string[]>([]);
  const [certification, setCertification] = useState("");
  const [languages, setLanguages] = useState<string[]>([]);
  const [language, setLanguage] = useState("");

  // Form state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingSkills, setLoadingSkills] = useState(true);
  const [loadingResume, setLoadingResume] = useState(true);

  // Redirect if not logged in or not a candidate
  useEffect(() => {
    if (!loading && (!user || user.role !== "candidate")) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Fetch user's resume data
  useEffect(() => {
    const fetchResumeData = async () => {
      if (user?.profile_id) {
        try {
          setLoadingResume(true);
          const candidateData = await apiClient.getCandidate(user.profile_id);

          // Set basic information
          setName(candidateData.name || "");
          setEmail(candidateData.email || "");
          // Phone may not be in the API response
          if ("phone" in candidateData) {
            setPhone((candidateData.phone as string) || "");
          }
          setLocation(candidateData.location || "");
          setTitle(candidateData.title || "");
          setSummary(candidateData.summary || "");
          setDomain(candidateData.domain || "");

          // Set skills
          if (candidateData.skills && candidateData.skills.length > 0) {
            // Filter primary and secondary skills - handle possible missing is_primary
            const primarySkills = candidateData.skills.filter(
              (s) => "is_primary" in s && s.is_primary === true
            );
            const secondarySkills = candidateData.skills.filter(
              (s) => !("is_primary" in s) || s.is_primary !== true
            );
            setCoreSkills(primarySkills);
            setSecondarySkills(secondarySkills);
          }

          // Set education - map to match our Education interface
          if (candidateData.education) {
            setEducations(
              candidateData.education.map((edu) => ({
                degree: edu.degree || "",
                institution: edu.institution || "",
                graduation_year: edu.year
                  ? parseInt(edu.year)
                  : new Date().getFullYear(),
              }))
            );
          }

          // Set experience - map to match our Experience interface
          if (candidateData.experience) {
            setExperiences(
              candidateData.experience.map((exp) => ({
                job_title: exp.title || "",
                company: exp.company || "",
                start_date: exp.period ? exp.period.split(" - ")[0] : "",
                end_date: exp.period
                  ? exp.period.split(" - ")[1] || "Present"
                  : "",
                description: Array.isArray(exp.description)
                  ? exp.description
                  : [],
                skills_used: exp.skills ? exp.skills.map((s) => s.name) : [],
              }))
            );
          }

          // Set certifications and languages if available
          if (candidateData.certifications) {
            // Handle both string arrays and object arrays
            setCertifications(
              Array.isArray(candidateData.certifications)
                ? candidateData.certifications.map((cert: any) =>
                    typeof cert === "string"
                      ? cert
                      : `${cert.name || ""} - ${cert.issuer || ""}`
                  )
                : []
            );
          }

          if (candidateData.languages) {
            // Handle both string arrays and object arrays
            setLanguages(
              Array.isArray(candidateData.languages)
                ? candidateData.languages.map((lang: any) =>
                    typeof lang === "string" ? lang : lang.name || ""
                  )
                : []
            );
          }
        } catch (error) {
          console.error("Error fetching resume data:", error);
          setError("Failed to load your resume data. Please try again.");
        } finally {
          setLoadingResume(false);
        }
      }
    };

    fetchResumeData();
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

  // Handle adding education
  const addEducation = () => {
    if (!degree || !institution || !graduationYear) return;

    setEducations([
      ...educations,
      { degree, institution, graduation_year: graduationYear },
    ]);

    // Reset fields
    setDegree("");
    setInstitution("");
    setGraduationYear(new Date().getFullYear());
  };

  // Handle removing education
  const removeEducation = (index: number) => {
    setEducations(educations.filter((_, i) => i !== index));
  };

  // Handle adding experience
  const addExperience = () => {
    if (!jobTitle || !company || !startDate || !endDate || !description) return;

    // Process description and skills used
    const descriptionArray = description
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);

    const skillsUsedArray = skillsUsed
      .split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill.length > 0);

    setExperiences([
      ...experiences,
      {
        job_title: jobTitle,
        company,
        start_date: startDate,
        end_date: endDate,
        description: descriptionArray,
        skills_used: skillsUsedArray,
      },
    ]);

    // Reset fields
    setJobTitle("");
    setCompany("");
    setStartDate("");
    setEndDate("");
    setDescription("");
    setSkillsUsed("");
  };

  // Handle removing experience
  const removeExperience = (index: number) => {
    setExperiences(experiences.filter((_, i) => i !== index));
  };

  // Handle adding a core skill
  const addCoreSkill = () => {
    if (!selectedSkill) return;

    const skill = availableSkills.find((s) => s.skill_id === selectedSkill);
    if (!skill) return;

    // Check if skill is already added
    if (
      coreSkills.some((s) => s.skill_id === selectedSkill) ||
      secondarySkills.some((s) => s.skill_id === selectedSkill)
    ) {
      setError("This skill is already added to the resume");
      return;
    }

    const newSkill = {
      ...skill,
      level:
        skillProficiency === "Expert"
          ? 8
          : skillProficiency === "Advanced"
          ? 6
          : skillProficiency === "Intermediate"
          ? 4
          : 2,
      proficiency: skillProficiency,
      experience_years: skillYears,
      is_primary: true,
    };

    setCoreSkills([...coreSkills, newSkill]);
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
      coreSkills.some((s) => s.skill_id === selectedSkill) ||
      secondarySkills.some((s) => s.skill_id === selectedSkill)
    ) {
      setError("This skill is already added to the resume");
      return;
    }

    const newSkill = {
      ...skill,
      level:
        skillProficiency === "Expert"
          ? 8
          : skillProficiency === "Advanced"
          ? 6
          : skillProficiency === "Intermediate"
          ? 4
          : 2,
      proficiency: skillProficiency,
      experience_years: skillYears,
      is_primary: false,
    };

    setSecondarySkills([...secondarySkills, newSkill]);
    setSelectedSkill("");
    setError(null);
  };

  // Remove a skill
  const removeSkill = (skillId: string, isCore: boolean) => {
    if (isCore) {
      setCoreSkills(coreSkills.filter((s) => s.skill_id !== skillId));
    } else {
      setSecondarySkills(secondarySkills.filter((s) => s.skill_id !== skillId));
    }
  };

  // Handle adding certification
  const addCertification = () => {
    if (!certification) return;
    setCertifications([...certifications, certification]);
    setCertification("");
  };

  // Handle removing certification
  const removeCertification = (index: number) => {
    setCertifications(certifications.filter((_, i) => i !== index));
  };

  // Handle adding language
  const addLanguage = () => {
    if (!language) return;
    setLanguages([...languages, language]);
    setLanguage("");
  };

  // Handle removing language
  const removeLanguage = (index: number) => {
    setLanguages(languages.filter((_, i) => i !== index));
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    // Validate form
    if (
      !name ||
      !email ||
      !location ||
      !title ||
      !summary ||
      coreSkills.length === 0
    ) {
      setError(
        "Please fill in all required fields and add at least one core skill"
      );
      setSubmitting(false);
      return;
    }

    // Prepare resume data
    const resumeData = {
      name,
      email,
      phone,
      location,
      title,
      summary,
      domain,
      primary_skills: coreSkills,
      secondary_skills: secondarySkills,
      education: educations,
      experience: experiences,
      certifications,
      languages,
    };

    try {
      if (!user?.profile_id) {
        setError("User profile not found");
        setSubmitting(false);
        return;
      }

      await apiClient.updateResume(user.profile_id, resumeData);

      // Redirect to profile page on success
      router.push(`/candidates/${user.profile_id}`);
    } catch (error: any) {
      console.error("Error updating resume:", error);
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

  if (loadingResume) {
    return (
      <Layout>
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Edit Your Resume
          </h1>
          <div className="flex justify-center items-center py-10">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
            <span className="ml-3 text-gray-600">
              Loading your resume data...
            </span>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Edit Your Resume
        </h1>

        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Personal Information Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name*
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email*
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
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
                  placeholder="City, State, Country"
                />
              </div>
            </div>
          </div>

          {/* Professional Summary Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Professional Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Professional Title*
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  required
                  placeholder="e.g. Software Engineer"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Industry/Domain
                </label>
                <select
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
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
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Professional Summary*
              </label>
              <textarea
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                required
                placeholder="Write a concise summary of your professional background and goals"
              ></textarea>
            </div>
          </div>

          {/* Skills Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Skills</h2>

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
                    Proficiency
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
                    Years of Experience
                  </label>
                  <input
                    type="number"
                    value={skillYears}
                    onChange={(e) =>
                      setSkillYears(parseInt(e.target.value) || 0)
                    }
                    min="0"
                    max="30"
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={addCoreSkill}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                  disabled={!selectedSkill}
                >
                  Add as Core Skill
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

            {/* Core Skills Display */}
            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2">Core Skills</h3>
              {coreSkills.length === 0 ? (
                <p className="text-gray-500 italic">
                  No core skills added yet. These are your main professional
                  strengths.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {coreSkills.map((skill) => (
                    <div
                      key={skill.skill_id}
                      className="bg-blue-100 border border-blue-300 rounded-full px-3 py-1 flex items-center"
                    >
                      <span className="text-blue-800 mr-1">{skill.name}</span>
                      <span className="text-xs text-blue-600 mr-2">
                        ({skill.proficiency} - {skill.experience_years} yrs)
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
                  No secondary skills added yet. These are your additional
                  skills.
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
                        ({skill.proficiency} - {skill.experience_years} yrs)
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

          {/* Education Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Education</h2>

            {/* Education Form */}
            <div className="bg-gray-50 p-4 rounded mb-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Degree
                  </label>
                  <input
                    type="text"
                    value={degree}
                    onChange={(e) => setDegree(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. Bachelor of Science in Computer Science"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Institution
                  </label>
                  <input
                    type="text"
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. University of California"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Graduation Year
                  </label>
                  <input
                    type="number"
                    value={graduationYear}
                    onChange={(e) =>
                      setGraduationYear(parseInt(e.target.value) || 2023)
                    }
                    min="1950"
                    max="2050"
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <button
                type="button"
                onClick={addEducation}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                disabled={!degree || !institution || !graduationYear}
              >
                Add Education
              </button>
            </div>

            {/* Education Display */}
            <div>
              {educations.length === 0 ? (
                <p className="text-gray-500 italic">No education added yet.</p>
              ) : (
                <div className="space-y-3">
                  {educations.map((edu, index) => (
                    <div
                      key={index}
                      className="flex justify-between items-center p-3 border rounded"
                    >
                      <div>
                        <div className="font-medium">{edu.degree}</div>
                        <div className="text-sm text-gray-600">
                          {edu.institution}, {edu.graduation_year}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeEducation(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Experience Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">Work Experience</h2>

            {/* Experience Form */}
            <div className="bg-gray-50 p-4 rounded mb-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title
                  </label>
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. Software Engineer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company
                  </label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g. Google"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="month"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date
                  </label>
                  <input
                    type="month"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <p className="text-xs text-gray-500 mb-1">
                  Enter each point on a new line
                </p>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  rows={4}
                  placeholder="• Developed feature X that improved performance by Y%&#10;• Led a team of Z developers"
                ></textarea>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Skills Used
                </label>
                <p className="text-xs text-gray-500 mb-1">
                  Comma-separated list of skills
                </p>
                <input
                  type="text"
                  value={skillsUsed}
                  onChange={(e) => setSkillsUsed(e.target.value)}
                  className="w-full p-2 border rounded focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. Python, React, Docker"
                />
              </div>

              <button
                type="button"
                onClick={addExperience}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
                disabled={
                  !jobTitle ||
                  !company ||
                  !startDate ||
                  !endDate ||
                  !description
                }
              >
                Add Experience
              </button>
            </div>

            {/* Experience Display */}
            <div>
              {experiences.length === 0 ? (
                <p className="text-gray-500 italic">
                  No work experience added yet.
                </p>
              ) : (
                <div className="space-y-3">
                  {experiences.map((exp, index) => (
                    <div key={index} className="p-3 border rounded">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-medium">{exp.job_title}</div>
                          <div className="text-sm text-gray-600">
                            {exp.company} | {exp.start_date} to {exp.end_date}
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeExperience(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                      <ul className="list-disc ml-5 text-sm text-gray-700 mb-2">
                        {exp.description.map((desc, i) => (
                          <li key={i}>{desc}</li>
                        ))}
                      </ul>
                      {exp.skills_used && exp.skills_used.length > 0 && (
                        <div className="text-sm">
                          <span className="font-medium">Skills: </span>
                          {exp.skills_used.join(", ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Submission Button */}
          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
              disabled={submitting}
            >
              {submitting ? "Updating..." : "Update Resume"}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
