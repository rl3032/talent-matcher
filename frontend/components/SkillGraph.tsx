import React, { useEffect, useRef } from "react";
import * as d3 from "d3";
import { SkillGraphData } from "../types";

interface SkillGraphProps {
  data: SkillGraphData;
  width?: number;
  height?: number;
  highlightedNodeId?: string;
  onNodeClick?: (nodeId: string) => void;
  currentDepth?: number;
}

const SkillGraph: React.FC<SkillGraphProps> = ({
  data,
  width = 600,
  height = 400,
  highlightedNodeId,
  onNodeClick,
  currentDepth = 1,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  // Color scale for different relationship types
  const relationshipColorScale = d3
    .scaleOrdinal<string, string>()
    .domain([
      "related_to",
      "requires",
      "complementary_to",
      "subset_of",
      "job_related",
      "HAS_CORE_SKILL",
      "HAS_SECONDARY_SKILL",
      "REQUIRES_PRIMARY",
      "REQUIRES_SECONDARY",
      "USED_SKILL",
    ])
    .range([
      "#4299e1", // blue
      "#f56565", // red
      "#48bb78", // green
      "#9f7aea", // purple
      "#ed8936", // orange
      "#3182ce", // darker blue
      "#90cdf4", // lighter blue
      "#e53e3e", // darker red
      "#fc8181", // lighter red
      "#805ad5", // darker purple
    ]);

  // Color scale for node types (now with more categories)
  const nodeColorScale = d3
    .scaleOrdinal<string, string>()
    .domain(["skill", "highlighted"])
    .range(["#3182ce", "#f6ad55"]);

  useEffect(() => {
    if (!data || !data.nodes || !data.edges || data.nodes.length === 0) {
      return;
    }

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove();

    // Filter out disconnected nodes
    // First, create a set of all node IDs that have connections
    const connectedNodeIds = new Set<string>();

    // Always include the highlighted node
    if (highlightedNodeId) {
      connectedNodeIds.add(highlightedNodeId);
    }

    // Add all nodes that appear in edges
    data.edges.forEach((edge) => {
      // Use optional chaining and type assertions to avoid errors
      const sourceId =
        typeof edge.source === "object"
          ? (edge.source as any)?.id
          : edge.source;
      const targetId =
        typeof edge.target === "object"
          ? (edge.target as any)?.id
          : edge.target;

      if (sourceId) connectedNodeIds.add(String(sourceId));
      if (targetId) connectedNodeIds.add(String(targetId));
    });

    // Filter nodes to only include connected ones
    const filteredNodes = data.nodes.filter(
      (node) => node && node.id && connectedNodeIds.has(node.id)
    );

    // Continue with visualization using filteredNodes instead of data.nodes

    // Create the SVG
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height]);

    // Create a group for the graph
    const g = svg.append("g");

    // Add zoom behavior
    const zoom = d3
      .zoom()
      .scaleExtent([0.5, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom as any);

    // Create forces for the simulation
    const simulation = d3
      .forceSimulation(filteredNodes as any)
      .force(
        "link",
        d3
          .forceLink(data.edges)
          .id((d: any) => d.id)
          .distance(120) // Increased for better spacing
      )
      .force("charge", d3.forceManyBody().strength(-500)) // Stronger repulsion
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(50)) // Larger collision radius
      .force("x", d3.forceX(width / 2).strength(0.1)) // Help center nodes horizontally
      .force("y", d3.forceY(height / 2).strength(0.1)); // Help center nodes vertically

    // Create a defs section for filters
    const defs = svg.append("defs");

    // Create a text shadow filter for better visibility
    const filter = defs
      .append("filter")
      .attr("id", "text-shadow")
      .attr("x", "-50%")
      .attr("y", "-50%")
      .attr("width", "200%")
      .attr("height", "200%");

    // Add a white background blur
    filter
      .append("feGaussianBlur")
      .attr("in", "SourceAlpha")
      .attr("stdDeviation", "2")
      .attr("result", "blur");

    filter
      .append("feFlood")
      .attr("flood-color", "white")
      .attr("flood-opacity", "1")
      .attr("result", "color");

    filter
      .append("feComposite")
      .attr("in", "color")
      .attr("in2", "blur")
      .attr("operator", "in")
      .attr("result", "shadow");

    filter
      .append("feComposite")
      .attr("in", "SourceGraphic")
      .attr("in2", "shadow")
      .attr("operator", "over");

    // Add arrowhead marker for directed edges
    svg
      .append("defs")
      .selectAll("marker")
      .data(["end"])
      .enter()
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25) // Adjust to position the arrow properly
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#999");

    // Create a set of directly connected nodes to the highlighted node
    const directConnections = new Set<string>();

    // If we have a highlighted node and are at depth 2, identify direct connections
    if (highlightedNodeId && currentDepth === 2) {
      data.edges.forEach((edge) => {
        // Add nodes directly connected to the highlighted node
        if (edge.source === highlightedNodeId) {
          directConnections.add(edge.target);
        } else if (edge.target === highlightedNodeId) {
          directConnections.add(edge.source);
        }
      });
    }

    // Create links
    const link = g
      .append("g")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(data.edges)
      .join("line")
      .attr(
        "stroke",
        (d: any) => relationshipColorScale(d.relationship) as string
      )
      .attr("stroke-width", 2)
      .attr("marker-end", "url(#arrowhead)")
      .attr("stroke-dasharray", (d: any) => {
        // If we're only showing depth 1, all lines are solid
        if (currentDepth === 1) {
          return null;
        }

        // For depth 2, determine if this is a direct or indirect connection
        const isSourceHighlighted =
          d.source.id === highlightedNodeId || d.source === highlightedNodeId;
        const isTargetHighlighted =
          d.target.id === highlightedNodeId || d.target === highlightedNodeId;

        // Direct connection to highlighted node
        if (isSourceHighlighted || isTargetHighlighted) {
          return null; // Solid line
        }

        // Direct connection between two nodes that are both directly connected to highlighted node
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;

        if (
          directConnections.has(sourceId) &&
          directConnections.has(targetId)
        ) {
          return "5,5"; // Dotted line (less dense)
        }

        // All other connections are indirect
        return "3,3"; // Dotted line (more dense)
      });

    // Create link labels
    const linkLabel = g
      .append("g")
      .selectAll("text")
      .data(data.edges)
      .join("text")
      .text((d: any) => d.relationship.replace(/_/g, " "))
      .attr("font-size", "8px")
      .attr("text-anchor", "middle")
      .attr("dy", -5)
      .attr("fill", "#666")
      .attr("filter", "url(#text-shadow)");

    // Create nodes with different sizes based on importance
    const node = g
      .append("g")
      .selectAll("circle")
      .data(filteredNodes)
      .join("circle")
      .attr("r", (d: any) => (highlightedNodeId === d.id ? 18 : 12))
      .attr("fill", (d: any) =>
        highlightedNodeId === d.id
          ? "#f6ad55"
          : (nodeColorScale(d.type) as string)
      )
      .attr("stroke", "#fff")
      .attr("stroke-width", (d: any) => (highlightedNodeId === d.id ? 3 : 1.5))
      .call(drag(simulation) as any);

    // Add click handler
    if (onNodeClick) {
      node.on("click", (_event: any, d: any) => {
        onNodeClick(d.id);
      });
    }

    // Add node labels
    const labels = g
      .append("g")
      .selectAll("text")
      .data(filteredNodes)
      .join("text")
      .text((d: any) => d.name)
      .attr("font-size", (d: any) =>
        highlightedNodeId === d.id ? "12px" : "10px"
      )
      .attr("font-weight", (d: any) =>
        highlightedNodeId === d.id ? "bold" : "normal"
      )
      .attr("text-anchor", "middle")
      .attr("dy", -15)
      .attr("fill", (d: any) => (highlightedNodeId === d.id ? "#000" : "#333"))
      .attr("filter", "url(#text-shadow)");

    // Update positions on each tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      linkLabel
        .attr("x", (d: any) => (d.source.x + d.target.x) / 2)
        .attr("y", (d: any) => (d.source.y + d.target.y) / 2);

      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);

      // Update label positions
      labels.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
    });

    // Drag functionality
    function drag(
      simulation: d3.Simulation<d3.SimulationNodeDatum, undefined>
    ) {
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

      return d3
        .drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
    }

    // Add a legend for relationship types and connection types
    const legend = svg
      .append("g")
      .attr("transform", `translate(${width - 150}, 20)`);

    // First section - Relationship types
    legend
      .append("text")
      .attr("x", 0)
      .attr("y", -5)
      .text("Relationship Types")
      .attr("font-size", "10px")
      .attr("font-weight", "bold");

    const relationships = [
      "related_to",
      "requires",
      "complementary_to",
      "subset_of",
      "job_related",
    ];
    const displayNames = [
      "Related To",
      "Requires",
      "Complementary",
      "Subset Of",
      "Job Related",
    ];

    relationships.forEach((relationship, i) => {
      const legendRow = legend
        .append("g")
        .attr("transform", `translate(0, ${i * 20 + 10})`);

      legendRow
        .append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", 20)
        .attr("y2", 0)
        .attr("stroke", relationshipColorScale(relationship) as string)
        .attr("stroke-width", 2);

      legendRow
        .append("text")
        .attr("x", 30)
        .attr("y", 4)
        .text(displayNames[i])
        .attr("font-size", "10px");
    });

    // Second section - Connection types
    if (currentDepth === 2) {
      legend
        .append("text")
        .attr("x", 0)
        .attr("y", 130)
        .text("Connection Types")
        .attr("font-size", "10px")
        .attr("font-weight", "bold");

      // Direct connection
      const directRow = legend
        .append("g")
        .attr("transform", `translate(0, ${140})`);

      directRow
        .append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", 20)
        .attr("y2", 0)
        .attr("stroke", "#666")
        .attr("stroke-width", 2);

      directRow
        .append("text")
        .attr("x", 30)
        .attr("y", 4)
        .text("Direct Connection")
        .attr("font-size", "10px");

      // Indirect connection
      const indirectRow = legend
        .append("g")
        .attr("transform", `translate(0, ${160})`);

      indirectRow
        .append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", 20)
        .attr("y2", 0)
        .attr("stroke", "#666")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "3,3");

      indirectRow
        .append("text")
        .attr("x", 30)
        .attr("y", 4)
        .text("Indirect Connection")
        .attr("font-size", "10px");
    }

    return () => {
      simulation.stop();
    };
  }, [data, width, height, highlightedNodeId, onNodeClick]);

  return <svg ref={svgRef} className="skill-graph border rounded"></svg>;
};

export default SkillGraph;
