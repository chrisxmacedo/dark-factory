import type { Config } from "jest";

const common = {
  preset: "ts-jest" as const,
  roots: ["<rootDir>/src"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/**/__tests__/**",
  ],
};

const config: Config = {
  projects: [
    {
      ...common,
      displayName: "node",
      testEnvironment: "node",
      testMatch: ["**/__tests__/**/*.test.ts"],
      transformIgnorePatterns: ["/node_modules/"],
      transform: {
        "^.+\\.[jt]sx?$": [
          "ts-jest",
          {
            tsconfig: "tsconfig.json",
          },
        ],
      },
    },
    {
      ...common,
      displayName: "jsdom",
      testEnvironment: "jsdom",
      testMatch: ["**/__tests__/**/*.test.tsx"],
      transformIgnorePatterns: ["/node_modules/"],
      transform: {
        "^.+\\.[jt]sx?$": [
          "ts-jest",
          {
            tsconfig: {
              jsx: "react-jsx",
            },
          },
        ],
      },
    },
  ],
};

export default config;
