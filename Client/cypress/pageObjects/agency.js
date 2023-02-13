import EntityPage from './entity';

class AgencyPage extends EntityPage {
  constructor() {
    super();

    this.elements = {
      ...this.elements,
      routeTableAgencyName: (agencyName) =>
        cy.xpath(`//a[contains(text(),"${agencyName}")]`),
      agencyCheckbox: (agencyName) =>
        cy.xpath(`//a[text()="${agencyName}"]/@href/preceding::input[1]`),
      agencyTableHref: () =>
        cy.get(
          'table > tbody > tr > td.ant-table-cell.ant-table-column-sort > a'
        ),
    };
  }

  createAgency(agencyName) {
    this.elements
      .createButton()
      .should('be.visible')
      .should('contain.text', 'Create New');
    this.elements.createButton().click();
    this.elements.inputName().should('be.visible');
    this.elements.inputName().type(agencyName);
    this.elements.inputDescription().type('Testing Agency');
    this.elements.agencyPriority().click();
    this.elements.agencyPriorityLow().click();
    this.elements.agencyCode().type('100');
    this.elements.agencyCity().type('Sun City');
    this.elements.agencyState().click();
    this.elements.agencyStateCA().click();
    this.elements.agencyTimezone().click();
    this.elements.agencyTimezonePacific().click();
    this.elements.submitButton().click();
    cy.wait(5000);
    cy.on('window:alert', (str) => {
      expect(str).to.equal(`${agencyName} successfully created!`);
    });
  }

  updateAgency(agencyName) {
    this.elements.agencyTableHref().each(($el) => {
      const value = $el.text();

      if (value === agencyName) {
        this.elements.routeTableAgencyName(agencyName).click();
        cy.wait(2000);
        this.elements.agencyPropertiesTable().should('be.visible');
        this.elements
          .agencyPropertiesTableTitle()
          .should('contain.text', 'Agency Properties');
        this.elements
          .editPropertiesButton()
          .should('be.visible')
          .should('contain.text', 'Edit Properties');
        this.elements.editPropertiesButton().click();
        this.elements.inputDescription().clear().type('Testing UI Agency');
        this.elements.agencyPriority().click();
        this.elements.agencyPriorityHigh().click();
        this.elements.agencyCode().clear().type('10');
        this.elements.agencyCity().clear().type('Star City');
        this.elements.agencyState().click();
        this.elements.agencyStateAL().click();
        this.elements.agencyTimezone().click();
        this.elements.agencyTimezoneCentral().click();
        this.elements.submitButton().click();
        cy.on('window:alert', (str) => {
          expect(str).to.equal(`${agencyName} successfully updated!`);
        });
        this.elements.regionUITestBreadcrumb().click();
        this.elements.agencyTable().should('be.visible');
        this.elements
          .updatedAgencyDescription()
          .should('contain.text', 'Testing UI Agency');
        this.elements.updatedAgencyPriority().should('contain.text', 'High');
        this.elements.updatedAgencyCode().should('contain.text', '10');
        this.elements.updatedAgencyCity().should('contain.text', 'Star City');
        this.elements.updatedAgencyState().should('contain.text', 'AL');
        this.elements.updatedAgencyTimezone().should('contain.text', 'Central');
        this.elements.updatedAgencyCity().should('contain.text', 'Star City');
        this.elements.agencyCmsId().contains(/\w+.\w+.\w+.\w+.\w+/);
      }
    });
  }

  deleteAgency(agencyName) {
    cy.wait(1000);
    this.elements.agencyTableHref().each(($el) => {
      const value = $el.text();

      if (value === agencyName) {
        this.elements.agencyCheckbox(agencyName).click();
        this.elements
          .deleteButton()
          .should('be.visible')
          .should('contain.text', 'Delete');
        this.elements.deleteButton().click();
        this.elements.deleteSubmitButton().click();
        this.elements.deleteOkButton().click();
        this.elements.regionBreadcrumb().click();
        this.elements
          .createButton()
          .should('be.visible')
          .should('contain.text', 'Create New');
      }
    });
  }

  searchAgency(agencyName) {
    cy.wait(1000);
    this.elements.agencyTableHref().each(($el) => {
      const value = $el.text();

      if (value === agencyName) {
        this.elements.routeTableAgencyName(agencyName).click();
        cy.wait(2000);
        this.elements.agencyPropertiesTable().should('be.visible');
        this.elements
          .agencyPropertiesTableTitle()
          .should('contain.text', 'Agency Properties');
      }
    });
  }

  deleteSearch(agencyName) {
    cy.wait(1000);
    this.elements.agencyTableHref().each(($el) => {
      const value = $el.text();

      if (value === agencyName) {
        this.elements.deleteAgency().click();
      }
    });
  }

  agencyTableName() {
    return cy.xpath('(//span[@class="ant-table-column-title"])[1]');
  }

  agencyNameAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-up ant-table-column-sorter-up active"]'
    );
  }

  agencyNameDescending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-down ant-table-column-sorter-down active"]'
    );
  }

  agencyCity() {
    return cy.xpath('(//span[@class="ant-table-column-title"])[2]');
  }

  agencyCityAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-up ant-table-column-sorter-up active"]'
    );
  }

  agencyState() {
    return cy.xpath('(//span[@class="ant-table-column-title"])[3]');
  }

  agencyStateAscending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-up ant-table-column-sorter-up active"]'
    );
  }

  agencyStateDescending() {
    return cy.xpath(
      '(//div[@class="ant-table-column-sorters"])//span[@class="anticon anticon-caret-down ant-table-column-sorter-down active"]'
    );
  }
}

export default AgencyPage;
