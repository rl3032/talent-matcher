"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../lib/api";
import { Candidate } from "../../types";
import CandidateCard from "../../components/CandidateCard";
import Layout from "../../components/Layout";

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<{
    locations: string[];
    titles: string[];
  }>({
    locations: [],
    titles: [],
  });
  const [selectedLocation, setSelectedLocation] = useState<string>("");
  const [selectedTitle, setSelectedTitle] = useState<string>("");

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setLoading(true);
        const response = await apiClient.getAllCandidates();
        setCandidates(response.candidates || []);
        setFilters({
          locations: response.filters?.locations || [],
          titles: response.filters?.titles || [],
        });
        setError(null);
      } catch (err) {
        console.error("Error fetching candidates:", err);
        setError("Failed to load candidates. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
  }, []);

  // Format a value for display (convert snake_case to Title Case)
  const formatForDisplay = (value: string): string => {
    if (!value) return "";
    return value
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Filter candidates based on search query and selected filters
  const filteredCandidates = candidates.filter((candidate) => {
    // Search query filter
    const matchesSearch =
      searchQuery === "" ||
      candidate.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (candidate.title &&
        candidate.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (candidate.location &&
        candidate.location.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (candidate.domain &&
        candidate.domain.toLowerCase().includes(searchQuery.toLowerCase()));

    // Location filter
    const matchesLocation =
      selectedLocation === "" || candidate.location === selectedLocation;

    // Title filter
    const matchesTitle =
      selectedTitle === "" || candidate.title === selectedTitle;

    return matchesSearch && matchesLocation && matchesTitle;
  });

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Talent Pool</h1>

        {/* Search and filters */}
        <div className="mb-6 space-y-4">
          {/* Search input */}
          <input
            type="text"
            placeholder="Search candidates by name, title, location..."
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
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

            {/* Title filter */}
            <div className="w-full md:w-auto">
              <select
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedTitle}
                onChange={(e) => setSelectedTitle(e.target.value)}
              >
                <option value="">All Titles</option>
                {filters.titles.map((title) => (
                  <option key={title} value={title}>
                    {title}
                  </option>
                ))}
              </select>
            </div>

            {/* Clear filters button */}
            {(selectedLocation || selectedTitle) && (
              <button
                className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                onClick={() => {
                  setSelectedLocation("");
                  setSelectedTitle("");
                }}
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="text-center py-10">
            <p className="text-gray-500">Loading candidates...</p>
          </div>
        ) : error ? (
          <div className="text-center py-10">
            <p className="text-red-500">{error}</p>
          </div>
        ) : filteredCandidates.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-gray-500">
              No candidates found matching your search criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCandidates.map((candidate) => (
              <CandidateCard
                key={candidate.resume_id}
                candidate={{
                  ...candidate,
                  domain: candidate.domain
                    ? formatForDisplay(candidate.domain)
                    : "",
                }}
              />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
