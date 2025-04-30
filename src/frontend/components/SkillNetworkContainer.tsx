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
            if (node.category) {
              // Extract category field
              uniqueCategories.add(node.category);
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
        (node.category && node.category === selectedCategory);
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

  // Get category counts for display
  const getCategoryCounts = useCallback(() => {
    if (!graphData || !graphData.nodes) return {};

    const counts: Record<string, number> = {};
    graphData.nodes.forEach((node) => {
      const category = node.category || "Uncategorized";
      counts[category] = (counts[category] || 0) + 1;
    });

    return counts;
  }, [graphData]);

  const categoryColors = {
    Technical: "#4299E1", // Blue
    Soft: "#48BB78", // Green
    Domain: "#ED8936", // Orange
    Tool: "#9F7AEA", // Purple
    Framework: "#F56565", // Red
    Language: "#38B2AC", // Teal
    Database: "#667EEA", // Indigo
  };

  // Default color for categories not in the map
  const getColorForCategory = (category: string) => {
    return categoryColors[category] || "#A0AEC0"; // Gray default
  };

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
          </div>
        </div>

        {/* Category filter badges */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            <button
              className={`px-3 py-1 text-xs rounded-full ${
                selectedCategory === "all"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-200 text-gray-700"
              }`}
              onClick={() => setSelectedCategory("all")}
            >
              All
            </button>
            {categories.map((category) => {
              const count = getCategoryCounts()[category] || 0;
              return (
                <button
                  key={category}
                  className={`px-3 py-1 text-xs rounded-full flex items-center ${
                    selectedCategory === category
                      ? "bg-blue-500 text-white"
                      : "bg-gray-200 text-gray-700"
                  }`}
                  onClick={() => setSelectedCategory(category)}
                >
                  <span
                    className="w-2 h-2 rounded-full mr-1"
                    style={{ backgroundColor: getColorForCategory(category) }}
                  ></span>
                  {category || "Uncategorized"} ({count})
                </button>
              );
            })}
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
        </div>
      </div>

      {/* Category filter badges */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          <button
            className={`px-3 py-1 text-xs rounded-full ${
              selectedCategory === "all"
                ? "bg-blue-500 text-white"
                : "bg-gray-200 text-gray-700"
            }`}
            onClick={() => setSelectedCategory("all")}
          >
            All
          </button>
          {categories.map((category) => {
            const count = getCategoryCounts()[category] || 0;
            return (
              <button
                key={category}
                className={`px-3 py-1 text-xs rounded-full flex items-center ${
                  selectedCategory === category
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-700"
                }`}
                onClick={() => setSelectedCategory(category)}
              >
                <span
                  className="w-2 h-2 rounded-full mr-1"
                  style={{ backgroundColor: getColorForCategory(category) }}
                ></span>
                {category || "Uncategorized"} ({count})
              </button>
            );
          })}
        </div>
      </div>

      <NetworkGraph
        skills={filtered.nodes}
        relationships={filtered.edges}
        width={width}
        height={height}
        showLabels={true}
      />

      {/* Legend for categories */}
      <div className="mt-6 p-4 border rounded-lg bg-gray-50">
        <h3 className="text-sm font-medium mb-2">Skill Categories</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Object.entries(categoryColors).map(([category, color]) => (
            <div key={category} className="flex items-center">
              <span
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: color }}
              ></span>
              <span className="text-xs">{category}</span>
            </div>
          ))}
          <div className="flex items-center">
            <span
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: "#A0AEC0" }}
            ></span>
            <span className="text-xs">Other</span>
          </div>
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-500">
        <p>
          Zoom and pan to explore the network. You can drag nodes to rearrange
          them.
        </p>
      </div>
    </div>
  );
};

export default SkillNetworkContainer;
