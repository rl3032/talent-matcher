"use client";

import React, { useState, useEffect } from "react";
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

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium mb-2">Skill Relationship Graph</h3>

      <div className="flex justify-end mb-4">
        <div className="text-xs text-gray-500">
          {graphData.nodes.length} skills · {graphData.edges.length} connections
        </div>
      </div>

      <NetworkGraph
        skills={graphData.nodes}
        relationships={graphData.edges}
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
