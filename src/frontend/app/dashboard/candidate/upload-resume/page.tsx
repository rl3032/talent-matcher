"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../../components/Layout";
import { apiClient } from "../../../../lib/api";

interface Skill {
  skill_id: string;
  name: string;
  category: string;
  level?: number;
  proficiency?: string;
  experience_years?: number;
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

export default function UploadResume() {
  const { user, loading, updateUser } = useAuth();
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

  // Redirect if not logged in or not a candidate
  useEffect(() => {
    if (!loading && (!user || user.role !== "candidate")) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Set name and email from user data
  useEffect(() => {
    if (user) {
      setName(user.name);
      setEmail(user.email);
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
      experiences.length === 0 ||
      educations.length === 0 ||
      coreSkills.length === 0
    ) {
      setError(
        "Please fill in all required fields and add at least one experience, education, and core skill"
      );
      setSubmitting(false);
      return;
    }

    // Format education data to match backend expectations
    const formattedEducations = educations.map((edu) => ({
      institution: edu.institution,
      degree: edu.degree,
      field: edu.degree, // Use degree as field if no specific field is available
      start_date: `${edu.graduation_year - 4}-09-01`, // Estimate 4 years before graduation
      end_date: `${edu.graduation_year}-06-01`, // Use graduation year for end date
      gpa: null,
    }));

    // Format experience data to match backend expectations
    const formattedExperiences = experiences.map((exp) => ({
      title: exp.job_title, // Map job_title to title
      company: exp.company,
      start_date: exp.start_date,
      end_date: exp.end_date,
      description: exp.description,
      skills_used: exp.skills_used,
    }));

    // Prepare resume data
    const resumeData = {
      name,
      email,
      phone,
      location,
      title,
      summary,
      education: formattedEducations,
      experience: formattedExperiences,
      certifications,
      languages,
      skills: {
        core: coreSkills,
        secondary: secondarySkills,
        domain,
      },
    };

    try {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        setError("You must be logged in to upload a resume");
        setSubmitting(false);
        return;
      }

      console.log(
        "Submitting resume data with",
        `${coreSkills.length} core skills, `,
        `${secondarySkills.length} secondary skills, `,
        `${formattedExperiences.length} experiences, `,
        `${formattedEducations.length} education entries`
      );

      try {
        const data = await apiClient.uploadResume(resumeData);

        console.log("Resume upload successful:", data);

        // Update user profile with resume ID
        updateUser({ profile_id: data.resume_id });
        // Navigate to the candidate dashboard
        router.push("/dashboard/candidate");
      } catch (apiError: any) {
        console.error("Resume upload failed:", apiError);
        setError(
          apiError.message || "Failed to upload resume. Please try again."
        );
      }
    } catch (error) {
      console.error("Error uploading resume:", error);
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
          Upload Your Resume
        </h1>

        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <h2 className="text-xl font-semibold mb-4">Personal Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="name">
                Full Name*
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100"
                readOnly
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="email">
                Email*
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-100"
                readOnly
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="phone">
                Phone
              </label>
              <input
                id="phone"
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. +1-234-567-8901"
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
              <label className="block text-gray-700 mb-2" htmlFor="title">
                Professional Title*
              </label>
              <input
                id="title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
                placeholder="e.g. Full Stack Developer"
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="domain">
                Domain
              </label>
              <select
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                <option value="general">General</option>
              </select>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 mb-2" htmlFor="summary">
              Professional Summary*
            </label>
            <textarea
              id="summary"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              required
              placeholder="Write a brief summary of your professional background, skills, and career objectives."
            />
          </div>

          <h2 className="text-xl font-semibold mb-4">Education</h2>
          <div className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
              <div>
                <label className="block text-gray-700 mb-2" htmlFor="degree">
                  Degree
                </label>
                <input
                  id="degree"
                  type="text"
                  value={degree}
                  onChange={(e) => setDegree(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Bachelor of Science in Computer Science"
                />
              </div>

              <div>
                <label
                  className="block text-gray-700 mb-2"
                  htmlFor="institution"
                >
                  Institution
                </label>
                <input
                  id="institution"
                  type="text"
                  value={institution}
                  onChange={(e) => setInstitution(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Stanford University"
                />
              </div>

              <div>
                <label
                  className="block text-gray-700 mb-2"
                  htmlFor="graduationYear"
                >
                  Graduation Year
                </label>
                <input
                  id="graduationYear"
                  type="number"
                  value={graduationYear}
                  onChange={(e) => setGraduationYear(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min={1950}
                  max={2100}
                />
              </div>
            </div>

            <button
              type="button"
              onClick={addEducation}
              disabled={!degree || !institution || !graduationYear}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              Add Education
            </button>

            {educations.length > 0 && (
              <div className="mt-4">
                <h3 className="font-medium mb-2">Added Education</h3>
                <ul className="space-y-2">
                  {educations.map((edu, index) => (
                    <li
                      key={index}
                      className="flex justify-between items-center p-2 bg-gray-50 rounded"
                    >
                      <div>
                        <span className="font-medium">{edu.degree}</span>
                        <span className="text-sm text-gray-600">
                          {" "}
                          at {edu.institution} ({edu.graduation_year})
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeEducation(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <h2 className="text-xl font-semibold mb-4">Work Experience</h2>
          <div className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
              <div>
                <label className="block text-gray-700 mb-2" htmlFor="jobTitle">
                  Job Title
                </label>
                <input
                  id="jobTitle"
                  type="text"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Senior Software Engineer"
                />
              </div>

              <div>
                <label className="block text-gray-700 mb-2" htmlFor="company">
                  Company
                </label>
                <input
                  id="company"
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. Google"
                />
              </div>

              <div>
                <label className="block text-gray-700 mb-2" htmlFor="startDate">
                  Start Date
                </label>
                <input
                  id="startDate"
                  type="text"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 2018-01 or Jan 2018"
                />
              </div>

              <div>
                <label className="block text-gray-700 mb-2" htmlFor="endDate">
                  End Date
                </label>
                <input
                  id="endDate"
                  type="text"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 2020-12, Present, or Dec 2020"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="description">
                Job Description (one responsibility per line)
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
                placeholder="Developed full-stack web applications using React&#10;Led a team of 5 developers on a major project&#10;Improved application performance by 40%"
              />
            </div>

            <div className="mb-4">
              <label className="block text-gray-700 mb-2" htmlFor="skillsUsed">
                Skills Used (comma separated)
              </label>
              <input
                id="skillsUsed"
                type="text"
                value={skillsUsed}
                onChange={(e) => setSkillsUsed(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g. JavaScript, React, Node.js, AWS"
              />
            </div>

            <button
              type="button"
              onClick={addExperience}
              disabled={
                !jobTitle || !company || !startDate || !endDate || !description
              }
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              Add Experience
            </button>

            {experiences.length > 0 && (
              <div className="mt-4">
                <h3 className="font-medium mb-2">Added Experiences</h3>
                <ul className="space-y-4">
                  {experiences.map((exp, index) => (
                    <li key={index} className="p-3 bg-gray-50 rounded">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">
                            {exp.job_title} at {exp.company}
                          </div>
                          <div className="text-sm text-gray-600">
                            {exp.start_date} - {exp.end_date}
                          </div>
                          <ul className="mt-2 list-disc list-inside text-sm text-gray-700">
                            {exp.description.map((desc, i) => (
                              <li key={i}>{desc}</li>
                            ))}
                          </ul>
                          {exp.skills_used && exp.skills_used.length > 0 && (
                            <div className="mt-2 text-sm">
                              <span className="font-medium">Skills: </span>
                              {exp.skills_used.join(", ")}
                            </div>
                          )}
                        </div>
                        <button
                          type="button"
                          onClick={() => removeExperience(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <h2 className="text-xl font-semibold mb-4">Skills</h2>
          <div className="mb-6">
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
                  htmlFor="skillYears"
                >
                  Years of Experience
                </label>
                <input
                  id="skillYears"
                  type="number"
                  value={skillYears}
                  onChange={(e) => setSkillYears(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min={0.1}
                  max={20}
                  step={0.1}
                />
              </div>
            </div>

            <div className="flex space-x-4 mb-6">
              <button
                type="button"
                onClick={addCoreSkill}
                disabled={!selectedSkill}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                Add as Core Skill
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
                <h3 className="font-medium mb-2">Core Skills</h3>
                {coreSkills.length > 0 ? (
                  <ul className="space-y-2">
                    {coreSkills.map((skill) => (
                      <li
                        key={skill.skill_id}
                        className="flex justify-between items-center p-2 bg-blue-50 rounded"
                      >
                        <div>
                          <span className="font-medium">{skill.name}</span>
                          <span className="ml-2 text-sm text-gray-600">
                            ({skill.proficiency}, {skill.experience_years}{" "}
                            years)
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
                  <p className="text-gray-500">No core skills added</p>
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
                            ({skill.proficiency}, {skill.experience_years}{" "}
                            years)
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

          <h2 className="text-xl font-semibold mb-4">Additional Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label
                className="block text-gray-700 mb-2"
                htmlFor="certification"
              >
                Certifications
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  id="certification"
                  type="text"
                  value={certification}
                  onChange={(e) => setCertification(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. AWS Certified Developer"
                />
                <button
                  type="button"
                  onClick={addCertification}
                  disabled={!certification}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  Add
                </button>
              </div>
              {certifications.length > 0 ? (
                <ul className="space-y-2">
                  {certifications.map((cert, index) => (
                    <li
                      key={index}
                      className="flex justify-between items-center p-2 bg-gray-50 rounded"
                    >
                      <span>{cert}</span>
                      <button
                        type="button"
                        onClick={() => removeCertification(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No certifications added</p>
              )}
            </div>

            <div>
              <label className="block text-gray-700 mb-2" htmlFor="language">
                Languages
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  id="language"
                  type="text"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. English (Native), Spanish (Fluent)"
                />
                <button
                  type="button"
                  onClick={addLanguage}
                  disabled={!language}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                >
                  Add
                </button>
              </div>
              {languages.length > 0 ? (
                <ul className="space-y-2">
                  {languages.map((lang, index) => (
                    <li
                      key={index}
                      className="flex justify-between items-center p-2 bg-gray-50 rounded"
                    >
                      <span>{lang}</span>
                      <button
                        type="button"
                        onClick={() => removeLanguage(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No languages added</p>
              )}
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {submitting ? "Uploading..." : "Upload Resume"}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
