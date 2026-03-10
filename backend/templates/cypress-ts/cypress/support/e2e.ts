// cypress/support/e2e.ts
// Support file for Cypress E2E tests
// Loads before every test file

/// <reference types="cypress" />

// Prevent TypeScript errors
declare global {
  namespace Cypress {
    interface Chainable {
      // Add custom commands here if needed
    }
  }
}

// Prevent Cypress from failing tests on uncaught exceptions
// This is useful when testing third-party libraries
Cypress.on('uncaught:exception', (err, runnable) => {
  // Return false to prevent the test from failing
  // You can add specific error handling here if needed
  console.log('Uncaught exception:', err.message);
  return false;
});

// Add custom commands if needed
// Example:
// Cypress.Commands.add('login', (email, password) => { ... })

// You can also import additional support files here
// import './commands'
