import RegionPage from '../../pageObjects/region';

const REGION_NAME = 'CypressTestRegion';

describe('pageStatus', { tags: ['Test', 'Pilot'] }, () => {
  it('PageStatus', () => {
    const region = new RegionPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
    cy.title().should('eq', 'GTT Smart Cities');

    // Verify 'Choose Region' label is active when user is on Regions page
    region.searchBar().should('be.visible').should('contain.text', 'Region:');
    region
      .regionPageActive()
      .should('have.class', 'regions-layout__step ant-steps-item-active');
    region.chooseRegionIcon().should('contain.text', '1');
    region.chooseRegionTitle().should('contain.text', 'Choose Region');
    region.agencyPageInactive().should('not.have.class', 'active');

    // Verify regions search bar
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
    region.searchIcon().should('be.visible');
    region.searchBarPlaceholder().type(REGION_NAME);
    region.searchIcon().click();

    // Search Region
    region.searchRegion(REGION_NAME);

    // Verify user is on Agency page
    region.searchBar().should('be.visible').should('contain.text', 'Agency:');

    // Verify 'Choose Agency' label is active when user is on Agency page
    region.agencyPageActive().should('have.class', 'ant-steps-item-active');
    region.chooseAgencyIcon().should('contain.text', '2');
    region.chooseAgencyTitle().should('contain.text', 'Choose Agency');
    region.regionPageInactive().should('not.have.class', 'active');
  });
});
