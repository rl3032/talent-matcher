import React from "react";
import { Skill } from "../types";
import Link from "next/link";

export type ProficiencyLevel =
  | "Beginner"
  | "Intermediate"
  | "Advanced"
  | "Expert";

interface SkillTagProps {
  skill: Skill;
  proficiency?: ProficiencyLevel;
  years?: number;
  importance?: number;
  onClick?: () => void;
  linkToSkill?: boolean;
  isPrimary?: boolean;
}

export default function SkillTag({
  skill,
  proficiency,
  years,
  importance,
  onClick,
  linkToSkill = false,
  isPrimary = false,
}: SkillTagProps) {
  // Determine background color based on proficiency
  const getBgColor = () => {
    if (proficiency) {
      switch (proficiency) {
        case "Beginner":
          return "bg-blue-50 text-blue-700";
        case "Intermediate":
          return "bg-green-50 text-green-700";
        case "Advanced":
          return "bg-purple-50 text-purple-700";
        case "Expert":
          return "bg-orange-50 text-orange-700";
        default:
          return "bg-gray-100 text-gray-800";
      }
    } else if (isPrimary) {
      return "bg-indigo-100 text-indigo-800";
    } else {
      return "bg-gray-100 text-gray-800";
    }
  };

  // Font weight based on importance
  const getFontWeight = () => {
    if (importance && importance >= 8) {
      return "font-bold";
    } else if (importance && importance >= 6) {
      return "font-semibold";
    }
    return "font-medium";
  };

  // Border style for primary/secondary skills
  const getBorderStyle = () => {
    if (isPrimary) {
      return "border-2 border-indigo-300";
    }
    return "border border-gray-200";
  };

  // Generate importance indicator stars
  const getImportanceIndicator = () => {
    if (!importance) return null;

    // Convert importance to a scale of 1-5 stars
    const starCount = Math.max(1, Math.min(5, Math.round(importance / 2)));

    return (
      <div className="flex items-center ml-1">
        {[...Array(5)].map((_, i) => (
          <svg
            key={i}
            className={`w-3 h-3 ${
              i < starCount ? "text-yellow-400" : "text-gray-300"
            }`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  // Get proficiency badge
  const getProficiencyBadge = () => {
    if (!proficiency) return null;

    const badgeColors = {
      Beginner: "bg-blue-100 text-blue-800",
      Intermediate: "bg-green-100 text-green-800",
      Advanced: "bg-purple-100 text-purple-800",
      Expert: "bg-orange-100 text-orange-800",
    };

    return (
      <span
        className={`ml-1 text-xs px-1.5 py-0.5 rounded-md font-medium ${badgeColors[proficiency]}`}
      >
        {proficiency}
      </span>
    );
  };

  const TagContent = () => (
    <>
      <span className={`${getFontWeight()}`}>{skill.name}</span>
      <div className="flex items-center ml-1">{getProficiencyBadge()}</div>
      {getImportanceIndicator()}
    </>
  );

  if (linkToSkill) {
    return (
      <Link
        href={`/skills/${skill.skill_id}`}
        className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm mr-2 mb-2 ${getBgColor()} ${getBorderStyle()} hover:opacity-80 shadow-sm transition-colors`}
      >
        <TagContent />
      </Link>
    );
  }

  return (
    <div
      className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm mr-2 mb-2 ${getBgColor()} ${getBorderStyle()} cursor-pointer hover:opacity-80 shadow-sm transition-colors`}
      onClick={onClick}
    >
      <TagContent />
    </div>
  );
}
