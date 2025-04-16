import React, { useRef, useEffect } from "react";
import * as d3 from "d3";

interface SkillNode {
  id: string;
  name: string;
  category: string;
}

interface SkillLink {
  source: string;
  target: string;
  type: string;
}

interface SkillGraphProps {
  skills: SkillNode[];
  relationships: SkillLink[];
  width?: number;
  height?: number;
}

export default function SkillGraph({
  skills,
  relationships,
  width = 800,
  height = 500,
}: SkillGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!skills || !relationships || skills.length === 0) return;

    // Clear any previous graph
    d3.select(svgRef.current).selectAll("*").remove();

    // Convert relationships to use objects instead of ids
    const links = relationships.map((rel) => ({
      source: skills.find((s) => s.id === rel.source) || rel.source,
      target: skills.find((s) => s.id === rel.target) || rel.target,
      type: rel.type,
    }));

    // Create a force simulation with appropriate forces
    const simulation = d3
      .forceSimulation(skills as any)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d: any) => d.id)
          .distance(100)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(40));

    // Create SVG container
    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])
      .attr("style", "max-width: 100%; height: auto;");

    // Add zoom behavior
    const g = svg.append("g");
    svg.call(
      d3
        .zoom()
        .extent([
          [0, 0],
          [width, height],
        ])
        .scaleExtent([0.5, 5])
        .on("zoom", (event) => {
          g.attr("transform", event.transform);
        }) as any
    );

    // Draw links
    const link = g
      .append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d) => ((d as any).type === "REQUIRED_BY" ? 3 : 1))
      .attr("stroke", (d) => {
        switch ((d as any).type) {
          case "RELATED_TO":
            return "#999";
          case "REQUIRES":
            return "#3182CE";
          case "SIMILAR_TO":
            return "#38A169";
          default:
            return "#999";
        }
      });

    // Create a group for nodes to ensure they're drawn on top of links
    const nodeGroup = g.append("g");

    // Create node elements with circles and labels
    const node = nodeGroup
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
    node
      .append("circle")
      .attr("r", 10)
      .attr("fill", (d) => {
        switch (d.category) {
          case "technical":
            return "#4299E1"; // blue
          case "soft":
            return "#48BB78"; // green
          case "domain":
            return "#ED8936"; // orange
          default:
            return "#A0AEC0"; // gray
        }
      });

    // Add labels
    node
      .append("text")
      .attr("dx", 15)
      .attr("dy", 5)
      .text((d) => d.name)
      .attr("font-size", "12px")
      .attr("fill", "#4A5568")
      .attr("pointer-events", "none")
      .attr("stroke", "white")
      .attr("stroke-width", "0.5px");

    // Handle node interactions
    node
      .on("mouseover", function () {
        d3.select(this)
          .select("circle")
          .transition()
          .duration(300)
          .attr("r", 15);
      })
      .on("mouseout", function () {
        d3.select(this)
          .select("circle")
          .transition()
          .duration(300)
          .attr("r", 10);
      });

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) =>
          Math.max(10, Math.min(width - 10, (d as any).source.x))
        )
        .attr("y1", (d) =>
          Math.max(10, Math.min(height - 10, (d as any).source.y))
        )
        .attr("x2", (d) =>
          Math.max(10, Math.min(width - 10, (d as any).target.x))
        )
        .attr("y2", (d) =>
          Math.max(10, Math.min(height - 10, (d as any).target.y))
        );

      node.attr(
        "transform",
        (d) =>
          `translate(${Math.max(
            10,
            Math.min(width - 10, (d as any).x)
          )}, ${Math.max(10, Math.min(height - 10, (d as any).y))})`
      );
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

    // Add a legend
    const legend = svg.append("g").attr("transform", "translate(20, 20)");

    const categories = [
      { name: "Technical Skill", color: "#4299E1", category: "technical" },
      { name: "Soft Skill", color: "#48BB78", category: "soft" },
      { name: "Domain Skill", color: "#ED8936", category: "domain" },
      { name: "Other", color: "#A0AEC0", category: "other" },
    ];

    categories.forEach((category, i) => {
      const legendRow = legend
        .append("g")
        .attr("transform", `translate(0, ${i * 20})`);

      legendRow
        .append("circle")
        .attr("cx", 10)
        .attr("cy", 10)
        .attr("r", 7)
        .attr("fill", category.color);

      legendRow
        .append("text")
        .attr("x", 25)
        .attr("y", 10)
        .attr("dy", "0.35em")
        .text(category.name)
        .attr("font-size", "12px")
        .attr("fill", "#4A5568");
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [skills, relationships, width, height]);

  return (
    <div className="skill-graph">
      <svg ref={svgRef} className="bg-white rounded-lg shadow"></svg>
      {(!skills || skills.length === 0) && (
        <div className="flex justify-center items-center h-60 bg-gray-50 rounded-lg border">
          <p className="text-gray-500">No skill data available to visualize</p>
        </div>
      )}
    </div>
  );
}
