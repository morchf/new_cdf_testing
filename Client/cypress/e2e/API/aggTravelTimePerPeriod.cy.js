import queryParamsTestEnv from '../../fixtures/testEnvQueryparams.json'
import queryParamsPilotEnv from '../../fixtures/pilotEnvQueryparams.json'

describe('TD - Agg travel time per period', () => {
    let queryParams
    before(() => { // Login
        cy.login(Cypress.env('agencySignInUsername'), Cypress.env('agencySignInUserPassword'));
        // Select queryParams for environment
        if (`${
            Cypress.env('environment')
        }` === 'test') {
            queryParams = queryParamsTestEnv
        } else {
            queryParams = queryParamsPilotEnv
        }
        // Get token from local storage
        cy.getToken()
    })

    it('Agg travel time per period', () => {
        cy.then(() => {
            cy.request({
                    method: 'POST', url: `${
                    Cypress.env('apiUrl')
                }/metrics/travel_time/agg_travel_time_per_period?${
                    Object.entries(queryParams.aggTravelTimePerPeriodEndpoint).map(([key, value]) => `${key}=${value}`).join('&')
                }`,
                headers: {
                    'Authorization': `Bearer ${
                        Cypress.env("authToken")
                    }`
                },
                body: {
                    "selected_direction": ["inbound"],
                    "selected_timeperiod": ["peak_am"],
                    "timeperiod": [
                        {
                            "end_time": "09:00:00",
                            "label": "peak_am",
                            "start_time": "05:00:00"
                        }, {
                            "end_time": "19:00:00",
                            "label": "peak_pm",
                            "start_time": "16:00:00"
                        }
                    ]
                }
            })
        }).then((response) => {
            expect(response.status).to.eq(200);
            // Verify response schema
            cy.fixture('aggTravelTimePerPeriodSchema.json').then((ObjectSchema) => {
                expect(response.body).to.be.jsonSchema(ObjectSchema);
            })
        });
    });
})

