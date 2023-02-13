import Maps from '../../pageObjects/maps';
import RouteTable from '../../pageObjects/routeTable';
import SearchRoutes from '../../pageObjects/searchRoutes';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';
import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';

describe('Maps', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Map on Transit Delay', () => {
    const maps = new Maps();
    const routes = new RouteTable();
    const searchRoutes = new SearchRoutes();
    const delay = new AnalyticScreensPage();

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

    // Route Table
    routes.transitDelayRouteTableSection().should('be.visible');
    routes.transitDelayRouteTitle().should('contain.text', 'Routes');
    searchRoutes.firstRouteLink().click();

    // TD L2 Screen - Validate Breadcrumb and Title for Route 38R
    delay.breadcrumbRouteName().should('be.visible');
    delay.breadcrumbRouteName().then(($elem) => {
      const breadcrumbRouteName = $elem.text()
      cy.wrap(breadcrumbRouteName).as('breadcrumbRouteName');
    })

    cy.then(function () {
      delay.breadcrumbRouteName().should('contain.text', this.breadcrumbRouteName);
      delay.l2ScreenHeadingTitle().should('contain.text', this.breadcrumbRouteName);
    })

    delay.l2ScreenHeadingTitle().should('be.visible');

    // TD L2 Screen Details Header
    delay.l2ScreenTabViewHeader().should('be.visible');

    // TD L2 Screen Map Container
    maps.mapContainer().scrollIntoView();
    maps.mapContainer().should('be.visible');
    maps.mapZoomIn().click();
    maps.mapContainer().should('be.visible');
    cy.wait(2000);
    maps.mapZoomOut().click();
    maps.mapContainer().should('be.visible');
    cy.wait(2000);
    maps.mapContainer().dblclick();
    maps.mapContainer().should('be.visible');
    cy.wait(2000);
  });

  it('Map on Schedule Deviation', () => {
    const maps = new Maps();
    const routes = new RouteTable();
    const delay = new AnalyticScreensPage();
    const deviation = new AnalyticsSideMenuPage();

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

    // Click Schedule Deviation link on Sidemenu to navigate to Schedule Deviation Screen
    deviation.sideMenuScheduleDeviation().click();
    deviation.scheduleDeviationBreadcrumb().should('be.visible');
    deviation
      .scheduleDeviationBreadcrumb()
      .should('contain.text', 'Schedule Deviation');
    deviation.headingTitle().should('contain.text', 'Schedule Deviation');

    // Route Table
    routes.scheduleDeviationRouteTable().scrollIntoView();
    routes.scheduleDeviationRouteTable().should('be.visible');
    routes.scheduleDeviationRouteTitle().should('contain.text', 'Routes');

    // Click on route to navigate to SD L2 screen
    let FirstRouteLink;
    delay.scheduleDeviationFirstRouteLink().each(($value) => {
      FirstRouteLink = $value.text();
    });

    delay.scheduleDeviationFirstRouteLink().click();

    let HeadingTitle;
    delay.l2ScreenHeadingTitle().each(($value) => {
      HeadingTitle = $value.text();
      expect(FirstRouteLink).to.equal(HeadingTitle);
    });

    // SD L2 Screen Tab View Header
    delay.l2ScreenTabViewHeader().should('be.visible');

    // SD L2 Screen Map Container
    maps.mapContainer().scrollIntoView();
    maps.mapContainer().should('be.visible');
    maps.mapZoomIn().click();
    maps.mapContainer().should('be.visible');
    cy.wait(2000);
    maps.mapZoomOut().click();
    maps.mapContainer().should('be.visible');
    cy.wait(2000);
    maps.mapContainer().dblclick();
    maps.mapContainer().should('be.visible');
    cy.wait(2000);
  });
});
