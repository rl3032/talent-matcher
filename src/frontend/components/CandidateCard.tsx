import React from "react";
import { Candidate, CandidateSkill, Skill } from "../types";
import SkillTag from "./SkillTag";
import Link from "next/link";

interface CandidateCardProps {
  candidate: Candidate;
  skills?: (CandidateSkill | Skill)[];
  matchPercentage?: number;
}

export default function CandidateCard({
  candidate,
  skills,
  matchPercentage,
}: CandidateCardProps) {
  return (
    <div className="border rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <Link
            href={`/candidates/${candidate.resume_id}`}
            className="text-xl font-semibold text-blue-600 hover:text-blue-800"
          >
            {candidate.name}
          </Link>
          <p className="text-gray-700">{candidate.title}</p>
          <p className="text-gray-500">{candidate.location}</p>
          {candidate.domain && (
            <p className="text-gray-500 text-sm">Domain: {candidate.domain}</p>
          )}

          {candidate.summary && (
            <p className="text-gray-600 text-sm mt-2 line-clamp-2">
              {candidate.summary}
            </p>
          )}
        </div>

        {matchPercentage !== undefined && (
          <div className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full font-medium text-sm">
            {Math.round(matchPercentage)}% Match
          </div>
        )}
      </div>

      {skills && skills.length > 0 && (
        <div className="mt-4">
          <p className="text-gray-700 font-medium mb-2">
            {matchPercentage ? "Matching Primary Skills:" : "Top Skills:"}
          </p>
          <div className="flex flex-wrap">
            {skills.slice(0, 5).map((skill) => (
              <SkillTag
                key={skill.skill_id}
                skill={skill}
                proficiency={
                  "level" in skill
                    ? skill.level >= 8
                      ? "Expert"
                      : skill.level >= 5
                      ? "Intermediate"
                      : "Beginner"
                    : undefined
                }
                years={"years" in skill ? skill.years : undefined}
              />
            ))}
            {skills.length > 5 && (
              <span className="text-sm text-gray-500 flex items-center ml-2">
                +{skills.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      <div className="mt-4 flex justify-end">
        <Link
          href={`/candidates/${candidate.resume_id}`}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          View Profile →
        </Link>
      </div>
    </div>
  );
}
