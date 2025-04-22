"use client";

import React from "react";
import Layout from "../../../components/Layout";
import SkillNetworkContainer from "../../../components/SkillNetworkContainer";

export default function SkillLibraryPage() {
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Skill Library</h1>
        <div className="mb-6">
          <p className="text-gray-600">
            Explore all skills and their relationships in our database. This
            visualization shows how different skills connect to each other
            through various relationships:
          </p>
          <ul className="list-disc ml-6 mt-2 text-gray-600">
            <li>
              <span className="font-medium">Related skills</span> - Skills that
              share a connection in the knowledge graph
            </li>
            <li>
              <span className="font-medium">Complementary skills</span> - Skills
              that work well together and enhance each other
            </li>
          </ul>
          <p className="text-gray-600 mt-2">
            Use the search and filter options to explore specific skills or
            categories. Drag nodes to rearrange the network and zoom in/out to
            explore connections.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow">
          <SkillNetworkContainer width={1000} height={800} />
        </div>
      </div>
    </Layout>
  );
}
