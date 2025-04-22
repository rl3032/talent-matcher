"use client";

import React, { useState, useEffect, useCallback } from "react";
import { apiClient } from "../lib/api";
import { SkillGraphData } from "../types";
import NetworkGraph from "./NetworkGraph";

interface SkillNetworkContainerProps {
  width?: number;
  height?: number;
}

const SkillNetworkContainer: React.FC<SkillNetworkContainerProps> = ({
  width = 1000,
  height = 800,
}) => {
  const [graphData, setGraphData] = useState<SkillGraphData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [categories, setCategories] = useState<string[]>([]);

  // Fetch the complete skills network
  useEffect(() => {
    const fetchSkillsNetwork = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await apiClient.getSkillsNetwork();
        setGraphData(data);

        // Extract unique categories from the nodes
        if (data.nodes && data.nodes.length > 0) {
          const uniqueCategories = new Set<string>();

          data.nodes.forEach((node) => {
            if (node.type) {
              // Extract category from type field
              uniqueCategories.add(node.type);
            }
          });

          setCategories(Array.from(uniqueCategories).sort());
        }
      } catch (err) {
        console.error("Error fetching skills network:", err);
        setError("Failed to load skills network. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchSkillsNetwork();
  }, []);

  // Filter the graph data based on search term and category
  const filteredGraphData = useCallback(() => {
    if (!graphData) return null;

    if (!searchTerm && selectedCategory === "all") return graphData;

    const searchTermLower = searchTerm.toLowerCase();

    // Filter nodes based on search term and category
    const filteredNodes = graphData.nodes.filter((node) => {
      const nameMatch = node.name.toLowerCase().includes(searchTermLower);
      const categoryMatch =
        selectedCategory === "all" ||
        (node.type && node.type === selectedCategory);
      return nameMatch && categoryMatch;
    });

    // Get the IDs of filtered nodes
    const nodeIds = new Set(filteredNodes.map((node) => node.id));

    // Only include edges where both source and target are in the filtered nodes
    const filteredEdges = graphData.edges.filter(
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    return {
      nodes: filteredNodes,
      edges: filteredEdges,
    };
  }, [graphData, searchTerm, selectedCategory]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Skills Network</h2>
        </div>
        <div className="flex justify-center items-center h-80">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-2"></div>
            <p className="text-gray-500">Loading skills network...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 p-4 rounded-lg">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  const filtered = filteredGraphData();

  if (!filtered || !filtered.nodes || filtered.nodes.length === 0) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Skills Network</h2>
          <div className="flex space-x-4">
            <input
              type="text"
              placeholder="Search skills..."
              className="px-3 py-2 border rounded-md"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="px-3 py-2 border rounded-md bg-white"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category === "skill" ? "General Skill" : category}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg">
          <p className="text-yellow-600">
            No skills found matching your criteria.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <h2 className="text-xl font-semibold mr-4">Skills Network</h2>
          <span className="text-sm text-gray-500">
            {filtered.nodes.length} skills · {filtered.edges.length} connections
          </span>
        </div>
        <div className="flex space-x-4">
          <input
            type="text"
            placeholder="Search skills..."
            className="px-3 py-2 border rounded-md"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="px-3 py-2 border rounded-md bg-white"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category === "skill" ? "General Skill" : category}
              </option>
            ))}
          </select>
        </div>
      </div>

      <NetworkGraph
        skills={filtered.nodes}
        relationships={filtered.edges}
        width={width}
        height={height}
        showLabels={true}
      />

      <div className="mt-6 text-sm text-gray-500">
        <p>
          Zoom and pan to explore the network. You can drag nodes to rearrange
          them.
        </p>
      </div>
    </div>
  );
};

export default SkillNetworkContainer;
