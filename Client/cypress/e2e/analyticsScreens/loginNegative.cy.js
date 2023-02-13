describe('LoginNegativeTest', { tags: ['Test', 'Pilot', 'Prod'] }, () => {
  it('Negative Test', () => {
    cy.visit(Cypress.env('launchUrl'));
    cy.get('[type=button]').should('contain.text', 'Sign In');
    cy.get('[type=button]').click();

    cy.origin(Cypress.env('cognitoUrl'), () => {
      cy.get('.banner-customizable').should('be.visible');
      cy.get('.visible-lg #signInFormUsername').type('jk_agency');
      cy.get('.visible-lg #signInFormPassword').type('Joshna12345');
      cy.get('.visible-lg [type="Submit"]').click();
      cy.get('.visible-lg #loginErrorMessage').should(
        'contain.text',
        'Incorrect username or password.'
      );
      cy.wait(5000);
      cy.get('.visible-lg #signInFormUsername').type(
        Cypress.env('agencySignInUsername')
      );
      cy.get('.visible-lg #signInFormPassword').type(
        Cypress.env('agencySignInUserPassword')
      );
      cy.get('.visible-lg [type="Submit"]').click();
    });

    // This code will run only on the Pilot environment to accept Disclaimer Modal
    cy.pilotEnvDisclaimerModal()

    cy.title().should('eq', 'GTT Smart Cities');
    cy.url().should('include', 'transit-delay');

  });
});
