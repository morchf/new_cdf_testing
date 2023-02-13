import AnalyticsSideMenu from '../../pageObjects/analyticsSideMenu';
import SearchRoute from '../../pageObjects/searchRoutes';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';
import Maps from '../../pageObjects/maps';

describe('searchRoutes', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('searchSingleRoute', () => {
    const page = new SearchRoute();
    const screens = new AnalyticScreensPage();
    const maps = new Maps();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal();

    // Transit Delay L1 Screen
    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

    page.routeTable().then(($table) => {
      if ($table.find('tr').length >= 1) {
        // Validate Search box
        page
          .searchRow()
          .should('be.visible')
          .should('contain.text', 'Search Routes:');
        page.searchBox().should('be.visible');
        page
          .searchPlaceholderText()
          .should('be.visible')
          .should('contain.text', 'Enter Route');

        // Click on search box and enter route number
        cy.scrollTo(0, -500);
        cy.wait(500);
        page.searchBox().click();

        // Get 1st route name
        page.l1RouteName().then(($elem) => {
          const l1RouteName = $elem.text().split(' ')[1];
          cy.wrap(l1RouteName).as('l1RouteName');
        });

        // Search for route
        cy.then(function () {
          page.searchBox().type(`${this.l1RouteName}{enter}`);
          page.l1RouteName().should('contain.text', this.l1RouteName);
          page.l1RouteName().should('contain.text', this.l1RouteName);

          // Clicking on route link should navigate to transit delay L2 screen
          page.l1RouteName().click();
          screens
            .transitDelayL2ScreenHeadingTitle()
            .should('be.visible')
            .should('contain.text', this.l1RouteName);
          screens.transitDelayL2ScreenTabViewHeader().should('be.visible');
          maps.mapContainer().should('be.visible');

          // Click on back button next to heading section title to navigate back to L1 screen
          page.backButton().click();

          // Verify user navigates back to L1 screen
          page.routeTable().should('be.visible');
          page.routeTable().find('tr').should('have.length.least', 1);
          page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
          page.searchPlaceholderText().should('contain.text', 'Enter Route');
          page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
          page.routeTable().find('tr').should('have.length.least', 1);
        });
      } else {
        page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
        page.searchPlaceholderText().should('contain.text', 'Enter Route');
        page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
      }
    });
  });

  it('searchMultipleRoutes', () => {
    const page = new SearchRoute();
    const menu = new AnalyticsSideMenu();
    const screens = new AnalyticScreensPage();
    const maps = new Maps();

    // Login
    cy.login(
      Cypress.env('agencySignInUsername'),
      Cypress.env('agencySignInUserPassword')
    );

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal();

    // Transit Delay L1 Screen
    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

    // Click on search box and enter route numbers
    cy.scrollTo(0, -500);
    cy.wait(500);
    page.searchBox().click();

    page.routeTable().then(($table) => {
      if ($table.find('tr').length >= 4) {
        // Get list of routes from routes table
        page.l1RouteName().then(($elem) => {
          const l1RouteName = $elem.text().split(' ')[1];
          cy.wrap(l1RouteName).as('l1RouteName');
        });

        page.l1RouteName2().then(($elem) => {
          const l1RouteName2 = $elem.text().split(' ')[1];
          cy.wrap(l1RouteName2).as('l1RouteName2');
        });

        page.l1RouteName3().then(($elem) => {
          const l1RouteName3 = $elem.text().split(' ')[1];
          cy.wrap(l1RouteName3).as('l1RouteName3');
        });

        page.l1RouteName4().then(($elem) => {
          const l1RouteName4 = $elem.text().split(' ')[1];
          cy.wrap(l1RouteName4).as('l1RouteName4');
        });

        // Search 4 Routes
        cy.then(function () {
          page
            .searchBox()
            .type(`${this.l1RouteName}{enter}`)
            .type(`${this.l1RouteName2}{enter}`)
            .type(`${this.l1RouteName3}{enter}`)
            .type(`${this.l1RouteName4}{enter}`);
          page.paginationTotalText().should('contain.text', '1-4 of 4 items');
          page.routeTable().find('tr').should('have.length', 4);

          // Remove one route from search list and verify only 3 routes are present
          cy.wait(500);
          page.searchBox().type('{backspace}');
          page.l1RouteName4().should('not.exist');
          cy.wait(1000);
          page.paginationTotalText().should('contain.text', '1-3 of 3 items');
          page.routeTable().find('tr').should('have.length', 3);

          // Clicking on First route link should navigate to transit delay L2 screen
          page.l1RouteName().click();
          screens
            .transitDelayL2ScreenHeadingTitle()
            .should('be.visible')
            .should('contain.text', this.l1RouteName);
          screens.transitDelayL2ScreenTabViewHeader().should('be.visible');
          maps.mapContainer().should('be.visible');

          // Click on transit delay breadcrumb on L2 screen to navigate back to L1 screen
          menu.transitDelayBreadcrumb().should('be.visible').click();

          // Verify user navigates back to L1 screen
          page.routeTable().should('be.visible');
          page.routeTable().find('tr').should('have.length.least', 1);
          page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
          page.searchPlaceholderText().should('contain.text', 'Enter Route');

          // Delete all routes from search box
          page.routeTable().should('be.visible');
          page.routeTable().find('tr').should('have.length.least', 1);
          page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
          page.searchPlaceholderText().should('contain.text', 'Enter Route');
        });
      } else {
        page.paginationTotalText().contains(/\d+-\d+ of \d+ items/);
        page.searchPlaceholderText().should('contain.text', 'Enter Route');
      }
    });
  });
});
