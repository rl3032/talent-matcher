"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../components/Layout";
import Link from "next/link";
import { apiClient } from "../../../lib/api";

interface Job {
  job_id: string;
  title: string;
  company: string;
  location: string;
  match_percentage: number;
}

export default function CandidateDashboard() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matchingJobs, setMatchingJobs] = useState<Job[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);

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

  return (
    <Layout>
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Candidate Dashboard
          </h1>

          {!user.profile_id ? (
            <Link
              href="/dashboard/candidate/upload-resume"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Upload Your Resume
            </Link>
          ) : (
            <div className="flex space-x-3">
              <Link
                href={`/candidates/${user.profile_id}`}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                View My Profile
              </Link>
              <Link
                href="/dashboard/candidate/edit-resume"
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Edit Resume
              </Link>
              <Link
                href="/dashboard/candidate/career-insights"
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                Career Insights
              </Link>
            </div>
          )}
        </div>

        {!user.profile_id ? (
          <div className="text-center py-12 bg-gray-50 rounded">
            <h2 className="text-xl font-semibold mb-2">
              Upload Your Resume to Get Started
            </h2>
            <p className="text-gray-500 mb-6">
              Upload your resume to see matching job opportunities and get
              personalized recommendations.
            </p>
            <Link
              href="/dashboard/candidate/upload-resume"
              className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Upload Resume
            </Link>
          </div>
        ) : (
          <div className="mb-8">
            <h2 className="text-xl font-semibold mb-4">
              Matching Job Opportunities
            </h2>
            {loadingJobs ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : matchingJobs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                        Title
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                        Company
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                        Location
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                        Match
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {matchingJobs.map((job) => (
                      <tr key={job.job_id} className="hover:bg-gray-50">
                        <td className="py-4 px-4">{job.title}</td>
                        <td className="py-4 px-4">{job.company}</td>
                        <td className="py-4 px-4">{job.location}</td>
                        <td className="py-4 px-4">
                          <div className="flex items-center">
                            <div className="w-full bg-gray-200 rounded-full h-2.5">
                              <div
                                className="bg-blue-600 h-2.5 rounded-full"
                                style={{ width: `${job.match_percentage}%` }}
                              ></div>
                            </div>
                            <span className="ml-2 text-sm text-gray-600">
                              {job.match_percentage}%
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Link
                            href={`/jobs/${job.job_id}`}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            View Details
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded">
                <p className="text-gray-500">
                  No matching jobs found. Check back later!
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
