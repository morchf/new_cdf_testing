# UI that manages CDF entities and VPS

### CDF

- Create new region/agencie/vehicle/device directly through the UI
- Delete regions/agencies/vehicles/devices
- Edit regions/agencies/vehicles/devices entity attributes
- Associate a device with a vehicle (1-to-1)
- Dissociate a device from its parent vehicle

- Expecting new feature: Import a CSV file to create/delete bulk entities

### VPS

VPS page is integrated into the UI for testing purpose but the content is currently deprecated.

### Access

Both CDF and VPS pages require a user account for the application. Contact an administrator to have a user account set up for you.

## Getting Started

### Building and Running

```sh
npm ci
npm start
```

### Linting

```sh
npm run format
```

_See [.eslintrc.yml](.eslintrc.yml) for linting configuration and [.prettierrc](.prettierrc) for formatting_

## Testing

Run both unit and functional tests

```bash
npm run test
```

### Unit Tests

Unit tests are stored under the `src` directory of the format `<file>.test.js`

```bash
npm run test:unit
```

### Functional Tests

Functional tests are stored in `Client/cypress` directory

```bash
npm run test:cypress
```

Override the runtime variables by passing in environment variables of the format `cypress_<variable>`. See [cypress.env.json](./cypress.env.json)

```bash
export cypress_launchUrl=https://cdfmanager.testgtt.com/
```
