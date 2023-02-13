# Smart City Platform
Smart City Platform components and infrastructure.

## Repository structure
Branches are based on the [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) model. A quick summary:

- The primary long-lived branches are `develop`, `test`, and `master`.
- The tip of `master` represents the latest released version.
- The tip of `test` represents the latest version under test. This branch is automatically deployed to the `gtttest` account in AWS.
- The tip of `develop` represents the latest state of development work. This branch is automatically deployed to the `gttdev` account in AWS.
- Ephemeral topic branches are created from `develop`. These branches represent work in progress and must follow specific naming and formatting rules to properly connect to Jira, our project tracking tool. The rules are as follows:
  - The name of a feature branch is prefixed with `feature-` and suffixed with the key of the story from Jira, e.g. `SCP-42`. The key is case sensitive, so in this example, the branch must be named `feature-SCP-42`.
  - The commits on a feature branch should reference the key of the relevant subtask before any other text in the title (the first line) of the commit message, e.g.
    ```
    SCP-142 I did a thing

    It has some details
    ```
    If the story doesn't have any subtasks, then reference the story key instead.

    Don't add brackets `[]` or other symbols around the key. For the advanced user, this is the [Smart Commit syntax](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html) which can be used to do [all](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-commentComment) [kinds](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-timeTime) [of](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-transitionWorkflowtransitions) [things](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-Advancedexamples) in Jira.
- Ephemeral release branches are created from `test` and have names prefixed with `release-`. Release branches are ultimately merged into `master` to become the latest release.

## Contributing
Topic branches are created from `develop` and merged back into `develop` using pull requests. When you are finished with your work, open a PR for your branch with `develop` as the base branch. Name your PR the same as the name of the ticket (story or task) in Jira. For example, if the full ticket name is `SCP-100 Refactor the frombulator`, your PR title should be `SCP-100 Refactor the frombulator`. Do not name your PR after subtasks. Provide a short description in your PR that summarizes the changes you have made. Also include a link to the JIRA story somewhere in the description of your PR.

### Style

**In addition to any requested changes from reviewers, your PR must pass a lint check on its latest commit to be accepted.**

For back-end code (JSON files, Python files, and CloudFormation templates), Black and flake8 are the format and lint tools used. Install these in your local environment with `pip install black flake8`. Be sure to point your copy of flake8 to the custom configuration set in `.github/linters/.flake8` to avoid inconsistencies between your local environment and the CI environment. Black uses the default configuration.

For front-end code (files in the `Client` directory), Prettier and ESLint are used for formatting and linting, respectively. These dependencies are automatically installed along with the other dependencies when running `npm install` in the `Client` directory. Installing extensions for both of these tools in your IDE is recommended (Prettier instructions [here](https://prettier.io/docs/en/editors.html), ESLint instructions [here](https://eslint.org/docs/user-guide/integrations#editors)). These checks are not currently enforced by the CI system, but will be in the future. To disable ESLint temporarily for development purposes, add `DISABLE_ESLINT_PLUGIN=true` to your `.env` file.

---

Top-level directories represent specific types of deliverables:

- `Auth` contains files for user authentication and authorization features.
- `CDFAndIoT` contains the implementation of features touching CDF and IoT, such as the IoT Lambda functions.
- `CEI` contains the implementation of Police Initiative features.
- `Deployment` contains files that control the CI/CD system.
- `Extras` contains everything else that is _not_ a deliverable, such as example code.
- `Client` contains files for the SCP UI front-end application.
- `Vps` contains the implementation of the Virtual Phase Selector.