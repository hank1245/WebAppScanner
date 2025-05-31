import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import ResultTable from "../../components/ResultTable";

describe("ResultTable", () => {
  test("renders component", () => {
    render(<ResultTable results={{}} />);
    expect(screen.getByText(/no scan results/i)).toBeInTheDocument();
  });
});
