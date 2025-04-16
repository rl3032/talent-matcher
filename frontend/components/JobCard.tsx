import React from "react";
import { Job, JobSkill } from "../types";
import SkillTag from "./SkillTag";
import Link from "next/link";

interface JobCardProps {
  job: Job;
  skills?: JobSkill[];
  matchPercentage?: number;
}

export default function JobCard({
  job,
  skills,
  matchPercentage,
}: JobCardProps) {
  return (
    <div className="border rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div>
          <Link
            href={`/jobs/${job.job_id}`}
            className="text-xl font-semibold text-blue-600 hover:text-blue-800"
          >
            {job.title}
          </Link>
          <p className="text-gray-700">{job.company}</p>
          <p className="text-gray-500">{job.location}</p>
          {job.domain && (
            <p className="text-gray-500 text-sm">Domain: {job.domain}</p>
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
          <p className="text-gray-700 font-medium mb-2">Key Skills:</p>
          <div className="flex flex-wrap">
            {skills.slice(0, 5).map((skill) => (
              <SkillTag
                key={skill.skill_id}
                skill={skill}
                importance={skill.importance}
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
          href={`/jobs/${job.job_id}`}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          View Details →
        </Link>
      </div>
    </div>
  );
}
