import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "../App";

describe("Offline AI Platform App", () => {
  it("renders authentication screen and live demo trigger when unauthenticated", () => {
    localStorage.clear();
    render(<App />);
    expect(screen.getByText("Offline AI Platform")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Account" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Launch Interactive Live Demo/i })
    ).toBeInTheDocument();
  });
});
