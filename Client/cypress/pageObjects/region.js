import EntityPage from './entity';

class RegionPage extends EntityPage {
  constructor() {
    super();

    this.elements = {
      ...this.elements,
      routeTableRegionName: (regionName) =>
        cy.xpath(`//a[contains(text(),"${regionName}")]`),
      regionCheckbox: (regionName) =>
        cy.xpath(`//a[text()="${regionName}"]/@href/preceding::input[1]`),
      routeTableHref: () =>
        cy.get(
          'table > tbody > tr > td.ant-table-cell.ant-table-column-sort > a'
        ),
    };
  }

  createRegion(regionName) {
    this.elements
      .createButton()
      .should('be.visible')
      .should('contain.text', 'Create New');
    this.elements.createButton().click();
    this.elements.inputName().should('be.visible');
    this.elements.inputName().type(regionName);
    this.elements.inputDescription().type('Testing Cypress');
    this.elements.submitButton().click();
    cy.wait(5000);
    cy.on('window:alert', (str) => {
      expect(str).to.equal(`${regionName} successfully created!`);
    });
  }

  updateRegion(regionName) {
    this.elements.routeTableHref().each(($el) => {
      const value = $el.text();

      if (value === regionName) {
        this.elements.routeTableRegionName(regionName).click();
        this.elements
          .editPropertiesButton()
          .should('be.visible')
          .should('contain.text', 'Edit Properties');
        this.elements.editPropertiesButton().click();
        this.elements.editRegionDescription().type(' Changes');
        this.elements.submitButton().click();
        cy.wait(5000);
        cy.on('window:alert', (str) => {
          expect(str).to.equal(`${regionName} successfully updated!`);
        });
        this.elements
          .newRegionDescription()
          .should('contain.text', 'Testing Cypress Changes');
        this.elements.regionBreadcrumb().click();
        this.elements
          .createButton()
          .should('be.visible')
          .should('contain.text', 'Create New');
      }
    });
  }

  deleteRegion(regionName) {
    cy.wait(1000);
    cy.pagination((value) => {
      if (value === regionName) {
        this.elements.regionCheckbox(regionName).click();
        this.elements
          .deleteButton()
          .should('be.visible')
          .should('contain.text', 'Delete');
        this.elements.deleteButton().click();
        this.elements.deleteSubmitButton().click();
        this.elements.deleteOkButton().click();
      }
    });
  }

  searchRegion(regionName) {
    cy.wait(1000);
    this.elements.routeTableHref().each(($el) => {
      const value = $el.text();

      if (value === regionName) {
        this.elements.regionTableContents().find('tr').should('have.length', 1);
        this.elements.routeTableRegionName(regionName).click();
        this.elements.agencyTable().should('be.visible');
        this.elements.agencyTableTitle().should('contain.text', 'Agency');
      }
    });
  }

  deleteSearch(regionName) {
    cy.wait(1000);
    this.elements.routeTableHref().each(($el) => {
      const value = $el.text();

      if (value === regionName) {
        this.elements.regionTableContents().find('tr').should('have.length', 1);
        this.elements.deleteSearch().click();
        this.elements
          .regionTableContents()
          .find('tr')
          .should('have.length', 20);
      }
    });
  }

  gttLogo() {
    return cy.get('.logo');
  }

  opticomCloudText() {
    return cy.get('.Login');
  }

  signInButton() {
    return cy.xpath('//button[contains(text(), "Sign In")]');
  }

  dropdownButton() {
    return cy.get('a.user-menu__dropdown');
  }

  dropdownTitle() {
    return cy.get('.ant-dropdown-menu-title-content'); // '.ant-dropdown-menu-title-content'
  }

  regionTable() {
    return cy.xpath('//div[@class="ant-table-content"]');
  }

  regionTableTitle() {
    return cy.xpath('//div//h5[contains(text(), "Region")]');
  }

  regionNameAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-up ant-table-column-sorter-up active"]'
    );
  }

  regionNameDescending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-down ant-table-column-sorter-down active"]'
    );
  }

  regionTableName() {
    return cy.xpath('//span[@class="ant-table-column-title"]');
  }

  clientServicesButton() {
    return cy.xpath('//p[@class="user-menu__title"]');
  }

  signOutButton() {
    return cy.xpath('//span[contains(text(), "Sign Out")]');
  }

  searchBar() {
    return cy.xpath('//div[@class="regions-controls__search-bar"]');
  }

  regionBreadcrumb() {
    return cy.xpath('//a[contains(text(),"Regions")]');
  }

  searchBarPlaceholder() {
    return cy.xpath('//input[@class="ant-input ant-input-lg"]');
  }

  searchIcon() {
    return cy.xpath(
      '//span[@class="anticon anticon-search"]//*[local-name() = "svg"]'
    );
  }

  regionPageActive() {
    return cy.xpath(
      '//div[@class="ant-steps-item ant-steps-item-process regions-layout__step ant-steps-item-active"]'
    );
  }

  regionPageInactive() {
    return cy.xpath(
      '//div[@class="ant-steps-item ant-steps-item-finish regions-layout__step"]'
    );
  }

  chooseRegionIcon() {
    return cy.xpath('(//span[@class="ant-steps-icon"])[1]');
  }

  chooseRegionTitle() {
    return cy.xpath('(//div[@class="ant-steps-item-title"])[1]');
  }

  agencyPageActive() {
    return cy.xpath(
      '//div[@class="ant-steps-item ant-steps-item-process ant-steps-item-active"]'
    );
  }

  agencyPageInactive() {
    return cy.xpath('//div[@class="ant-steps-item ant-steps-item-wait"]');
  }

  chooseAgencyIcon() {
    return cy.xpath('(//span[@class="ant-steps-icon"])[2]');
  }

  chooseAgencyTitle() {
    return cy.xpath('(//div[@class="ant-steps-item-title"])[2]');
  }
}

export default RegionPage;
