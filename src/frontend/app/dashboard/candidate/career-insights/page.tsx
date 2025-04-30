"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../../components/Layout";
import SkillGapAnalysis from "../../../../components/SkillGapAnalysis";
import { apiClient } from "../../../../lib/api";

interface Job {
  job_id: string;
  title: string;
  company: string;
  match_percentage: number;
}

export default function CareerInsightsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matchingJobs, setMatchingJobs] = useState<Job[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  // Redirect if not logged in or not a candidate
  useEffect(() => {
    if (!loading && (!user || user.role !== "candidate")) {
      router.push("/auth/login");
    }
  }, [user, loading, router]);

  // Fetch matching jobs for the current user
  useEffect(() => {
    const fetchMatchingJobs = async () => {
      if (user?.profile_id) {
        try {
          const data = await apiClient.getCandidateMatchesEnhanced(
            user.profile_id
          );
          setMatchingJobs(data || []);

          // Select the first job by default if available
          if (data && data.length > 0) {
            setSelectedJobId(data[0].job_id);
          }
        } catch (error) {
          console.error("Error fetching matching jobs:", error);
        }
      }
      setLoadingJobs(false);
    };

    if (user && user.profile_id) {
      fetchMatchingJobs();
    } else {
      setLoadingJobs(false);
    }
  }, [user]);

  if (loading || !user) {
    return (
      <Layout>
        <div className="flex justify-center items-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  if (!user.profile_id) {
    return (
      <Layout>
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            Career Insights
          </h1>
          <div className="text-center py-12 bg-gray-50 rounded">
            <h2 className="text-xl font-semibold mb-2">
              Upload Your Resume First
            </h2>
            <p className="text-gray-500 mb-6">
              You need to upload your resume to access career insights and
              recommendations.
            </p>
            <button
              onClick={() => router.push("/dashboard/candidate/upload-resume")}
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Upload Resume
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Skill Gap Analysis
        </h1>

        <div>
          <div className="mb-6">
            <label
              htmlFor="jobSelect"
              className="block font-medium text-gray-700 mb-2"
            >
              Select a job to analyze your skill gap:
            </label>
            <select
              id="jobSelect"
              value={selectedJobId || ""}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              disabled={loadingJobs || matchingJobs.length === 0}
            >
              {loadingJobs ? (
                <option>Loading jobs...</option>
              ) : matchingJobs.length === 0 ? (
                <option>No matching jobs found</option>
              ) : (
                matchingJobs.map((job) => (
                  <option key={job.job_id} value={job.job_id}>
                    {job.title} at {job.company} (
                    {Math.round(job.match_percentage)}% match)
                  </option>
                ))
              )}
            </select>
          </div>

          {selectedJobId && user.profile_id && (
            <SkillGapAnalysis
              candidateId={user.profile_id}
              jobId={selectedJobId}
            />
          )}
        </div>
      </div>
    </Layout>
  );
}
