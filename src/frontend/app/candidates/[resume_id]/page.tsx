"use client";

import React, { useState, useEffect } from "react";
import Layout from "../../../components/Layout";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "../../../lib/api";
import { CandidateWithSkills, MatchResult } from "../../../types";
import SkillTag from "../../../components/SkillTag";
import { useAuth } from "../../../lib/AuthContext";

interface ExperienceItem {
  company: string;
  title: string;
  period?: string;
  description: string | string[];
  skills?: {
    skill_id: string;
    name: string;
    category: string;
  }[];
  start_date?: string;
  end_date?: string;
}

interface EducationItem {
  institution: string;
  degree: string;
  field: string;
  year: string;
}

interface CertificationItem {
  name: string;
  issuer: string;
  date: string;
}

type Props = {
  params: {
    resume_id: string;
  };
};

export default function CandidateDetailPage({ params }: Props) {
  const { resume_id } = params;
  const { user } = useAuth();
  const [candidate, setCandidate] = useState<CandidateWithSkills | null>(null);
  const [matchingJobs, setMatchingJobs] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unauthorized, setUnauthorized] = useState(false);

  // Format a value for display (convert snake_case to Title Case)
  const formatForDisplay = (value: string): string => {
    if (!value) return "";
    return value
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Format date string for display
  const formatDate = (dateStr: string): string => {
    if (dateStr === "Present") return dateStr;

    // Format YYYY-MM to MMM YYYY
    const parts = dateStr.split("-");
    if (parts.length >= 2) {
      const year = parts[0];
      const month = new Date(`${year}-${parts[1]}-01`).toLocaleString(
        "default",
        { month: "short" }
      );
      return `${month} ${year}`;
    }
    return dateStr;
  };

  useEffect(() => {
    const fetchCandidateDetails = async () => {
      try {
        setLoading(true);
        // Fetch candidate details
        const candidateData = await apiClient.getCandidate(resume_id as string);

        // Ensure the skills array exists and has skill_type for backward compatibility
        if (!candidateData.skills) {
          candidateData.skills = [];
        } else {
          // For backward compatibility with existing data that doesn't have skill_type
          candidateData.skills = candidateData.skills.map((skill) => ({
            ...skill,
            skill_type: skill.skill_type || "core", // Default to core if not specified
          }));
        }

        setCandidate(candidateData);

        // Fetch matching jobs using enhanced matching
        const jobsData = await apiClient.getCandidateMatchesEnhanced(
          resume_id as string,
          {
            limit: 10,
            skillsWeight: 0.75,
            locationWeight: 0.15,
            semanticWeight: 0.1,
          }
        );
        setMatchingJobs(jobsData);

        setError(null);
        setUnauthorized(false);
      } catch (err: any) {
        console.error("Error fetching candidate details:", err);
        // Check if this is an authorization error
        if (
          err.message === "Failed to fetch candidate details" &&
          (!user ||
            (user.role === "candidate" && user.profile_id !== resume_id))
        ) {
          setUnauthorized(true);
          setError(
            "You do not have permission to view this candidate's profile"
          );
        } else {
          setError("Failed to load candidate details. Please try again later.");
        }
      } finally {
        setLoading(false);
      }
    };

    if (resume_id) {
      fetchCandidateDetails();
    }
  }, [resume_id, user]);

  return (
    <Layout>
      <div className="py-8">
        <div className="max-w-4xl mx-auto px-4">
          {/* Back button */}
          <div className="mb-6">
            <Link
              href={
                user && user.role === "candidate"
                  ? "/dashboard/candidate"
                  : "/candidates"
              }
              className="text-blue-600 hover:text-blue-800"
            >
              {user && user.role === "candidate"
                ? "← Back to Dashboard"
                : "← Back to Candidates"}
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-10">
              <p className="text-gray-500">Loading candidate details...</p>
            </div>
          ) : error ? (
            <div className="text-center py-10">
              <p className="text-red-500">{error}</p>
              {unauthorized && (
                <div className="mt-4">
                  <p className="text-gray-700">
                    {!user ? (
                      <>
                        You need to be logged in to view candidate profiles.{" "}
                        <Link
                          href="/auth/login"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Log in
                        </Link>{" "}
                        to continue.
                      </>
                    ) : user.role === "candidate" ? (
                      "As a job seeker, you can only view your own profile."
                    ) : (
                      "Please try again or contact support if you think this is an error."
                    )}
                  </p>
                </div>
              )}
            </div>
          ) : candidate ? (
            <div className="space-y-6">
              {/* Candidate header */}
              <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6">
                  <h1 className="text-3xl font-bold text-gray-900">
                    {candidate.name}
                  </h1>
                  <p className="mt-1 max-w-2xl text-lg text-gray-700">
                    {candidate.title}
                  </p>
                  <div className="mt-2 flex items-center text-sm text-gray-500">
                    <span>{candidate.location}</span>
                    {candidate.domain && (
                      <>
                        <span className="mx-2">•</span>
                        <span>{formatForDisplay(candidate.domain)}</span>
                      </>
                    )}
                    {candidate.email && (
                      <>
                        <span className="mx-2">•</span>
                        <span>{candidate.email}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Summary section */}
              {candidate.summary && (
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                  <div className="px-4 py-5 sm:px-6">
                    <h2 className="text-xl font-bold text-gray-900">Summary</h2>
                  </div>
                  <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                    <p className="text-gray-700">{candidate.summary}</p>
                  </div>
                </div>
              )}

              {/* Skills section */}
              <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                <div className="px-4 py-5 sm:px-6">
                  <h2 className="text-xl font-bold text-gray-900">Skills</h2>
                  <p className="mt-1 max-w-2xl text-sm text-gray-500">
                    Skills and competencies listed by proficiency level
                  </p>
                </div>
                <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                  {candidate.skills?.length > 0 ? (
                    <div className="space-y-6">
                      {/* Skill breakdown summary */}
                      <div className="mb-8 bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">
                          Skill Proficiency Breakdown
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                          {[
                            "Expert",
                            "Advanced",
                            "Intermediate",
                            "Beginner",
                          ].map((proficiencyLevel) => {
                            const skillsWithLevel = candidate.skills?.filter(
                              (skill) => {
                                const level = skill.level || 0;
                                if (proficiencyLevel === "Expert")
                                  return level >= 8;
                                if (proficiencyLevel === "Advanced")
                                  return level >= 6 && level < 8;
                                if (proficiencyLevel === "Intermediate")
                                  return level >= 4 && level < 6;
                                return level < 4; // Beginner
                              }
                            );

                            const percentage = Math.round(
                              (skillsWithLevel.length /
                                candidate.skills.length) *
                                100
                            );

                            // Define colors for different proficiency levels
                            const colorClasses = {
                              Expert: {
                                text: "text-orange-800",
                                bg: "bg-orange-500",
                                light: "bg-orange-100",
                              },
                              Advanced: {
                                text: "text-purple-800",
                                bg: "bg-purple-500",
                                light: "bg-purple-100",
                              },
                              Intermediate: {
                                text: "text-green-800",
                                bg: "bg-green-500",
                                light: "bg-green-100",
                              },
                              Beginner: {
                                text: "text-blue-800",
                                bg: "bg-blue-500",
                                light: "bg-blue-100",
                              },
                            };

                            return (
                              <div
                                key={proficiencyLevel}
                                className={`border rounded-lg overflow-hidden shadow-sm ${
                                  colorClasses[proficiencyLevel].light
                                } border-${
                                  colorClasses[proficiencyLevel].bg.split(
                                    "-"
                                  )[0]
                                }-200`}
                              >
                                <div
                                  className={`px-4 py-2 ${
                                    colorClasses[proficiencyLevel].light
                                  } border-b border-${
                                    colorClasses[proficiencyLevel].bg.split(
                                      "-"
                                    )[0]
                                  }-200`}
                                >
                                  <div className="flex justify-between items-center">
                                    <h4
                                      className={`font-semibold ${colorClasses[proficiencyLevel].text}`}
                                    >
                                      {proficiencyLevel}
                                    </h4>
                                    <span className="text-sm font-medium">
                                      {skillsWithLevel.length} skills
                                    </span>
                                  </div>
                                </div>
                                <div className="px-4 py-4">
                                  <div className="mb-2">
                                    <div className="flex justify-between mb-1">
                                      <span className="text-xs font-medium">
                                        Distribution
                                      </span>
                                      <span className="text-xs font-medium">
                                        {percentage}%
                                      </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                      <div
                                        className={`${colorClasses[proficiencyLevel].bg} h-2 rounded-full`}
                                        style={{ width: `${percentage}%` }}
                                      ></div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Core and Secondary skills display */}
                      <div className="mt-6 space-y-6">
                        {/* Core Skills */}
                        <div className="pt-4 border-t border-gray-200">
                          <h3 className="text-md font-medium text-gray-800 mb-3">
                            Core Skills
                          </h3>
                          <div className="flex flex-wrap">
                            {candidate.skills
                              ?.filter((skill) => skill.skill_type === "core")
                              .map((skill) => (
                                <SkillTag
                                  key={skill.skill_id}
                                  skill={skill}
                                  proficiency={
                                    skill.level >= 8
                                      ? "Expert"
                                      : skill.level >= 6
                                      ? "Advanced"
                                      : skill.level >= 4
                                      ? "Intermediate"
                                      : "Beginner"
                                  }
                                  linkToSkill={true}
                                />
                              ))}
                            {candidate.skills?.filter(
                              (skill) => skill.skill_type === "core"
                            ).length === 0 && (
                              <p className="text-gray-500">
                                No core skills listed.
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Secondary Skills */}
                        <div className="pt-4 border-t border-gray-200">
                          <h3 className="text-md font-medium text-gray-800 mb-3">
                            Secondary Skills
                          </h3>
                          <div className="flex flex-wrap">
                            {candidate.skills
                              ?.filter(
                                (skill) => skill.skill_type === "secondary"
                              )
                              .map((skill) => (
                                <SkillTag
                                  key={skill.skill_id}
                                  skill={skill}
                                  proficiency={
                                    skill.level >= 8
                                      ? "Expert"
                                      : skill.level >= 6
                                      ? "Advanced"
                                      : skill.level >= 4
                                      ? "Intermediate"
                                      : "Beginner"
                                  }
                                  linkToSkill={true}
                                />
                              ))}
                            {candidate.skills?.filter(
                              (skill) => skill.skill_type === "secondary"
                            ).length === 0 && (
                              <p className="text-gray-500">
                                No secondary skills listed.
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500">No skills listed.</p>
                  )}
                </div>
              </div>

              {/* Experience section */}
              {candidate.experience &&
                Array.isArray(candidate.experience) &&
                candidate.experience.length > 0 && (
                  <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div className="px-4 py-5 sm:px-6">
                      <h2 className="text-xl font-bold text-gray-900">
                        Work Experience
                      </h2>
                    </div>
                    <div className="border-t border-gray-200">
                      <ul className="divide-y divide-gray-200">
                        {candidate.experience.map((experience, index) => {
                          // Cast experience to our updated interface
                          const exp = experience as unknown as ExperienceItem;
                          return (
                            <li key={index} className="px-4 py-4 sm:px-6">
                              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                                <div>
                                  <h3 className="text-lg font-medium text-gray-900">
                                    {exp.title}
                                  </h3>
                                  <p className="text-gray-700">{exp.company}</p>
                                </div>
                                <p className="text-sm text-gray-500">
                                  {exp.start_date && (
                                    <>
                                      {exp.start_date}
                                      {exp.end_date && <> - {exp.end_date}</>}
                                    </>
                                  )}
                                  {!exp.start_date && exp.period && (
                                    <>{exp.period}</>
                                  )}
                                </p>
                              </div>
                              {Array.isArray(exp.description) &&
                              exp.description.length > 0 ? (
                                <ul className="mt-2 list-disc list-inside text-gray-600 space-y-1 ml-2">
                                  {exp.description.map((item, i) => (
                                    <li key={i} className="text-gray-600">
                                      {item}
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="mt-2 text-gray-600">
                                  {typeof exp.description === "string"
                                    ? exp.description
                                    : ""}
                                </p>
                              )}
                              {exp.skills && exp.skills.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-sm font-medium text-gray-500 mb-1">
                                    Skills used:
                                  </p>
                                  <div className="flex flex-wrap gap-1">
                                    {exp.skills.map((skill) => (
                                      <span
                                        key={skill.skill_id}
                                        className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded-full"
                                      >
                                        {skill.name}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  </div>
                )}

              {/* Education section */}
              {candidate.education &&
                Array.isArray(candidate.education) &&
                candidate.education.length > 0 && (
                  <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div className="px-4 py-5 sm:px-6">
                      <h2 className="text-xl font-bold text-gray-900">
                        Education
                      </h2>
                    </div>
                    <div className="border-t border-gray-200">
                      <ul className="divide-y divide-gray-200">
                        {candidate.education.map((education, index) => (
                          <li key={index} className="px-4 py-4 sm:px-6">
                            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                              <div>
                                <h3 className="text-lg font-medium text-gray-900">
                                  {education.degree} in {education.field}
                                </h3>
                                <p className="text-gray-700">
                                  {education.institution}
                                </p>
                              </div>
                              <p className="text-sm text-gray-500">
                                {education.year}
                              </p>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

              {/* Certifications section */}
              {candidate.certifications &&
                Array.isArray(candidate.certifications) &&
                candidate.certifications.length > 0 && (
                  <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                    <div className="px-4 py-5 sm:px-6">
                      <h2 className="text-xl font-bold text-gray-900">
                        Certifications
                      </h2>
                    </div>
                    <div className="border-t border-gray-200">
                      <ul className="divide-y divide-gray-200">
                        {candidate.certifications.map((cert, index) => (
                          <li key={index} className="px-4 py-4 sm:px-6">
                            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                              <div>
                                <h3 className="text-lg font-medium text-gray-900">
                                  {cert.name}
                                </h3>
                                <p className="text-gray-700">{cert.issuer}</p>
                              </div>
                              <p className="text-sm text-gray-500">
                                {cert.date}
                              </p>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

              {/* Matching jobs section */}
              {matchingJobs.length > 0 && (
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                  <div className="px-4 py-5 sm:px-6">
                    <h2 className="text-xl font-bold text-gray-900">
                      Matching Jobs
                    </h2>
                    <p className="mt-1 max-w-2xl text-sm text-gray-500">
                      Jobs that match this candidate's skills
                    </p>
                  </div>
                  <div className="border-t border-gray-200">
                    <ul className="divide-y divide-gray-200">
                      {matchingJobs.map((job) => (
                        <li key={job.job_id} className="px-4 py-4 sm:px-6">
                          <div className="flex justify-between items-center">
                            <div>
                              <Link
                                href={`/jobs/${job.job_id}`}
                                className="text-lg font-medium text-blue-600 hover:text-blue-800"
                              >
                                {job.title}
                              </Link>
                              <p className="text-gray-700">{job.company}</p>
                            </div>
                            <div className="text-sm px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                              {Math.round(job.match_percentage)}% Match
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-10">
              <p className="text-red-500">Candidate not found</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
