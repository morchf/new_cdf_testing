import RegionPage from '../../pageObjects/region';
import AgencyPage from '../../pageObjects/agency';

const REGION_NAME = 'RegionUITest';
const AGENCY_NAME = 'AgencyUITest';

describe('createRegion', { tags: ['Test', 'Pilot'] }, () => {
  it('Region', () => {
    const region = new RegionPage();
    const agency = new AgencyPage();

    // Login
    cy.login(
      Cypress.env('adminSignInUsername'),
      Cypress.env('adminSignInUserPassword')
    );

    // Create Region
    region.createRegion(REGION_NAME);

    // Navigate to Regions Page
    region.searchBarPlaceholder().type(REGION_NAME);
    region.searchIcon().click();
    region.searchRegion(REGION_NAME);

    // Create Agency
    agency.createAgency(AGENCY_NAME);

    // Update Agency
    agency.updateAgency(AGENCY_NAME);

    // Delete Agency
    agency.deleteAgency(AGENCY_NAME);

    // Delete Region
    region.deleteRegion(REGION_NAME);
  });
});
