import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';

describe('analyticsSideMenu', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('sideMenuItems', () => {
    const page = new AnalyticsSideMenuPage();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    cy.title().should('eq', 'GTT Smart Cities');

    // Validate sidemenu elements
    page.sideMenuIcon().should('be.visible');
    page.sideMenuTitle().should('be.visible');
    page.sideMenuTitle().should('contain.text', 'ANALYTICS');
    page.sideSubMenu().should('be.visible');
    page.sideMenuTitle().click();
    page.sideMenuTransitDelay().should('not.be.visible');
    page.sideMenuTitle().click();
    page.sideMenuTransitDelay().should('be.visible');
    page.transitDelayBreadcrumb().should('be.visible');
    page.transitDelayBreadcrumb().should('contain.text', 'Transit Delay');

    // Clicking on Schedule Deviation link in sidemenu navigates to Schedule Deviation L1 screen
    page.sideMenuScheduleDeviation().click();
    page.scheduleDeviationBreadcrumb().should('be.visible');
    page
      .scheduleDeviationBreadcrumb()
      .should('contain.text', 'Schedule Deviation');
    page.headingTitle().should('contain.text', 'Schedule Deviation');

    // Clicking on Transit Delay link in sidemenu navigates to Transit Delay L1 screen
    page.sideMenuTransitDelay().click();
    page.transitDelayBreadcrumb().should('be.visible');
    page.transitDelayBreadcrumb().should('contain.text', 'Transit Delay');
    page.headingTitle().should('contain.text', 'Transit Delay');
  });
});
