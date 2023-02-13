import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('scheduleDeviationMostOnTimeRoutesTable', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
    it('Most On Time Routes Table', () => {
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

        // Most On-time Routes - Infotooltip
        analyticScreensPage.mostOntimeInfoIcon().trigger('mouseover').invoke('show')
        analyticScreensPage.mostOntimeToolTipText().should('contain', 'Routes with the lowest percentage of on-time performance')

        // Most On-time Routes
        analyticScreensPage.mostOntimeRoutesSection().should('be.visible');
        analyticScreensPage.mostOntimeRoutesHeading().should('contain.text', 'Most On-time Routes');
        analyticScreensPage.mostOnTimeColumn().should('contain.text', 'On-time');
        analyticScreensPage.mostAvgDeviationColumn().should('contain.text', 'Avg. Deviation');

        // Collect data from L1 Screen
        analyticScreensPage.l1MostOnTimeRouteName().then(($elem) => {
            const l1MostOnTimeRouteName = $elem.text()
            cy.wrap(l1MostOnTimeRouteName).as('l1MostOnTimeRouteName');
        })

        analyticScreensPage.l1MostOnTimeArrivalPercentage().then(($elem) => {
            const l1MostOnTimeArrivalPercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(l1MostOnTimeArrivalPercentage).as('l1MostOnTimeArrivalPercentage');
        })

        analyticScreensPage.l1MostOnTimeAvgDeviation().then(($elem) => {
            const l1MostOnTimeAvgDeviation = $elem.text().replace(/[{()}\s]/g, '')
            cy.wrap(l1MostOnTimeAvgDeviation).as('l1MostOnTimeAvgDeviation');
        })

        // Nevigate to L2 screen
        analyticScreensPage.l1MostOnTimeRouteName().click();
        analyticScreensPage.l2MostOnTimeRouteNameHeading().should('be.visible');
        analyticScreensPage.l2MostOntimeRoutesSection().should('be.visible');
        analyticScreensPage.l2MostScheduleDeviationSection().should('be.visible');

        // Collect data from L2 Screen
        analyticScreensPage.l2MostOnTimeRouteNameHeading().then(($elem) => {
            const l2MostOnTimeRouteNameHeading = $elem.text()
            cy.wrap(l2MostOnTimeRouteNameHeading).as('l2MostOnTimeRouteNameHeading');
        })

        analyticScreensPage.l2MostOnTimeArrivalPercentage().then(($elem) => {
            const l2MostOnTimeArrivalPercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(l2MostOnTimeArrivalPercentage).as('l2MostOnTimeArrivalPercentage');
        })

        analyticScreensPage.l2MostRouteAverageScheduleDeviation().then(($elem) => {
            const l2MostRouteAverageScheduleDeviation = $elem.text().replace(/[{()}\s]/g, '')
            cy.wrap(l2MostRouteAverageScheduleDeviation).as('l2MostRouteAverageScheduleDeviation');
        })

        // Verify L1 screen data with the L2 screen data
        cy.then(function () {
            expect(this.l1MostOnTimeRouteName).to.equal(this.l2MostOnTimeRouteNameHeading)
            expect(+this.l1MostOnTimeArrivalPercentage).to.equal(+this.l2MostOnTimeArrivalPercentage)
            expect(this.l1MostOnTimeAvgDeviation).to.equal(this.l2MostRouteAverageScheduleDeviation)
        })
    })
})

