"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../lib/api";
import { Job } from "../../types";
import JobCard from "../../components/JobCard";
import Layout from "../../components/Layout";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<{
    domains: string[];
    locations: string[];
  }>({
    domains: [],
    locations: [],
  });
  const [selectedDomain, setSelectedDomain] = useState<string>("");
  const [selectedLocation, setSelectedLocation] = useState<string>("");

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        setLoading(true);
        const response = await apiClient.getAllJobs();
        setJobs(response.jobs || []);
        setFilters({
          domains: response.filters?.domains || [],
          locations: response.filters?.locations || [],
        });
        setError(null);
      } catch (err) {
        console.error("Error fetching jobs:", err);
        setError("Failed to load jobs. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchJobs();
  }, []);

  // Format a value for display (convert snake_case to Title Case)
  const formatForDisplay = (value: string): string => {
    if (!value) return "";
    return value
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Filter jobs based on search query and selected filters
  const filteredJobs = jobs.filter((job) => {
    // Search query filter
    const matchesSearch =
      searchQuery === "" ||
      job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (job.location &&
        job.location.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (job.domain &&
        job.domain.toLowerCase().includes(searchQuery.toLowerCase()));

    // Domain filter
    const matchesDomain =
      selectedDomain === "" || job.domain === selectedDomain;

    // Location filter
    const matchesLocation =
      selectedLocation === "" || job.location === selectedLocation;

    return matchesSearch && matchesDomain && matchesLocation;
  });

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Available Jobs
        </h1>

        {/* Search and filters */}
        <div className="mb-6 space-y-4">
          {/* Search input */}
          <input
            type="text"
            placeholder="Search jobs by title, company, location..."
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            {/* Domain filter */}
            <div className="w-full md:w-auto">
              <select
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
              >
                <option value="">All Domains</option>
                {filters.domains.map((domain) => (
                  <option key={domain} value={domain}>
                    {formatForDisplay(domain)}
                  </option>
                ))}
              </select>
            </div>

            {/* Location filter */}
            <div className="w-full md:w-auto">
              <select
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
              >
                <option value="">All Locations</option>
                {filters.locations.map((location) => (
                  <option key={location} value={location}>
                    {location}
                  </option>
                ))}
              </select>
            </div>

            {/* Clear filters button */}
            {(selectedDomain || selectedLocation) && (
              <button
                className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                onClick={() => {
                  setSelectedDomain("");
                  setSelectedLocation("");
                }}
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-10">
            <p className="text-gray-500">Loading jobs...</p>
          </div>
        ) : error ? (
          <div className="text-center py-10">
            <p className="text-red-500">{error}</p>
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-gray-500">
              No jobs found matching your search criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.job_id}
                job={{
                  ...job,
                  domain: job.domain ? formatForDisplay(job.domain) : "",
                }}
              />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
