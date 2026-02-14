import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "../ProtectedRoute";

// Mock useAuth to control auth state per test
const mockUseAuth = jest.fn();
jest.mock("../../hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

// Helper: render ProtectedRoute inside a router with a /login route
function renderWithRouter(authState: {
  isAuthenticated: boolean;
  loading: boolean;
}) {
  mockUseAuth.mockReturnValue({
    user: authState.isAuthenticated
      ? { id: "1", email: "test@example.com", display_name: "Test" }
      : null,
    loading: authState.loading,
    isAuthenticated: authState.isAuthenticated,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    hydrate: jest.fn(),
  });

  return render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <ProtectedRoute>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("shows spinner while auth is loading", () => {
    renderWithRouter({ isAuthenticated: false, loading: true });
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    renderWithRouter({ isAuthenticated: true, loading: false });
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("redirects to /login when not authenticated", () => {
    renderWithRouter({ isAuthenticated: false, loading: false });
    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });
});
