"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../lib/AuthContext";
import { useRouter } from "next/navigation";
import Layout from "../../../components/Layout";
import Link from "next/link";

interface Job {
  job_id: string;
  title: string;
  company: string;
  location: string;
  domain: string;
  owner_email?: string;
}

export default function HiringDashboard() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [postedJobs, setPostedJobs] = useState<Job[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteInProgress, setDeleteInProgress] = useState(false);

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

  // Fetch posted jobs for the current user
  useEffect(() => {
    const fetchPostedJobs = async () => {
      try {
        const response = await fetch(
          `/api/jobs?owner_email=${encodeURIComponent(user?.email || "")}`
        );
        if (response.ok) {
          const data = await response.json();
          setPostedJobs(data.jobs || []);
        }
      } catch (error) {
        console.error("Error fetching jobs:", error);
      }
      setLoadingJobs(false);
    };

    if (user) {
      fetchPostedJobs();
    }
  }, [user]);

  // Handle job deletion
  const handleDeleteJob = async (jobId: string) => {
    if (!confirm("Are you sure you want to delete this job posting?")) {
      return;
    }

    setDeleteInProgress(true);
    setDeleteError(null);

    try {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        setDeleteError("You must be logged in to delete a job");
        setDeleteInProgress(false);
        return;
      }

      const response = await fetch(`/api/jobs/${jobId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Remove the deleted job from the list
        setPostedJobs(postedJobs.filter((job) => job.job_id !== jobId));
      } else {
        const data = await response.json();
        setDeleteError(data.error || "Failed to delete job. Please try again.");
      }
    } catch (error) {
      console.error("Error deleting job:", error);
      setDeleteError("An error occurred. Please try again.");
    } finally {
      setDeleteInProgress(false);
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
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">
            {user.role === "admin"
              ? "Admin Dashboard"
              : "Hiring Manager Dashboard"}
          </h1>
          <Link
            href="/dashboard/hiring/post-job"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Post a New Job
          </Link>
        </div>

        {deleteError && (
          <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">
            {deleteError}
          </div>
        )}

        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Your Posted Jobs</h2>
          {loadingJobs ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : postedJobs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                      Title
                    </th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                      Location
                    </th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                      Domain
                    </th>
                    <th className="py-3 px-4 text-left text-sm font-medium text-gray-600">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {postedJobs.map((job) => (
                    <tr key={job.job_id} className="hover:bg-gray-50">
                      <td className="py-4 px-4">{job.title}</td>
                      <td className="py-4 px-4">{job.location}</td>
                      <td className="py-4 px-4">{formatDomain(job.domain)}</td>
                      <td className="py-4 px-4">
                        <div className="flex space-x-2">
                          <Link
                            href={`/jobs/${job.job_id}`}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            View
                          </Link>
                          <Link
                            href={`/dashboard/hiring/edit-job/${job.job_id}`}
                            className="text-green-600 hover:text-green-800"
                          >
                            Edit
                          </Link>
                          <button
                            onClick={() => handleDeleteJob(job.job_id)}
                            disabled={deleteInProgress}
                            className="text-red-600 hover:text-red-800"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 bg-gray-50 rounded">
              <p className="text-gray-500">
                You haven&apos;t posted any jobs yet.
              </p>
              <Link
                href="/dashboard/hiring/post-job"
                className="mt-2 inline-block text-blue-600 hover:text-blue-800"
              >
                Post your first job
              </Link>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
