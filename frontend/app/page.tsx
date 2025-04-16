import React from "react";
import Link from "next/link";
import Layout from "../components/Layout";

export default function Home() {
  return (
    <Layout>
      <div className="bg-white shadow-xl rounded-lg overflow-hidden">
        <div className="py-12 px-6 sm:px-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to TalentMatcher
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            A next-generation platform for matching candidates with jobs using
            skill graph analysis
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">
            <FeaturedCard
              title="Browse Jobs"
              description="Explore job listings and find matching candidates based on skill requirements"
              href="/jobs"
              color="bg-blue-50"
              textColor="text-blue-600"
              hoverColor="hover:bg-blue-100"
            />
            <FeaturedCard
              title="Talent Pool"
              description="View candidate profiles and match them with suitable job opportunities"
              href="/candidates"
              color="bg-green-50"
              textColor="text-green-600"
              hoverColor="hover:bg-green-100"
            />
            <FeaturedCard
              title="Skills Library"
              description="Explore the skills database and relationships between different skills"
              href="/skills"
              color="bg-purple-50"
              textColor="text-purple-600"
              hoverColor="hover:bg-purple-100"
            />
          </div>

          <div className="mt-12 px-6 py-8 bg-gray-50 rounded-lg">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
              <FeatureCard
                number="1"
                title="Skill Graph Technology"
                description="Our platform uses a knowledge graph to understand relationships between skills"
              />
              <FeatureCard
                number="2"
                title="Intelligent Matching"
                description="Match candidates with jobs based on skill similarity and complementary skills"
              />
              <FeatureCard
                number="3"
                title="Career Development"
                description="Recommend skills for candidates to acquire to qualify for desired roles"
              />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

interface FeaturedCardProps {
  title: string;
  description: string;
  href: string;
  color: string;
  textColor: string;
  hoverColor: string;
}

function FeaturedCard({
  title,
  description,
  href,
  color,
  textColor,
  hoverColor,
}: FeaturedCardProps) {
  return (
    <Link
      href={href}
      className={`block p-6 rounded-lg shadow-sm ${color} ${hoverColor} transition-colors`}
    >
      <h2 className={`text-xl font-bold ${textColor} mb-2`}>{title}</h2>
      <p className="text-gray-600">{description}</p>
      <div className={`mt-4 inline-flex items-center ${textColor} font-medium`}>
        Explore
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 ml-1"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </div>
    </Link>
  );
}

interface FeatureCardProps {
  number: string;
  title: string;
  description: string;
}

function FeatureCard({ number, title, description }: FeatureCardProps) {
  return (
    <div className="flex">
      <div className="flex-shrink-0">
        <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white text-xl font-bold">
          {number}
        </div>
      </div>
      <div className="ml-4">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <p className="mt-2 text-base text-gray-600">{description}</p>
      </div>
    </div>
  );
}
