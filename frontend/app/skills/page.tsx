"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "../../lib/api";
import { Skill } from "../../types";
import Layout from "../../components/Layout";
import SkillTag from "../../components/SkillTag";
import Link from "next/link";

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getAllSkills();
        setSkills(data.skills || []);

        // Extract unique categories
        const uniqueCategories = Array.from(
          new Set(data.skills.map((skill: Skill) => skill.category))
        ) as string[];
        setCategories(uniqueCategories.sort());

        setError(null);
      } catch (err) {
        console.error("Error fetching skills:", err);
        setError("Failed to load skills. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchSkills();
  }, []);

  // Format a value for display (convert snake_case to Title Case)
  const formatForDisplay = (value: string): string => {
    if (!value) return "";
    return value
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Filter skills based on search query and category
  const filteredSkills = skills.filter((skill) => {
    const matchesSearch =
      searchQuery === "" ||
      skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (skill.category &&
        skill.category.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesCategory =
      categoryFilter === "" || skill.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Skills Library
        </h1>

        {/* Search and filters */}
        <div className="mb-6 space-y-4">
          {/* Search input */}
          <input
            type="text"
            placeholder="Search skills by name or category..."
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          {/* Category filter */}
          <div className="w-full">
            <select
              className="w-full md:w-64 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">All Categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {formatForDisplay(category)}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-10">
            <p className="text-gray-500">Loading skills...</p>
          </div>
        ) : error ? (
          <div className="text-center py-10">
            <p className="text-red-500">{error}</p>
          </div>
        ) : filteredSkills.length === 0 ? (
          <div className="text-center py-10">
            <p className="text-gray-500">
              No skills found matching your search criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredSkills.map((skill) => (
              <Link
                key={skill.skill_id}
                href={`/skills/${skill.skill_id}`}
                className="group"
              >
                <div className="h-full bg-white border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow p-4 flex flex-col">
                  <h3 className="text-lg font-semibold text-blue-600 group-hover:text-blue-800 mb-2">
                    {skill.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    Category: {formatForDisplay(skill.category)}
                  </p>
                  <p className="text-xs text-gray-500 mt-auto">
                    Click to view skill details and relationships
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
