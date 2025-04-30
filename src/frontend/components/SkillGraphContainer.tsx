"use client";

import React, { useState, useEffect, useMemo } from "react";
import { apiClient } from "../lib/api";
import NetworkGraph from "./NetworkGraph";
import { SkillGraphData } from "../types";

interface SkillGraphContainerProps {
  skillId: string;
  width?: number;
  height?: number;
}

const SkillGraphContainer: React.FC<SkillGraphContainerProps> = ({
  skillId,
  width = 600,
  height = 400,
}) => {
  const [graphData, setGraphData] = useState<SkillGraphData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string>(skillId);
  const [categoryFilters, setCategoryFilters] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        setLoading(true);
        // Reset error state
        setError(null);

        // Fetch graph data for the selected skill (direct connections only)
        const data = await apiClient.getSkillGraphData(selectedNodeId);

        // Deduplicate edges with the same source, target, and relationship type
        if (data.edges && data.edges.length > 0) {
          const uniqueEdges = [];
          const edgeKeys = new Set();

          for (const edge of data.edges) {
            // Skip edges with null source or target
            if (!edge.source || !edge.target) continue;

            // Create a unique key for each edge combination
            const edgeKey = `${edge.source}-${edge.target}-${edge.relationship}`;

            // Only add this edge if we haven't seen this combination before
            if (!edgeKeys.has(edgeKey)) {
              edgeKeys.add(edgeKey);
              uniqueEdges.push(edge);
            }
          }

          // Replace edges with deduplicated version
          data.edges = uniqueEdges;
        }

        setGraphData(data);

        // Extract unique categories
        if (data.nodes && data.nodes.length > 0) {
          const categories = new Set<string>();
          data.nodes.forEach((node) => {
            if (node.category) {
              categories.add(node.category);
            }
          });
          setCategoryFilters(Array.from(categories).sort());
        }
      } catch (err) {
        console.error("Error fetching skill graph data:", err);
        setError("Failed to load skill graph. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchGraphData();
  }, [selectedNodeId]);

  const handleNodeClick = (nodeId: string) => {
    if (nodeId !== selectedNodeId) {
      setLoading(true);
      setSelectedNodeId(nodeId);
    }
  };

  // Filter nodes based on selected categories
  const filteredGraphData = useMemo(() => {
    if (!graphData) return null;

    // If no categories selected, show all
    if (selectedCategories.length === 0) return graphData;

    // Filter nodes by selected categories
    const filteredNodes = graphData.nodes.filter((node) =>
      selectedCategories.includes(node.category || "")
    );

    // Get the IDs of filtered nodes
    const nodeIds = new Set(filteredNodes.map((node) => node.id));

    // Filter edges where both source and target are in filtered nodes
    const filteredEdges = graphData.edges.filter(
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    return {
      nodes: filteredNodes,
      edges: filteredEdges,
    };
  }, [graphData, selectedCategories]);

  // Toggle category selection
  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) => {
      if (prev.includes(category)) {
        return prev.filter((c) => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  // Get category counts for display
  const getCategoryCounts = useMemo(() => {
    if (!graphData || !graphData.nodes) return {};

    const counts: Record<string, number> = {};
    graphData.nodes.forEach((node) => {
      const category = node.category || "Uncategorized";
      counts[category] = (counts[category] || 0) + 1;
    });

    return counts;
  }, [graphData]);

  if (loading) {
    return (
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-medium mb-2">Skill Relationship Graph</h3>
        <div className="flex justify-center items-center h-60">
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-2"></div>
            <p className="text-gray-500">Loading skill graph...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 p-4 rounded-lg">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="bg-yellow-50 p-4 rounded-lg">
        <p className="text-yellow-600">
          No graph data available for this skill.
        </p>
      </div>
    );
  }

  const dataToDisplay = filteredGraphData || graphData;

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-2">Skill Relationship Graph</h3>

      <div className="flex justify-between mb-4">
        <div className="text-xs text-gray-500">
          {dataToDisplay.nodes.length} skills · {dataToDisplay.edges.length}{" "}
          connections
        </div>

        {categoryFilters.length > 0 && (
          <div className="flex items-center">
            <span className="text-xs text-gray-500 mr-2">Filter:</span>
            <div className="flex flex-wrap gap-1">
              {categoryFilters.map((category) => {
                const count = getCategoryCounts[category] || 0;
                const isSelected = selectedCategories.includes(category);
                return (
                  <button
                    key={category}
                    onClick={() => toggleCategory(category)}
                    className={`px-2 py-0.5 text-xs rounded ${
                      isSelected
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200 text-gray-700"
                    }`}
                  >
                    {category} ({count})
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <NetworkGraph
        skills={dataToDisplay.nodes}
        relationships={dataToDisplay.edges}
        width={width}
        height={height}
        showLabels={true}
      />
      <div className="mt-4 text-sm text-gray-500">
        <p>Click on a skill node to explore related skills.</p>
      </div>
    </div>
  );
};

export default SkillGraphContainer;
