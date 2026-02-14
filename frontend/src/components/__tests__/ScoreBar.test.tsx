import React from "react";
import { render, screen } from "@testing-library/react";
import ScoreBar from "../ScoreBar";

describe("ScoreBar", () => {
  it("renders label and score", () => {
    render(<ScoreBar label="Situation" score={4} />);
    expect(screen.getByText("Situation")).toBeInTheDocument();
    expect(screen.getByText("4/5 — Strong")).toBeInTheDocument();
  });

  it("shows correct label for each score level", () => {
    const { rerender } = render(<ScoreBar label="Test" score={5} />);
    expect(screen.getByText("5/5 — Exceptional")).toBeInTheDocument();

    rerender(<ScoreBar label="Test" score={3} />);
    expect(screen.getByText("3/5 — Solid")).toBeInTheDocument();

    rerender(<ScoreBar label="Test" score={2} />);
    expect(screen.getByText("2/5 — Needs Work")).toBeInTheDocument();

    rerender(<ScoreBar label="Test" score={1} />);
    expect(screen.getByText("1/5 — Off-Track")).toBeInTheDocument();
  });

  it("renders dash for null score", () => {
    render(<ScoreBar label="Action" score={null} />);
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("supports custom maxScore", () => {
    render(<ScoreBar label="Custom" score={8} maxScore={10} />);
    expect(screen.getByText("Custom")).toBeInTheDocument();
    // score=8 has no label in the 1-5 map, so getScoreLabel returns ""
    expect(screen.getByText(/8\/10/)).toBeInTheDocument();
  });
});
