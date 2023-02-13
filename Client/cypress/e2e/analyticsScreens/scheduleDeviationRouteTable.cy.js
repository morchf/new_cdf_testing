import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('ScheduleDeviationRouteTable', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
    it('Route Table', () => {
        const page = new AnalyticsSideMenuPage();
        const analyticScreensPage = new AnalyticScreensPage();

        // Login
        cy.login(
            Cypress.env('agencySignInUsername'),
            Cypress.env('agencySignInUserPassword')
        );

        // This code will run only on the Pilot environment to accept Disclaimer Modal
        cy.pilotEnvDisclaimerModal()

        cy.title().should('eq', 'GTT Smart Cities');

        // Clicking on Schedule Deviation link in sidemenu navigates to Schedule Deviation L1 screen
        page.sideMenuScheduleDeviation().click();
        page.scheduleDeviationBreadcrumb().should('be.visible');
        page.scheduleDeviationBreadcrumb().should('contain.text', 'Schedule Deviation');
        page.headingTitle().should('contain.text', 'Schedule Deviation');

        // Route Table
        analyticScreensPage.l1RouteTable().should('be.visible');
        analyticScreensPage.l1RouteHeading().should('contain.text', 'Routes');
        analyticScreensPage.l1RouteTableHeadingsCount().should('have.length', 5);
        analyticScreensPage.l1RouteTableRow().last().find('td').should('have.length', 5);
        analyticScreensPage.l1RouteTableRowsCount().should('have.length.least', 1);

        // Collect data from L1 Screen
        analyticScreensPage.l1RouteName().then(($elem) => {
            const l1RouteName = $elem.text()
            cy.wrap(l1RouteName).as('l1RouteName');
        })

        analyticScreensPage.l1RouteOnTimeArrivalsPercentage().then(($elem) => {
            const l1OnTimeArrivalPercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(l1OnTimeArrivalPercentage).as('l1OnTimeArrivalPercentage');
        })

        analyticScreensPage.l1RouteEarlyArrivalsPercentage().then(($elem) => {
            const l1EarlyArrivalPercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(l1EarlyArrivalPercentage).as('l1EarlyArrivalPercentage');
        })

        analyticScreensPage.l1RouteLateArrivalsPercentage().then(($elem) => {
            const l1LateArrivalPercentage = $elem.text().match(/(\d+)/)[1]
            cy.wrap(l1LateArrivalPercentage).as('l1LateArrivalPercentage');
        })

        analyticScreensPage.l1RouteAverageScheduleDeviation().then(($elem) => {
            const l1AverageScheduleDeviation = $elem.text().replace(/[{()}\s]/g, '')
            cy.wrap(l1AverageScheduleDeviation).as('l1AverageScheduleDeviation');
        })

        // Navigate to L2 screen
        analyticScreensPage.l1RouteName().click()
        analyticScreensPage.l2RouteName().should('be.visible');
        analyticScreensPage.l2OnTimePercentageSection().should('be.visible');
        analyticScreensPage.l2ScheduleDeviationSection().should('be.visible');

        // Collect data from L2 Screen
        analyticScreensPage.l2RouteName().then(($elem) => {
            const l2RouteName = $elem.text()
            cy.wrap(l2RouteName).as('l2RouteName');
        })

        analyticScreensPage.l2RouteOnTimeArrivalsPercentage().then(($elem) => {
            const l2OnTimePercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(l2OnTimePercentage).as('l2OnTimePercentage');
        })

        analyticScreensPage.l2RouteEarlyArrivalsPercentage().then(($elem) => {
            const l2OnEarlyPercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(l2OnEarlyPercentage).as('l2OnEarlyPercentage');
        })

        analyticScreensPage.l2RouteLateArrivalsPercentage().then(($elem) => {
            const l2OnLatePercentage = $elem.text().split('-')[1].match(/(\d+)/)[0]
            cy.wrap(l2OnLatePercentage).as('l2OnLatePercentage');
        })

        analyticScreensPage.l2RouteAverageScheduleDeviation().then(($elem) => {
            const l2ScheduleDeviation = $elem.text().replace(/[{()}\s]/g, '')
            cy.wrap(l2ScheduleDeviation).as('l2ScheduleDeviation');
        })

        // Verify L1 screen data with the L2 screen data
        cy.then(function () {
            expect(this.l1RouteName).to.equal(this.l2RouteName)
            expect(this.l1OnTimeArrivalPercentage).to.equal(this.l2OnTimePercentage)
            expect(this.l1EarlyArrivalPercentage).to.equal(this.l2OnEarlyPercentage)
            expect(this.l1LateArrivalPercentage).to.equal(this.l2OnLatePercentage)
            expect(this.l1AverageScheduleDeviation).to.equal(this.l2ScheduleDeviation)
        })

        // Navigate back to L1 screen
        analyticScreensPage.l2BackButton().click()

        // Verify L1 Screen
        analyticScreensPage.l1RouteTable().should('be.visible');
        analyticScreensPage.l1RouteHeading().should('contain.text', 'Routes');
        analyticScreensPage.l1RouteTableHeadingsCount().should('have.length', 5);
        analyticScreensPage.l1RouteTableRow().find('td').should('have.length', 5);
        analyticScreensPage.l1RouteTableRowsCount().should('have.length.least', 1);
    })
});
