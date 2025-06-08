import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App.js";

// API 모킹
jest.mock("./api.js");

describe("App", () => {
  test("renders main components", () => {
    render(<App />);

    expect(screen.getByText(/directory tracer/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/target url list/i)).toBeInTheDocument();
  });
});
