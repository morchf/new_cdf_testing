import AnalyticsSideMenuPage from '../../pageObjects/analyticsSideMenu';
import AnalyticScreensPage from '../../pageObjects/analyticScreens';

describe('scheduleDeviationHeadingSection', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
    it('Heading Section', () => {
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

        // Check Schedule Deviation Infotooltip
        analyticScreensPage.headingTitleInfoIcon().trigger('mouseover').invoke('show');
        analyticScreensPage.scheduleDeviationHeadingToolTipText().should('contain', 'Provides an overview for all routes in accordance with the schedule');

        // Check Date Range Infotooltip
        analyticScreensPage.scheduleDeviationHeadingDateInfoIcon().trigger('mouseover').invoke('show');
        analyticScreensPage.scheduleDeviationHeadingDateToolTipText().should('contain', 'Selectable dates correspond to available data for the selected timeperiod. The date range can span a maximum of 90 days');

        // Validate Schedule Deviation L1 Screen Heading Section Elements
        analyticScreensPage.headingTitle().should('be.visible');
        analyticScreensPage.headingTitle().should('contain.text', 'Schedule Deviation');
        analyticScreensPage.scheduleDeviationHeadingDirectionFilter().should('be.visible');
        analyticScreensPage.scheduleDeviationHeadingDateRangeFilter().should('be.visible');
        analyticScreensPage.scheduleDeviationHeadingTimeFilter().should('be.visible');

        // Validate dropdown elements in each filter
        analyticScreensPage.directionFilterText().should('contain.text', 'Inbound');
        analyticScreensPage.directionFilterText().click();
        analyticScreensPage
            .outboundDirectionText()
            .should('be.visible')
            .should('contain.text', 'Outbound');
        analyticScreensPage.allDirectionText().should('be.visible').should('contain.text', 'All');
        analyticScreensPage.datePickerStartDate().should('be.visible');
        analyticScreensPage.datePickerRange().click({ force: true });
        analyticScreensPage.datePickerContainer().should('be.visible');
        analyticScreensPage
            .scheduleDeviationHeadingPeakAmText()
            .invoke('text')
            .should('match', /Peak AM\s.(\d+)?\d+:\d+\d+ - (\d+)?\d+:\d+\d+/)
        analyticScreensPage
            .scheduleDeviationHeadingPeakAmText().click()
        analyticScreensPage
            .scheduleDeviationHeadingPeakPmText()
            .invoke('text')
            .should('match', /Peak PM\s.(\d+)?\d+:\d+\d+ - (\d+)?\d+:\d+\d+/)
        analyticScreensPage
            .offPeakText()
            .should('be.visible')
            .should('contain.text', 'Off-Peak (not peak or weekends)');
        analyticScreensPage
            .weekendText()
            .should('be.visible')
            .should('contain.text', 'Weekends (Saturday & Sunday)');
        analyticScreensPage.allTimeText().should('be.visible').should('contain.text', 'All');
    })
})

