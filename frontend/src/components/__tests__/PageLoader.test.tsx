import React from "react";
import { render, screen } from "@testing-library/react";
import PageLoader from "../PageLoader";

describe("PageLoader", () => {
  it("renders default loading message", () => {
    render(<PageLoader />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders custom loading message", () => {
    render(<PageLoader message="Fetching evaluations..." />);
    expect(screen.getByText("Fetching evaluations...")).toBeInTheDocument();
  });

  it("renders a spinner", () => {
    render(<PageLoader />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });
});
