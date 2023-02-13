import RegionPage from '../../pageObjects/region';

describe('LoginConfigurationScreen', { tags: ['Test', 'Pilot'] }, () => {
  it('Login', () => {
    const region = new RegionPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
    cy.title().should('eq', 'GTT Smart Cities');

    // Verify region's table is visible
    region.regionTable().should('be.visible');
    region.regionTableTitle().should('contain.text', 'Region');

    // Verify sign out button is visible
    region.clientServicesButton().should('be.visible').click();
    region
      .signOutButton()
      .should('be.visible')
      .should('contain.text', 'Sign Out')
      .click();

    // Verify user navigates back to login screen
    cy.url().should('include', '/login');
    region.gttLogo().should('be.visible');
    region.signInButton().should('be.visible');
  });
});
