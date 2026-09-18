import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
  // ADR-012: the API key lives in sessionStorage only; tests must not leak
  // session state between cases.
  sessionStorage.clear();
});
