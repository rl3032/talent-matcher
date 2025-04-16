"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "../../../lib/api";
import { Skill } from "../../../types";
import Layout from "../../../components/Layout";
import Link from "next/link";
import SkillGraphContainer from "../../../components/SkillGraphContainer";

interface RelatedSkill extends Skill {
  relationship_type?: string;
}

interface SkillDetail extends Skill {
  related_skills?: RelatedSkill[];
  jobs?: {
    job_id: string;
    title: string;
    company: string;
    required_level: number;
  }[];
}

export default function SkillDetailPage() {
  const { skill_id } = useParams<{ skill_id: string }>();
  const [skill, setSkill] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSkillDetails = async () => {
      try {
        setLoading(true);
        // Fetch skill details using apiClient
        const data = await apiClient.getSkill(skill_id as string);
        setSkill(data.skill);
        setError(null);
      } catch (err) {
        console.error("Error fetching skill details:", err);
        setError("Failed to load skill details. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    if (skill_id) {
      fetchSkillDetails();
    }
  }, [skill_id]);

  const formatRelationshipType = (type: string): string => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-center py-20">
          <p className="text-gray-500">Loading skill details...</p>
        </div>
      </Layout>
    );
  }

  if (error || !skill) {
    return (
      <Layout>
        <div className="text-center py-20">
          <p className="text-red-500">{error || "Skill not found"}</p>
          <Link
            href="/skills"
            className="mt-4 inline-block text-blue-600 hover:text-blue-800"
          >
            ← Back to Skills
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-8">
        {/* Back button */}
        <div className="mb-6">
          <Link href="/skills" className="text-blue-600 hover:text-blue-800">
            ← Back to Skills
          </Link>
        </div>

        {/* Skill Header */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
          <div className="px-4 py-5 sm:px-6">
            <h1 className="text-3xl font-bold text-gray-900">{skill.name}</h1>
            <p className="mt-2 text-sm text-gray-500">
              Category: <span className="font-semibold">{skill.category}</span>
            </p>
          </div>
        </div>

        {/* Skill Graph */}
        <div className="mb-6">
          <SkillGraphContainer
            skillId={skill_id as string}
            width={800}
            height={500}
            depth={2}
          />
        </div>

        {/* Related Skills */}
        {skill.related_skills && skill.related_skills.length > 0 && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-xl font-bold text-gray-900">
                Related Skills
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Skills connected to {skill.name}
              </p>
            </div>
            <div className="border-t border-gray-200">
              <ul>
                {skill.related_skills.map((relatedSkill) => (
                  <li
                    key={relatedSkill.skill_id}
                    className="px-4 py-3 sm:px-6 border-b border-gray-200 last:border-b-0"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <Link
                          href={`/skills/${relatedSkill.skill_id}`}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          {relatedSkill.name}
                        </Link>
                        <p className="text-sm text-gray-500">
                          {relatedSkill.category}
                        </p>
                      </div>
                      {relatedSkill.relationship_type && (
                        <span className="text-xs bg-gray-100 rounded-full px-3 py-1">
                          {formatRelationshipType(
                            relatedSkill.relationship_type
                          )}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Jobs requiring this skill */}
        {skill.jobs && skill.jobs.length > 0 && (
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h2 className="text-xl font-bold text-gray-900">
                Jobs requiring this skill
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Job postings that require {skill.name}
              </p>
            </div>
            <div className="border-t border-gray-200">
              <ul>
                {skill.jobs.map((job) => (
                  <li
                    key={job.job_id}
                    className="px-4 py-3 sm:px-6 border-b border-gray-200 last:border-b-0"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <Link
                          href={`/jobs/${job.job_id}`}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          {job.title}
                        </Link>
                        <p className="text-sm text-gray-500">{job.company}</p>
                      </div>
                      <div className="text-xs bg-blue-100 text-blue-800 rounded-full px-3 py-1">
                        Level: {job.required_level}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
