import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import EmptyState from "../EmptyState";

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState
        title="No Data Yet"
        description="Complete an evaluation to see results."
      />
    );

    expect(screen.getByText("No Data Yet")).toBeInTheDocument();
    expect(
      screen.getByText("Complete an evaluation to see results.")
    ).toBeInTheDocument();
  });

  it("renders without description", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.getByText("Empty")).toBeInTheDocument();
  });

  it("renders action button and fires callback", async () => {
    const handleAction = jest.fn();
    render(
      <EmptyState
        title="Nothing here"
        actionLabel="Start Now"
        onAction={handleAction}
      />
    );

    const button = screen.getByRole("button", { name: /start now/i });
    expect(button).toBeInTheDocument();

    await userEvent.click(button);
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it("does not render button without actionLabel", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
