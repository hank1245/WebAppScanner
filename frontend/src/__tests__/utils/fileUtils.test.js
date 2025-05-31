import { downloadJSON } from "../../utils/fileUtils";

Object.defineProperty(document, "createElement", {
  value: jest.fn(() => ({ click: jest.fn() })),
});
Object.defineProperty(document.body, "appendChild", { value: jest.fn() });
Object.defineProperty(document.body, "removeChild", { value: jest.fn() });

describe("fileUtils", () => {
  test("downloadJSON exists", () => {
    expect(typeof downloadJSON).toBe("function");
  });
});
