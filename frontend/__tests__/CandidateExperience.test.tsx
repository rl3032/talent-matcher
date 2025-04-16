import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useRouter, useSearchParams } from "next/navigation";
import CandidateDetailPage from "../app/candidates/[resume_id]/page";
import { apiClient } from "../lib/api";

// Mock the Next.js navigation hooks
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock the API client
jest.mock("../lib/api", () => ({
  apiClient: {
    getCandidate: jest.fn(),
  },
}));

// Mock the Layout component
jest.mock("../app/components/Layout", () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="layout">{children}</div>
  ),
}));

// Mock Link component
jest.mock("next/link", () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

describe("CandidateDetailPage Experience Section", () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: jest.fn(),
    });
    (useSearchParams as jest.Mock).mockReturnValue({
      get: jest.fn(),
    });
  });

  it("renders experience items with bullet points", async () => {
    // Mock API response with experience data
    (apiClient.getCandidate as jest.Mock).mockResolvedValue({
      id: "1",
      name: "John Doe",
      title: "Software Engineer",
      location: "San Francisco, CA",
      summary: "Experienced software engineer",
      experiences: [
        {
          company: "Tech Corp",
          title: "Senior Developer",
          period: "Jan 2020 - Present",
          description: [
            "Led a team of 5 developers",
            "Implemented new features",
            "Reduced bug count by 30%",
          ],
          skills: ["React", "TypeScript", "Node.js"],
        },
      ],
    });

    // Render the component
    render(<CandidateDetailPage params={{ resume_id: "1" }} />);

    // Wait for the API call to resolve
    await screen.findByText("John Doe");

    // Check for experience section
    expect(screen.getByText("Experience")).toBeInTheDocument();
    expect(screen.getByText("Tech Corp")).toBeInTheDocument();
    expect(screen.getByText("Senior Developer")).toBeInTheDocument();
    expect(screen.getByText("Jan 2020 - Present")).toBeInTheDocument();

    // Check for bullet points
    expect(screen.getByText("Led a team of 5 developers")).toBeInTheDocument();
    expect(screen.getByText("Implemented new features")).toBeInTheDocument();
    expect(screen.getByText("Reduced bug count by 30%")).toBeInTheDocument();

    // Check for skills
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.getByText("TypeScript")).toBeInTheDocument();
    expect(screen.getByText("Node.js")).toBeInTheDocument();
  });

  it("handles string description instead of array", async () => {
    // Mock API response with string description
    (apiClient.getCandidate as jest.Mock).mockResolvedValue({
      id: "1",
      name: "John Doe",
      title: "Software Engineer",
      location: "San Francisco, CA",
      summary: "Experienced software engineer",
      experiences: [
        {
          company: "Tech Corp",
          title: "Senior Developer",
          period: "Jan 2020 - Present",
          description: "Single description string",
          skills: ["React"],
        },
      ],
    });

    render(<CandidateDetailPage params={{ resume_id: "1" }} />);
    await screen.findByText("John Doe");

    expect(screen.getByText("Single description string")).toBeInTheDocument();
  });

  it("handles empty experience list", async () => {
    // Mock API response with no experiences
    (apiClient.getCandidate as jest.Mock).mockResolvedValue({
      id: "1",
      name: "John Doe",
      title: "Software Engineer",
      location: "San Francisco, CA",
      summary: "Experienced software engineer",
      experiences: [],
    });

    render(<CandidateDetailPage params={{ resume_id: "1" }} />);
    await screen.findByText("John Doe");

    // Experience section should not be rendered
    expect(screen.queryByText("Experience")).not.toBeInTheDocument();
  });

  it("handles experiences with no skills", async () => {
    // Mock API response with experience but no skills
    (apiClient.getCandidate as jest.Mock).mockResolvedValue({
      id: "1",
      name: "John Doe",
      title: "Software Engineer",
      location: "San Francisco, CA",
      summary: "Experienced software engineer",
      experiences: [
        {
          company: "Tech Corp",
          title: "Senior Developer",
          period: "Jan 2020 - Present",
          description: ["Led a team of 5 developers"],
          skills: [],
        },
      ],
    });

    render(<CandidateDetailPage params={{ resume_id: "1" }} />);
    await screen.findByText("John Doe");

    expect(screen.getByText("Experience")).toBeInTheDocument();
    expect(screen.getByText("Tech Corp")).toBeInTheDocument();

    // Skills section should not be displayed
    expect(screen.queryByText("Skills:")).not.toBeInTheDocument();
  });

  it("handles experiences with empty description array", async () => {
    // Mock API response with empty description array
    (apiClient.getCandidate as jest.Mock).mockResolvedValue({
      id: "1",
      name: "John Doe",
      title: "Software Engineer",
      location: "San Francisco, CA",
      summary: "Experienced software engineer",
      experiences: [
        {
          company: "Tech Corp",
          title: "Senior Developer",
          period: "Jan 2020 - Present",
          description: [],
          skills: ["React"],
        },
      ],
    });

    render(<CandidateDetailPage params={{ resume_id: "1" }} />);
    await screen.findByText("John Doe");

    expect(screen.getByText("Experience")).toBeInTheDocument();
    expect(screen.getByText("Tech Corp")).toBeInTheDocument();

    // No bullet points should be rendered
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
  });
});
