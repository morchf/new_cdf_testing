import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('Verify OverallPerformance Card', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
    it('OverallPerformanceCard', () => {
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

        // Overall Performance Card
        analyticScreensPage.overallPerformanceHeader().should('contain.text', 'Overall Performance')
        analyticScreensPage.onTimeP1().should('be.visible')
        analyticScreensPage.lateP1().should('be.visible')
        analyticScreensPage.earlyP1().should('be.visible')
        analyticScreensPage.onTimeP2().should('be.visible')
        analyticScreensPage.lateP2().should('be.visible')
        analyticScreensPage.earlyP2().should('be.visible')
        analyticScreensPage.onTimeP3().should('be.visible')
        analyticScreensPage.lateP3().should('be.visible')
        analyticScreensPage.earlyP3().should('be.visible')

        // Check Infotooltip
        analyticScreensPage.infoToolTip().trigger('mouseover').invoke('show')
        analyticScreensPage.infoToolTipMessage().should('contain', 'Provides % and number of routes that are on-time, early and late')

        // Check Total Percentage = 100%
        analyticScreensPage.onTimeP2().then(($elem) => {
            const ontimePercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(ontimePercentage).as('ontimePercentage');
        })

        analyticScreensPage.lateP2().then(($elem) => {
            const latePercentage = $elem.text().match(/(\d+)/)[0]
            cy.wrap(latePercentage).as('latePercentage');
        })

        analyticScreensPage.earlyP2().then(($ele) => {
            const earlyPercentage = $ele.text().match(/(\d+)/)[0]
            cy.wrap(earlyPercentage).as('earlyPercentage');
        })

        cy.then(function () {
            const totalPer = (+this.ontimePercentage) + (+this.latePercentage) + (+this.earlyPercentage)
            expect(totalPer).to.equal(100)
        })

        // Check number of Routes
        analyticScreensPage.onTimeP3().then(($elem) => {
            const ontimeRoutes = $elem.text().match(/(\d+)/)[1]
            cy.wrap(ontimeRoutes).as('ontimeRoutes');
        })

        analyticScreensPage.onTimeP3().then(($elem) => {
            const totalOntimeRoutes = $elem.text().split('/')[1].match(/(\d+)/)[1]
            cy.wrap(totalOntimeRoutes).as('totalOntimeRoutes');
        })

        analyticScreensPage.lateP3().then(($elem) => {
            const lateRoutes = $elem.text().match(/(\d+)/)[1]
            cy.wrap(lateRoutes).as('lateRoutes');
        })

        analyticScreensPage.lateP3().then(($elem) => {
            const totalLateRoutes = $elem.text().split('/')[1].match(/(\d+)/)[1]
            cy.wrap(totalLateRoutes).as('totalLateRoutes');
        })

        analyticScreensPage.earlyP3().then(($elem) => {
            const earlyRoutes = $elem.text().match(/(\d+)/)[1]
            cy.wrap(earlyRoutes).as('earlyRoutes');
        })

        analyticScreensPage.earlyP3().then(($elem) => {
            const totalEarlyRoutes = $elem.text().split('/')[1].match(/(\d+)/)[1]
            cy.wrap(totalEarlyRoutes).as('totalEarlyRoutes')
        })

        cy.then(function () {
            const totalRoutes = (+this.ontimeRoutes) + (+this.lateRoutes) + (+this.earlyRoutes)
            expect(totalRoutes).to.equal(+this.totalOntimeRoutes)
            expect(totalRoutes).to.equal(+this.totalLateRoutes)
            expect(totalRoutes).to.equal(+this.totalEarlyRoutes)
        })
    })
})

