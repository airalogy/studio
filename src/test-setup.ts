// Test setup file for Jest
// Configure any global test settings here

// Set up fast-check configuration
import * as fc from 'fast-check';

// Configure fast-check to run at least 100 iterations for property tests
fc.configureGlobal({
  numRuns: 100,
  verbose: false,
});