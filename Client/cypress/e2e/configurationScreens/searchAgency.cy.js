import RegionPage from '../../pageObjects/region';
import AgencyPage from '../../pageObjects/agency';

const REGION_NAME = 'CypressTestRegion';
const AGENCY_NAME = 'CypressTestAgency';

describe('searchAgency', { tags: ['Test', 'Pilot'] }, () => {
  it('SearchAgency', () => {
    const region = new RegionPage();
    const agency = new AgencyPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );
    cy.title().should('eq', 'GTT Smart Cities');

    // Verify regions search bar
    region.searchBar().should('be.visible').should('contain.text', 'Region:');
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
    region.searchIcon().should('be.visible');
    region.searchBarPlaceholder().type(REGION_NAME);
    region.searchIcon().click();

    // Search Region
    region.searchRegion(REGION_NAME);

    // Verify agency search bar
    region.searchBar().should('be.visible').should('contain.text', 'Agency:');
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
    region.searchIcon().should('be.visible');
    region.searchBarPlaceholder().type(AGENCY_NAME);
    region.searchIcon().click();

    // Search Agency
    agency.searchAgency(AGENCY_NAME);

    // Clear agency name is search box
    cy.go('back');
    region.searchBarPlaceholder().type(AGENCY_NAME);
    region.searchIcon().click();
    agency.deleteSearch(AGENCY_NAME);

    // Verify search bar displays placeholder text
    region
      .searchBarPlaceholder()
      .should('have.attr', 'placeholder', 'Please enter');
  });
});
