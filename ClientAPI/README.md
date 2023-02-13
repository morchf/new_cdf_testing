# Client API

Repository for Client API code and infrastructure

## Repository structure

Branches are based on the [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/) model. A quick summary:

- The primary long-lived branches are `develop` and `main`.
- The tip of `main` represents the latest released version.
- The tip of `develop` represents the latest state of development work.
- Ephemeral topic branches are created from `develop`. These branches represent work in progress and must follow specific naming and formatting rules to properly connect to Jira, our project tracking tool. The rules are as follows:

  - The name of a feature branch is prefixed with `feature-` and suffixed with the key of the story from Jira, e.g. `TSPA-2`. The key is case sensitive, so in this example, the branch must be named `feature-TSPA-2`.
  - The commits on a feature branch should reference the key of the relevant subtask before any other text in the title (the first line) of the commit message, e.g.

    ```
    TSPA-3 I did a thing

    It has some details
    ```

    If the story doesn't have any subtasks, then reference the story key instead.

    Don't add brackets `[]` or other symbols around the key. For the advanced user, this is the [Smart Commit syntax](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html) which can be used to do [all](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-commentComment) [kinds](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-timeTime) [of](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-transitionWorkflowtransitions) [things](https://confluence.atlassian.com/jirasoftwarecloud/processing-issues-with-smart-commits-788960027.html#ProcessingissueswithSmartCommits-Advancedexamples) in Jira.

## Contributing

Topic branches are created from `develop` and merged back into `develop` using pull requests. When you are finished with your work, open a PR for your branch with `develop` as the base branch. Name your PR the same as the name of the ticket (story or task) in Jira. For example, if the full ticket name is `TSPA-1 Refactor the frombulator`, your PR title should be `TSPA-1 Refactor the frombulator`. Do not name your PR after subtasks. Provide a short description in your PR that summarizes the changes you have made.

## Getting Started

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project. The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory. To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation
