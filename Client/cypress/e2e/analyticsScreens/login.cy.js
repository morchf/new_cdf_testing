import RegionPage from '../../pageObjects/region';

describe('LoginTest', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Login and Logout', () => {
    const page = new RegionPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    // Transit Delay L1 Screen
    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

    // Logout
    page.dropdownButton().click();
    page.dropdownTitle().should('contain.text', 'Sign Out');
    page.dropdownTitle().click();

    // Validate user is on Login screen
    page.gttLogo().should('be.visible');
    page.opticomCloudText().should('contain.text', 'Opticom Cloud');
    page.signInButton().should('contain.text', 'Sign In');
  });
});
