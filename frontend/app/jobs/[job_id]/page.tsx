"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "../../../lib/api";
import { JobWithSkills, MatchResult } from "../../../types";
import Layout from "../../../components/Layout";
import SkillTag, { ProficiencyLevel } from "../../../components/SkillTag";
import CandidateCard from "../../../components/CandidateCard";
import Link from "next/link";
import { useAuth } from "../../../lib/AuthContext";

export default function JobDetailPage() {
  const { user } = useAuth();
  const { job_id } = useParams<{ job_id: string }>();
  const [job, setJob] = useState<JobWithSkills | null>(null);
  const [matchingCandidates, setMatchingCandidates] = useState<MatchResult[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [canViewCandidates, setCanViewCandidates] = useState(false);
  const [candidateError, setCandidateError] = useState<string | null>(null);

  // Format a value for display (convert snake_case to Title Case)
  const formatForDisplay = (value: string): string => {
    if (!value) return "";
    return value
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        setLoading(true);
        // Fetch job details
        const jobData = await apiClient.getJob(job_id as string);
        setJob(jobData);

        // Check if the current user is a hiring manager or admin
        if (user && (user.role === "hiring_manager" || user.role === "admin")) {
          // If the job has an owner_email property and it matches the current user's email,
          // or if this is the first time the job is being viewed (no owner_email yet)
          // or if the user is an admin
          if (
            !jobData.owner_email ||
            jobData.owner_email === user.email ||
            user.role === "admin"
          ) {
            setCanViewCandidates(true);

            try {
              // Only fetch candidates if user has permission
              const candidatesData = await apiClient.getJobMatchesEnhanced(
                job_id as string,
                {
                  limit: 10,
                  skillsWeight: 0.75,
                  locationWeight: 0.15,
                  semanticWeight: 0.1,
                }
              );
              setMatchingCandidates(candidatesData);
            } catch (candidateErr) {
              console.error(
                "Error fetching matching candidates:",
                candidateErr
              );
              setCandidateError(
                "Failed to load matching candidates. You might not have permission to view them."
              );
            }
          }
        }

        setError(null);
      } catch (err) {
        console.error("Error fetching job details:", err);
        setError("Failed to load job details. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    if (job_id) {
      fetchJobDetails();
    }
  }, [job_id, user]);

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-20">
          <p className="text-gray-500">Loading job details...</p>
        </div>
      </Layout>
    );
  }

  if (error || !job) {
    return (
      <Layout>
        <div className="text-center py-20">
          <p className="text-red-500">{error || "Job not found"}</p>
          <Link
            href="/jobs"
            className="mt-4 inline-block text-blue-600 hover:text-blue-800"
          >
            ← Back to Jobs
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-8">
        {/* Back link */}
        <Link
          href="/jobs"
          className="text-blue-600 hover:text-blue-800 mb-6 inline-block"
        >
          ← Back to Jobs
        </Link>

        {/* Job header */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
          <div className="px-4 py-5 sm:px-6">
            <h1 className="text-3xl font-bold text-gray-900">{job.title}</h1>
            <p className="mt-1 max-w-2xl text-lg text-gray-700">
              {job.company}
            </p>
            <div className="mt-2 flex items-center text-sm text-gray-500">
              <span>{job.location}</span>
              {job.domain && (
                <>
                  <span className="mx-2">•</span>
                  <span>{formatForDisplay(job.domain)}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Job description section */}
        {job.description && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-xl font-bold text-gray-900">Description</h2>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
              <p className="text-gray-700 whitespace-pre-line">
                {job.description}
              </p>
            </div>
          </div>
        )}

        {/* Responsibilities section */}
        {job.responsibilities && Array.isArray(job.responsibilities) && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-xl font-bold text-gray-900">
                Responsibilities
              </h2>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
              {job.responsibilities.length > 0 ? (
                <ul className="list-disc pl-5 space-y-2">
                  {job.responsibilities.map((responsibility, index) => (
                    <li key={index} className="text-gray-700">
                      {responsibility}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">
                  No specific responsibilities listed for this job.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Qualifications section */}
        {job.qualifications && Array.isArray(job.qualifications) && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-xl font-bold text-gray-900">
                Qualifications
              </h2>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
              {job.qualifications.length > 0 ? (
                <ul className="list-disc pl-5 space-y-2">
                  {job.qualifications.map((qualification, index) => (
                    <li key={index} className="text-gray-700">
                      {qualification}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">
                  No specific qualifications listed for this job.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Skills section */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
          <div className="px-4 py-5 sm:px-6">
            <h2 className="text-xl font-bold text-gray-900">Required Skills</h2>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Skills required for this position
            </p>
          </div>
          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
            {job.skills && job.skills.length > 0 ? (
              <div>
                {/* Primary Skills Section */}
                <h3 className="text-lg font-semibold mb-3">Primary Skills</h3>
                <div className="flex flex-wrap mb-6">
                  {job.skills
                    .filter(
                      (skill) => skill.relationship_type === "REQUIRES_PRIMARY"
                    )
                    .sort((a, b) => b.level - a.level)
                    .map((skill) => (
                      <SkillTag
                        key={skill.skill_id}
                        skill={skill}
                        proficiency={
                          skill.proficiency
                            ? ((skill.proficiency.charAt(0).toUpperCase() +
                                skill.proficiency
                                  .slice(1)
                                  .toLowerCase()) as ProficiencyLevel)
                            : skill.level >= 8
                            ? "Expert"
                            : skill.level >= 6
                            ? "Advanced"
                            : skill.level >= 4
                            ? "Intermediate"
                            : "Beginner"
                        }
                        importance={skill.level}
                        linkToSkill={true}
                        isPrimary={true}
                      />
                    ))}
                </div>

                {/* Secondary Skills Section */}
                <h3 className="text-lg font-semibold mb-3">Secondary Skills</h3>
                <div className="flex flex-wrap">
                  {job.skills
                    .filter(
                      (skill) => skill.relationship_type !== "REQUIRES_PRIMARY"
                    )
                    .sort((a, b) => b.level - a.level)
                    .map((skill) => (
                      <SkillTag
                        key={skill.skill_id}
                        skill={skill}
                        proficiency={
                          skill.proficiency
                            ? ((skill.proficiency.charAt(0).toUpperCase() +
                                skill.proficiency
                                  .slice(1)
                                  .toLowerCase()) as ProficiencyLevel)
                            : skill.level >= 8
                            ? "Expert"
                            : skill.level >= 6
                            ? "Advanced"
                            : skill.level >= 4
                            ? "Intermediate"
                            : "Beginner"
                        }
                        importance={skill.level}
                        linkToSkill={true}
                        isPrimary={false}
                      />
                    ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-500">
                No specific skills listed for this job.
              </p>
            )}
          </div>
        </div>

        {/* Matching candidates section - only shown for job owners and admins */}
        {user &&
        (user.role === "hiring_manager" || user.role === "admin") &&
        canViewCandidates ? (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-xl font-bold text-gray-900">
                Matching Candidates
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Candidates who match the requirements for this job
              </p>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
              {candidateError ? (
                <p className="text-red-500">{candidateError}</p>
              ) : matchingCandidates.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {matchingCandidates.map((candidate) => (
                    <CandidateCard
                      key={candidate.resume_id}
                      candidate={{
                        resume_id: candidate.resume_id || "",
                        name: candidate.name || "",
                        title: candidate.title || "",
                        location: "",
                        domain: "",
                      }}
                      matchPercentage={candidate.match_percentage}
                      skills={candidate.matching_skills}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">
                  No matching candidates found for this job.
                </p>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </Layout>
  );
}
