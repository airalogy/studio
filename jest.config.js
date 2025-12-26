module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': ['ts-jest', { useESM: true }],
  },
  transformIgnorePatterns: [
    'node_modules/(?!(unified|remark.*|rehype.*|micromark.*|unist.*|mdast.*|hast.*|vfile.*|bail|trough|zwitch|property-information|space-separated-tokens|comma-separated-tokens|web-namespaces|html-void-elements|ccount|escape-string-regexp|markdown-table|character-entities|decode-named-character-reference|trim-lines)/)',
  ],
  extensionsToTreatAsEsm: ['.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
  ],
  setupFilesAfterEnv: ['<rootDir>/src/test-setup.ts'],
};