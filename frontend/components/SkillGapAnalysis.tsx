import React, { useState, useEffect } from "react";
import { apiClient } from "../lib/api";

interface SkillGapProps {
  candidateId: string;
  jobId: string;
}

interface MissingSkill {
  missing_skill: string;
  category: string;
  importance: number;
}

interface RelatedSkill {
  target_skill: string;
  related_skill: string;
  importance: number;
}

interface SkillGapData {
  missing_skills: MissingSkill[];
  related_skills: RelatedSkill[];
}

export default function SkillGapAnalysis({
  candidateId,
  jobId,
}: SkillGapProps) {
  const [skillGap, setSkillGap] = useState<SkillGapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSkillGap = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getSkillGap(candidateId, jobId);
        setSkillGap(data);
        setError(null);
      } catch (error: any) {
        console.error("Error fetching skill gap:", error);
        setError(error.message || "Failed to load skill gap analysis");
      } finally {
        setLoading(false);
      }
    };

    fetchSkillGap();
  }, [candidateId, jobId]);

  if (loading) {
    return (
      <div className="mt-4 p-6 border rounded-lg bg-white shadow animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-5/6 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-4/6 mb-2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-4 p-4 border rounded-lg bg-red-50 text-red-800">
        <h3 className="text-lg font-semibold mb-2">Error Loading Analysis</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!skillGap) {
    return null;
  }

  return (
    <div className="mt-6 p-6 border rounded-lg bg-white shadow">
      <h3 className="text-xl font-semibold mb-4 text-gray-800">
        Skill Gap Analysis
      </h3>

      {/* Missing Skills Section */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-700 text-lg mb-2">
          Skills You Need to Develop
        </h4>
        {skillGap.missing_skills && skillGap.missing_skills.length > 0 ? (
          <div className="space-y-2">
            {skillGap.missing_skills.map((skill, index) => (
              <div
                key={index}
                className="flex items-center p-2 bg-gray-50 rounded"
              >
                <span className="w-3 h-3 mr-2 rounded-full bg-red-500"></span>
                <span className="font-medium">{skill.missing_skill}</span>
                <span className="ml-2 text-gray-500">({skill.category})</span>
                {skill.importance && (
                  <span className="ml-auto text-sm text-gray-600">
                    Relevance:{" "}
                    {skill.importance > 7
                      ? "High"
                      : skill.importance > 4
                      ? "Medium"
                      : "Low"}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500 p-3 bg-green-50 rounded">
            You already have all the required skills for this position! 🎉
          </p>
        )}
      </div>

      {/* Related Skills Section */}
      {skillGap.related_skills && skillGap.related_skills.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 text-lg mb-2">
            Skills You Can Leverage
          </h4>
          <div className="space-y-2">
            {skillGap.related_skills.map((skill, index) => (
              <div key={index} className="p-2 bg-blue-50 rounded">
                <div className="flex items-center">
                  <span className="font-medium text-blue-700">
                    {skill.related_skill}
                  </span>
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-4 w-4 mx-2 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 5l7 7-7 7M5 5l7 7-7 7"
                    />
                  </svg>
                  <span className="font-medium">{skill.target_skill}</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Your experience with {skill.related_skill} can help you learn{" "}
                  {skill.target_skill} faster.
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendation */}
      {skillGap.missing_skills && skillGap.missing_skills.length > 0 && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-800 mb-2">Next Steps</h4>
          <p className="text-blue-700">
            Focus on developing the skills listed above to increase your match
            for this position. Consider online courses, certifications, or
            project work to build these skills.
          </p>
        </div>
      )}
    </div>
  );
}
