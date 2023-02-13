import Pagination from '../../pageObjects/pagination';

describe('Pagination', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Pagination', () => {
    const page = new Pagination();

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

    // Verify Paginatiom section is visible
    page.paginationSection().scrollIntoView();
    page.paginationSection().should('be.visible');

    // Verify pagination total text
    page
      .paginationTotalText()
      .should('be.visible')
      .contains(/1-\d+ of \d+ items/);

    // Verify page 1 is active by default, previous page arrow is disabled, next page arrow is enabled
    page.page1().should('have.class', 'ant-pagination-item-active');
    page.previousPage().should('have.attr', 'aria-disabled', 'true');

    page.routeTable().then(($table) => {
      if ($table.find('tr').length === 10) {

        // Navigate to last page and verify next page arrow is disabled
        cy.paginatelast();

        page.nextPage().should('have.attr', 'aria-disabled', 'true');
        page.previousPage().should('have.attr', 'aria-disabled', 'false');

        // Click on page 2 and verify page 2 is active, previous and next page arrorws are not disabled
        page.page2().click();
        page.page2().should('have.class', 'ant-pagination-item-active');
        page.previousPage().should('have.attr', 'aria-disabled', 'false');
        page.nextPage().should('have.attr', 'aria-disabled', 'false');
        page
          .paginationTotalText()
          .should('be.visible')
          .contains(/11-\d+ of \d+ items/);

        // Clicking on previous page arrow should navigate to page 1
        page.previousPage().click();
        page.page1().should('have.class', 'ant-pagination-item-active');
        page.previousPage().should('have.attr', 'aria-disabled', 'true');
        page.nextPage().should('have.attr', 'aria-disabled', 'false');

        // Enter page number in Go To pagination box
        page.goToPage().should('be.visible');
        page.goToPageText().type('3{enter}');
        page.page3().should('have.class', 'ant-pagination-item-active');
        page
          .paginationTotalText()
          .should('be.visible')
          .contains(/21-30 of \d+ items/);
        page.previousPage().should('have.attr', 'aria-disabled', 'false');
        page.nextPage().should('have.attr', 'aria-disabled', 'false');

        // Verify default page size is 10/page, select 20/page and verify pagination total text, rows count is equal to 20
        page.page1().click();
        page.pageSizeText().should('contain.text', '10 / page');
        page.routeTable().find('tr').should('have.length', 10);
        page.pageSizeText().click();
        page.pageSize20().click();
        page.pageSizeText().should('contain.text', '20 / page');
        page.routeTable().find('tr').should('have.length', 20);
        page.previousPage().should('have.attr', 'aria-disabled', 'true');
        page.nextPage().should('have.attr', 'aria-disabled', 'false');
        page
          .paginationTotalText()
          .should('be.visible')
          .contains(/1-20 of \d+ items/);

        // Verify clicking on next page arrow navigates to second page
        page.nextPage().click();
        page
          .paginationTotalText()
          .should('be.visible')
          .contains(/\d+-\d+ of \d+ items/); // using regex
        page.previousPage().should('have.attr', 'aria-disabled', 'false');
        page.nextPage().should('have.attr', 'aria-disabled', 'false');
      }
      else {
        page.previousPage().should('have.attr', 'aria-disabled', 'true');
        page.pageSizeText().should('contain.text', '10 / page');
      }
    })
  });
});
