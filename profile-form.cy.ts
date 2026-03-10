// profile-form.cy.ts
// Cypress test for Profile Form validation - 10 Essential Tests

describe('Profile Form Validation', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5173');
  });

  it('Test 1: Should show error when name is less than 3 characters', () => {
    cy.get('[data-testid="name-input"]').clear().type('Jo').blur();
    cy.get('[data-testid="name-error"]').should('be.visible');
    cy.get('[data-testid="name-error"]').should('contain', 'Name must be at least 3 characters');
  });

  it('Test 2: Should accept valid name with 3+ characters', () => {
    cy.get('[data-testid="name-input"]').clear().type('John Doe').blur();
    cy.get('[data-testid="name-error"]').should('not.exist');
  });

  it('Test 3: Should show error for invalid email format', () => {
    cy.get('[data-testid="email-input"]').clear().type('invalidemail.com').blur();
    cy.get('[data-testid="email-error"]').should('be.visible');
    cy.get('[data-testid="email-error"]').should('contain', 'Please enter a valid email address');
  });

  it('Test 4: Should show error when phone number is not exactly 10 digits', () => {
    cy.get('[data-testid="phone-input"]').clear().type('12345').blur();
    cy.get('[data-testid="phone-error"]').should('be.visible');
    cy.get('[data-testid="phone-error"]').should('contain', 'Phone number must be exactly 10 digits');
  });

  it('Test 5: Should show error when age is less than 18', () => {
    cy.get('[data-testid="age-input"]').clear().type('17').blur();
    cy.get('[data-testid="age-error"]').should('be.visible');
    cy.get('[data-testid="age-error"]').should('contain', 'Age must be at least 18');
  });

  it('Test 6: Should show error when bio exceeds 200 characters', () => {
    const longBio = 'a'.repeat(201);
    cy.get('[data-testid="bio-input"]').clear().type(longBio).blur();
    cy.get('[data-testid="bio-error"]').should('be.visible');
    cy.get('[data-testid="bio-error"]').should('contain', 'Bio must not exceed 200 characters');
  });

  it('Test 7: Should disable submit button when form is invalid', () => {
    cy.get('[data-testid="name-input"]').clear().type('Jo'); // Invalid - too short
    cy.get('[data-testid="email-input"]').clear().type('test@test.com');
    cy.get('[data-testid="phone-input"]').clear().type('1234567890');
    cy.get('[data-testid="age-input"]').clear().type('25');
    cy.get('[data-testid="save-button"]').should('be.disabled');
  });

  it('Test 8: Should enable submit button and submit successfully with all valid data', () => {
    // Fill all fields with valid data
    cy.get('[data-testid="name-input"]').clear().type('John Doe');
    cy.get('[data-testid="email-input"]').clear().type('john.doe@example.com');
    cy.get('[data-testid="phone-input"]').clear().type('1234567890');
    cy.get('[data-testid="age-input"]').clear().type('30');
    cy.get('[data-testid="bio-input"]').clear().type('Software Engineer');

    // Verify button is enabled
    cy.get('[data-testid="save-button"]').should('not.be.disabled');

    // Mock the API call
    cy.intercept('PUT', 'http://localhost:3001/api/profile', {
      statusCode: 200,
      body: { message: 'Profile updated successfully' }
    }).as('submitProfile');

    // Submit the form
    cy.get('[data-testid="save-button"]').click();

    // Verify submission
    cy.wait('@submitProfile');
    cy.get('[data-testid="success-message"]').should('be.visible');
    cy.get('[data-testid="success-message"]').should('contain', 'Profile updated successfully');
  });

  it('Test 9: Should accept valid email with various formats', () => {
    cy.get('[data-testid="email-input"]').clear().type('user.name+tag@example.co.uk').blur();
    cy.get('[data-testid="email-error"]').should('not.exist');
  });

  it('Test 10: Should accept exactly 200 characters in bio (boundary test)', () => {
    const exactBio = 'a'.repeat(200);
    cy.get('[data-testid="bio-input"]').clear().type(exactBio).blur();
    cy.get('[data-testid="bio-error"]').should('not.exist');
  });
});
