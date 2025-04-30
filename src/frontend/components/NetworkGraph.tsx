"use client";

import React, { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { GraphNode, GraphEdge } from "../types";

interface NetworkGraphProps {
  skills: GraphNode[];
  relationships: GraphEdge[];
  width?: number;
  height?: number;
  showLabels?: boolean;
}

export default function NetworkGraph({
  skills,
  relationships,
  width = 1000,
  height = 800,
  showLabels = false,
}: NetworkGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!skills || !relationships || skills.length === 0) return;

    // Clear any previous graph
    d3.select(svgRef.current).selectAll("*").remove();

    // Convert relationships to use objects instead of ids
    const links = relationships.map((rel) => ({
      source: skills.find((s) => s.id === rel.source) || rel.source,
      target: skills.find((s) => s.id === rel.target) || rel.target,
      type: rel.relationship,
    })) as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[];

    // Create SVG container with zoom capability
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .attr("style", "max-width: 100%; height: auto;");

    // Create container group for zoom/pan
    const g = svg.append("g");

    // Add zoom behavior
    const zoom = d3
      .zoom()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom as any);

    // For large graphs, use a different layout algorithm
    const simulation = d3
      .forceSimulation(skills as d3.SimulationNodeDatum[])
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance(showLabels ? 80 : 30) // Increase distance when showing labels
      )
      .force("charge", d3.forceManyBody().strength(showLabels ? -100 : -20)) // Stronger repulsion when showing labels
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(showLabels ? 40 : 8)); // Larger collision radius when showing labels

    // Create a group for links to ensure they're drawn behind nodes
    const link = g
      .append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.4) // More transparent links
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", 1) // All links are gray
      .attr("stroke-dasharray", (d) => {
        // Use dashed lines for complementary relationships
        return (d as any).type === "complementary_to" ? "5,5" : null;
      });

    // Create a group for nodes
    const nodeGroup = g
      .append("g")
      .selectAll(".node")
      .data(skills)
      .join("g")
      .attr("class", "node")
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended) as any
      );

    // Add circles for nodes
    nodeGroup
      .append("circle")
      .attr("r", showLabels ? 6 : 5) // Slightly larger when showing labels
      .attr("fill", (d) => {
        // Use category field for coloring
        const category = d.category || "";
        if (category.toLowerCase().includes("technical")) return "#4299E1"; // Blue
        if (category.toLowerCase().includes("soft")) return "#48BB78"; // Green
        if (category.toLowerCase().includes("domain")) return "#ED8936"; // Orange
        if (category.toLowerCase().includes("tool")) return "#9F7AEA"; // Purple
        if (category.toLowerCase().includes("framework")) return "#F56565"; // Red
        if (category.toLowerCase().includes("language")) return "#38B2AC"; // Teal
        if (category.toLowerCase().includes("database")) return "#667EEA"; // Indigo
        return "#A0AEC0"; // Gray default
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    // Add text labels for nodes if showLabels is true
    if (showLabels) {
      nodeGroup
        .append("text")
        .text((d) => d.name)
        .attr("font-size", "9px")
        .attr("text-anchor", "middle")
        .attr("dy", -10)
        .attr("fill", "#4A5568")
        .attr("pointer-events", "none")
        .attr("stroke", "white")
        .attr("stroke-width", "0.3px");
    }

    // Add hover interactions
    nodeGroup
      .on("mouseover", function (event, d) {
        // Highlight the node
        d3.select(this)
          .select("circle")
          .attr("r", showLabels ? 8 : 6)
          .attr("stroke", "#000");

        // Get mouse position for tooltip
        const [x, y] = d3.pointer(event);
        setTooltipPosition({ x, y });

        // Show tooltip with the skill name
        setHoveredNode(d as GraphNode);
      })
      .on("mouseout", function () {
        // Reset node appearance
        d3.select(this)
          .select("circle")
          .attr("r", showLabels ? 6 : 5)
          .attr("stroke", "#fff");

        // Hide tooltip
        setHoveredNode(null);
      });

    // Update positions on simulation tick
    simulation.on("tick", () => {
      // Keep nodes within the visible area
      nodeGroup.attr("transform", (d: any) => {
        const x = Math.max(20, Math.min(width - 20, d.x));
        const y = Math.max(20, Math.min(height - 20, d.y));
        return `translate(${x}, ${y})`;
      });

      // Update link positions
      link
        .attr("x1", (d) =>
          Math.max(20, Math.min(width - 20, (d as any).source.x))
        )
        .attr("y1", (d) =>
          Math.max(20, Math.min(height - 20, (d as any).source.y))
        )
        .attr("x2", (d) =>
          Math.max(20, Math.min(width - 20, (d as any).target.x))
        )
        .attr("y2", (d) =>
          Math.max(20, Math.min(height - 20, (d as any).target.y))
        );
    });

    // Add legend for relationship types
    const legend = svg
      .append("g")
      .attr("transform", `translate(20, ${height - 100})`);

    const relationshipTypes = [
      { name: "Related Skills", color: "#999", dashArray: null },
      { name: "Complementary Skills", color: "#999", dashArray: "5,5" },
    ];

    relationshipTypes.forEach((type, i) => {
      const row = legend
        .append("g")
        .attr("transform", `translate(0, ${i * 20})`);

      row
        .append("line")
        .attr("x1", 0)
        .attr("y1", 10)
        .attr("x2", 20)
        .attr("y2", 10)
        .attr("stroke", type.color)
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", type.dashArray);

      row
        .append("text")
        .attr("x", 30)
        .attr("y", 10)
        .attr("dy", "0.35em")
        .attr("font-size", "12px")
        .text(type.name);
    });

    // Drag functions
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Slow down the simulation after initial layout but wait longer if showing labels
    setTimeout(
      () => {
        simulation.alphaTarget(0).alphaDecay(0.05);
      },
      showLabels ? 5000 : 2000
    );

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [skills, relationships, width, height, showLabels]);

  return (
    <div className="relative">
      <svg
        ref={svgRef}
        className="bg-white rounded-lg shadow w-full"
        style={{ maxHeight: `${height}px` }}
      ></svg>

      {hoveredNode && (
        <div
          className="absolute bg-black bg-opacity-80 text-white px-3 py-2 rounded text-sm pointer-events-none z-10"
          style={{
            left: `${tooltipPosition.x + 20}px`,
            top: `${tooltipPosition.y}px`,
            transform: "translate(0, -50%)",
            maxWidth: "250px",
          }}
        >
          <div className="font-semibold">{hoveredNode.name}</div>
          <div className="text-xs mt-1">
            Category: {hoveredNode.category || "Unknown"}
            <br />
            ID: {hoveredNode.id}
          </div>
        </div>
      )}

      {(!skills || skills.length === 0) && (
        <div className="absolute inset-0 flex justify-center items-center bg-gray-50 bg-opacity-75 rounded-lg">
          <p className="text-gray-500">No skill data available to visualize</p>
        </div>
      )}
    </div>
  );
}
