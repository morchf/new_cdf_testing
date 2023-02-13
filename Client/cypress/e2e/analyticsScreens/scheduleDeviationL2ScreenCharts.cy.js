import RouteTable from '../../pageObjects/routeTable';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';
import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';

describe(
  'scheduleDeviationL2ScreenCharts',
  { tags: ['Test', 'Pilot', 'Prod'] },
  () => {
    it('scheduleDeviationL2ScreenCharts', () => {
      const table = new RouteTable();
      const screens = new AnalyticScreensPage();
      const page = new AnalyticsSideMenuPage();

      // Login
      cy.login(
        Cypress.env('agencySignInUsername'),
        Cypress.env('agencySignInUserPassword')
      );

      // This code will run only on the Pilot environment to accept Disclaimer Modal
      cy.pilotEnvDisclaimerModal();

      cy.title().should('eq', 'GTT Smart Cities');

      // Clicking on Schedule Deviation link in sidemenu navigates to Schedule Deviation L1 screen
      page.sideMenuScheduleDeviation().click();
      page.scheduleDeviationBreadcrumb().should('be.visible');
      page
        .scheduleDeviationBreadcrumb()
        .should('contain.text', 'Schedule Deviation');
      page.headingTitle().should('contain.text', 'Schedule Deviation');
      table.scheduleDeviationRouteTable().should('be.visible');
      table.scheduleDeviationRouteTitle().should('contain.text', 'Routes');

      // Get l1FirstRouteLink name
      screens.scheduleDeviationFirstRouteLink().then(($elem) => {
        const l1FirstRouteLink = $elem.text();
        cy.wrap(l1FirstRouteLink).as('l1FirstRouteLink');
      });

      // Click on 1st Route.
      screens.scheduleDeviationFirstRouteLink().click();

      // verify breadcrumbs,Map and title on L2 screen.
      page.scheduleDeviationBreadcrumb().should('be.visible');
      page
        .scheduleDeviationBreadcrumb()
        .should('contain.text', 'Schedule Deviation');
      screens.scheduleDeviationMap().should('be.visible');

      // Assert Route name breadcrumb
      cy.then(function () {
        page
          .scheduleDeviationRouteNameBreadcrumb()
          .should('contain.text', this.l1FirstRouteLink);
      });

      // Get L2 page Route Heading
      screens.headingTitle().then(($elem) => {
        const routeHeadingTitle = $elem.text();
        cy.wrap(routeHeadingTitle).as('routeHeadingTitle');
      });

      // Check l1FirstRouteLink is equal to L2 page Route Heading
      cy.then(function () {
        expect(this.l1FirstRouteLink).to.equal(this.routeHeadingTitle);
      });

      // Verify tab view headers are visible
      screens.l2OnTimePercentageSection().should('be.visible');
      screens.l2ScheduleDeviationSection().should('be.visible');

      // Check On-Time Percentage tab is active by default
      screens
        .l2OnTimePercentageSection()
        .should('have.class', 'ant-radio-button-checked');

      // Verify "On-Time Percentage by Day" and "On-Time Percentage by Stop" charts are visible
      screens.l2ScheduleDeviationSectionChart1().should('be.visible');
      screens.l2ScheduleDeviationSectionChart2().should('be.visible');

      // Assert "On-Time Percentage by Day" and "On-Time Percentage by Stop" headings
      cy.then(function () {
        screens
          .l2scheduleDeviationGraph1H3()
          .should(
            'contain.text',
            `On-Time Percentage by Day  on ${this.routeHeadingTitle}`
          );
        screens
          .l2scheduleDeviationGraph2H3()
          .should(
            'contain.text',
            `On-Time Percentage by Stop  on ${this.routeHeadingTitle}`
          );
      });

      // Click on Schedule Deviation Tab
      screens.l2ScheduleDeviationSection().click({ force: true });

      // Verify "Schedule Deviation by Day" and "Schedule Deviation by Stop" charts are visible
      screens.l2ScheduleDeviationSectionChart1().should('be.visible');
      screens.l2ScheduleDeviationSectionChart2().should('be.visible');

      // Assert "Schedule Deviation by Day" and "Schedule Deviation by Stop" charts Headings.
      cy.then(function () {
        screens
          .l2scheduleDeviationGraph1H3()
          .should(
            'contain.text',
            `Schedule Deviation by Day  on ${this.routeHeadingTitle}`
          );
        screens
          .l2scheduleDeviationGraph2H3()
          .should(
            'contain.text',
            `Schedule Deviation by Stop  on ${this.routeHeadingTitle}`
          );
      });

      // Verify Inbound button is active by default
      screens.directionFilterText().should('contain.text', 'Inbound');
      screens.directionFilterText().click();

      // Click on Outbound menu
      screens.directionOutboundFilterText().click();

      // Verify "Schedule Deviation by Day" and "Schedule Deviation by Stop" charts are visible
      screens.scheduleDeviationMap().should('be.visible');
      screens.l2ScheduleDeviationSectionChart1().should('be.visible');
      screens.l2ScheduleDeviationSectionChart2().should('be.visible');

      // Assert "Schedule Deviation by Day" and "Schedule Deviation by Stop" charts Headings.
      cy.then(function () {
        screens
          .l2scheduleDeviationGraph1H3()
          .should(
            'contain.text',
            `Schedule Deviation by Day  on ${this.routeHeadingTitle}`
          );
        screens
          .l2scheduleDeviationGraph2H3()
          .should(
            'contain.text',
            `Schedule Deviation by Stop  on ${this.routeHeadingTitle}`
          );
      });
    });
  }
);
