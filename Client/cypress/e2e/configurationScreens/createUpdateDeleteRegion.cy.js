import RegionPage from '../../pageObjects/region';

const REGION_NAME = 'CypressUITest';

describe('createRegion', { tags: ['Test', 'Pilot'] }, () => {
  it('Region', () => {
    const page = new RegionPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
    cy.title().should('eq', 'GTT Smart Cities');

    // Create Region
    page.createRegion(REGION_NAME);

    // Update Region
    page.updateRegion(REGION_NAME);

    // Delete Region
    page.deleteRegion(REGION_NAME);
  });
});
