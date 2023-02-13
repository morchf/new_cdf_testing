import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe(
  'scheduleDeviationLeastOnTimeRoutesTable',
  { tags: ['Test', 'Pilot', 'Prod'] },
  () => {
    it('Least On Time Routes Table', () => {
      const page = new AnalyticsSideMenuPage();
      const analyticScreensPage = new AnalyticScreensPage();

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

      // Least On-time Routes - Infotooltip
      analyticScreensPage
        .leastOntimeInfoIcon()
        .trigger('mouseover')
        .invoke('show');
      analyticScreensPage
        .leastOntimeToolTipText()
        .should(
          'contain',
          'Routes with the lowest percentage of on-time performance'
        );

      // Least On-time Routes
      analyticScreensPage.leastOntimeRoutesSection().should('be.visible');
      analyticScreensPage
        .leastOntimeRoutesHeading()
        .should('contain.text', 'Least On-time Routes');
      analyticScreensPage.onTimeColumn().should('contain.text', 'On-time');
      analyticScreensPage
        .avgDeviationColumn()
        .should('contain.text', 'Avg. Deviation');

      // Collect data from L1 Screen
      analyticScreensPage.l1LeastOnTimeRouteName().then(($elem) => {
        const l1LeastOnTimeRouteName = $elem.text();
        cy.wrap(l1LeastOnTimeRouteName).as('l1LeastOnTimeRouteName');
      });

      analyticScreensPage.l1LeastOnTimeArrivalPercentage().then(($elem) => {
        const l1LeastOnTimeArrivalPercentage = $elem.text().match(/(\d+)/)[0];
        cy.wrap(l1LeastOnTimeArrivalPercentage).as(
          'l1LeastOnTimeArrivalPercentage'
        );
      });

      analyticScreensPage.l1LeastOnTimeAvgDeviation().then(($elem) => {
        const l1LeastOnTimeAvgDeviation = $elem.text().replace(/[{()}\s]/g, '');
        cy.wrap(l1LeastOnTimeAvgDeviation).as('l1LeastOnTimeAvgDeviation');
      });

      // Nevigate to L2 screen
      analyticScreensPage.l1LeastOnTimeRouteName().click();
      analyticScreensPage.l2LeastOnTimeRouteNameHeading().should('be.visible');
      analyticScreensPage.l2LeastOntimeRoutesSection().should('be.visible');
      analyticScreensPage
        .l2LeastScheduleDeviationSection()
        .should('be.visible');

      // Collect data from L2 Screen
      analyticScreensPage.l2LeastOnTimeRouteNameHeading().then(($elem) => {
        const l2LeastOnTimeRouteName = $elem.text();
        cy.wrap(l2LeastOnTimeRouteName).as('l2LeastOnTimeRouteName');
      });

      analyticScreensPage.l2LeastOnTimeArrivalPercentage().then(($elem) => {
        const l2LeastOnTimeArrivalPercentage = $elem.text().match(/(\d+)/)[0];
        cy.wrap(l2LeastOnTimeArrivalPercentage).as(
          'l2LeastOnTimeArrivalPercentage'
        );
      });

      analyticScreensPage
        .l2LeastRouteAverageScheduleDeviation()
        .then(($elem) => {
          const l2LeastRouteAverageScheduleDeviation = $elem
            .text()
            .replace(/[{()}\s]/g, '');
          cy.wrap(l2LeastRouteAverageScheduleDeviation).as(
            'l2LeastRouteAverageScheduleDeviation'
          );
        });

      // Verify L1 screen data with the L2 screen data
      cy.then(function () {
        expect(this.l1LeastOnTimeRouteName).to.equal(
          this.l2LeastOnTimeRouteName
        );
        expect(+this.l1LeastOnTimeArrivalPercentage).to.equal(
          +this.l2LeastOnTimeArrivalPercentage
        );
        expect(this.l1LeastOnTimeAvgDeviation).to.equal(
          this.l2LeastRouteAverageScheduleDeviation
        );
      });
    });
  }
);
