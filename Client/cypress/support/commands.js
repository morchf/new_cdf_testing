// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

// Login
Cypress.Commands.add('login', (username, password) => {
  cy.visit(Cypress.env('launchUrl'));
  cy.url().should('include', Cypress.env('launchUrl').split('/')[2]);
  cy.get('.logo').should('be.visible');
  cy.get('.Login').should('contain.text', 'Opticom Cloud');
  cy.get('[type=button]').should('contain.text', 'Sign In');
  cy.get('[type=button]').click();

  cy.origin(
    Cypress.env('cognitoUrl'),
    { args: { username, password } },
    ({ username, password }) => {
      cy.get('.banner-customizable').should('be.visible');
      cy.get('.visible-lg #signInFormUsername').type(username);
      cy.get('.visible-lg #signInFormPassword').type(password);
      cy.get('.visible-lg [type="Submit"]').click();
    }
  );
});

// Get Authorization Token
Cypress.Commands.add('getToken', () => {
  cy.wait(2000).then(() => {
    const token = localStorage.getItem(`${Cypress.env('jwtTokenKey')}`)
    Cypress.env("authToken", token)
  })
})

// Paginate to find an entity on configuration screens
// (This command is to navigate through configuration screens pages and find an entity)

Cypress.Commands.add('pagination', (callback) => {
  cy.xpath('//li[contains(text(),"1-20 of ")]').each(($el) => {
    const value = $el.text()[8] + $el.text()[9];

    for (let i = 1; i < value / 20; i++) {
      cy.get('.ant-pagination-next')
        .should('have.attr', 'aria-disabled', 'false')
        .each(() => {
          cy.get(
            'table > tbody > tr > td.ant-table-cell.ant-table-column-sort > a'
          ).each(($el) => {
            callback($el.text());
          });
          cy.xpath('//li[@title="Next Page"]/button').click();
        });
    }
  });
});

// Navigate to the last page on configuration screens
// (This command is used to navigate to last page)

Cypress.Commands.add('paginatetolastoncdf', (callback) => {
  cy.xpath('//li[contains(text(),"1-20 of ")]').each(($el) => {
    const value = $el.text()[8] + $el.text()[9];

    for (let i = 1; i < value / 20; i++) {
      cy.get('.ant-pagination-next')
        .should('have.attr', 'aria-disabled', 'false')
        .each(($el) => {
          cy.xpath('//li[@title="Next Page"]/button').click();
        });
    }
  });
});

// Date Picker
Cypress.Commands.add('datepicker', (startDate, endDate) => {
  cy.xpath('//div[@class="ant-picker ant-picker-range"]').click();
  cy.xpath('//div[@class="ant-picker-input ant-picker-input-active"]').click();
  cy.xpath('//input[@placeholder="Start date"]').clear();
  cy.xpath(
    `//td[@title="${startDate}" and contains(@class, 'ant-picker-cell-in-view')]`
  ).click();
  cy.xpath('//div[@class="ant-picker-input ant-picker-input-active"]').click();
  cy.xpath('//input[@placeholder="End date"]').clear();
  cy.xpath(
    `//td[@title="${endDate}" and contains(@class, 'ant-picker-cell-in-view')]`
  ).click();
  cy.wait(2000);
  cy.xpath('//input[@placeholder="Start date"]').should(
    'contain.value',
    startDate
  );
  cy.xpath('//input[@placeholder="End date"]').should('contain.value', endDate);
});

// pilotEnvModule
Cypress.Commands.add('pilotEnvDisclaimerModal', () => {
  if (Cypress.env('launchUrl').includes('pilotgtt')) {
    cy.get('.ant-btn-primary').click();
  }
});

// Navigate to last page on analytic screens
// (This command is used to navigate to last page)

Cypress.Commands.add('paginatelast', (callback) => {
  cy.xpath('//li[contains(text(),"1-10 of ")]').each(($el) => {
    const value = $el.text()[8] + $el.text()[9];

    for (let i = 0; i < value / 10; i++) {
      cy.get('.ant-pagination-next')
        .should('have.attr', 'aria-disabled', 'false')
        .each(($el) => {
          cy.xpath('//li[@title="Next Page"]/button')
            .should('be.visible')
            .click();
        });
      cy.wait(500);
    }
  });
});
