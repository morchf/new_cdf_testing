# ClientAPI / dwh

Redshift data warehouse infrastructure, DDL, and automatic migration scripts

## Overview

`dwh_module.py`: CDK code for DWH infrastructure. As part of the CDK deployment process, secrets are added to Secrets Manager with auto-generated passwords. These auto-updated values are pulled at DWH migration time

`Dockerfile`, `docker-compose.yml`, and `sql/`: Code for DWH management/migrations

## Infrastructure

The Redshift cluster is defined in [redshift.yml](../CF/redshift.yml). The CDK deployment references the Redshift cluster to add permissions and run the migration against.

### Creating a User Secret

```python
from aws_cdk import aws_secretsmanager as sm

sm.Secret(
   scope=self,
   id="SecretId",
   description="API user. Read-only permissions granted to relevant tables",
   generate_secret_string=aws_sm.SecretStringGenerator(
         exclude_characters="'",
         exclude_punctuation=True,
         generate_string_key="password",
         secret_string_template=json.dumps(
            {
               "username": "api",
               "dbname": redshift_dbname,
               "host": redshift_host,
               "port": redshift_port,
            }
         ),
   ),
)
```

**Note**: You may also add/update DB users using the [CustomResources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html) resource in CloudFormation templates. This would require including an inline Lambda that would pull the secrets, load the username/password, and run a SQL command to update the user, whenever the template is updated.

## Directory Overview

Under the `sql` directory

- `functions/`: User-defined functions
  - Format: `f_<function_name>.sql`
  - Both SQL-based and Python-based (https://docs.aws.amazon.com/redshift/latest/dg/user-defined-functions.html)
- `procedures`: Stored procedures

  - Format: `sp_<procedure_name>.sql`

- `scripts`: Scripts used for admin management, including user setup and schema management
- `tables`: Tables
- `test`: Test scripts and data
- `versions`: Migration scripts for new versions
- `views`: Views
  - Format: `v_<view_name>.sql`
- `core`: Migration code
- `release`: Utility scripts for running
  - _Not automatically run_

## Migration Process

As part of the pipeline (defined in [buildspec.yml](../buildspec.yml)), a Docker container is run using the [DwhManager](./sql/core/dwh_manager.py#DwhManager)

```sh
# Run from ClientAPI/
docker-compose -f ./dwh/docker-compose.yml up --build
```

The `DwhManager` uses SQL files defined in the `sql` directory to automatically run migration scripts, such as removing old tables, adding new columns, or updating user permissions.

These files may include template expressions of the format `{VARIABLE}`, which will be substituted by any matching variables of the same key in the JSON string encoded in the `SQL_SCRIPT_KWARGS` environment variable

- e.g. `SQL_SCRIPT_KWARGS='{ "VARIABLE": "v" }'` will substitute any instance of `{VARIABLE}` in any SQL script with the value `v`

### Steps

1. Check the current DWH version. If no version found (first time running the `DwhManager` utility on this DWH) create the versioning table

   - Find current version: [scripts/version.sql](./sql/scripts/version.sql)
   - Create versioning table: [tables/meta/changelog.sql](./sql/tables/meta/changelog.sql)

2. Run any versioning scripts greater than the current DWH version

   - `versions/{version:03}`: To create a new version, add a folder of the format `XXX` under the [versions](./sql/versions) folder. Add any SQL commands in separate files, defining their run order with the format `001_<description>.sql`, `002_<description>.sql`...
   - _e.g. DWH version is 2. Run any scripts under versions/004, versions/005..., in the order versions/004/001_description.sql, versions/004/002_description.sql, versions/005/001_description.sql..._

3. Run SQL scripts in the order matching [core/constants.py](./sql/core/constants.py). Generally, the scripts are run as functions, then procedures, then tables, then views. Within these directories, each script is run following alphanumeric order, based on the file name.
   - [scripts/pre](./sql/scripts/pre) and [scripts/post](./sql/scripts/post) are included to organize scripts running before/after primary migration operations
     - pre: Includes creating new schemas or attaching external schemas
     - post: Adding user permissions for updated/created tables, views, and stored procedures
   - To enforce dependencies between scripts that must be run out of order. See below

```python
# core/constants.py
...
SQL_FILES = [
  ...
  "views/v_view_1.sql",
  "views/v_view_2.sql",
  "views",
  ...
]

# v_view_2 has a dependency on v_view 1
# v_view_1 is created first, v_view_2 is created second, then all other views under 'views/' are created in the alphanumeric order of their file name
```

- **Note**: To allow use by other projects, this step may be extended to accept ordering as an environment variable and the SQL files as a Docker volume mount

4. Update user permissions. Using [scripts/post/setup_users.sql](./sql/scripts/post/setup_users.sql), users can be granted access to specific schemas and/or tables with a given password and database. This script calls [procedures/sp_setup_user.sql](./sql/procedures/sp_setup_user.sql), which removes all existing user permissions, drops the user, and recreates the user with the given password

   - Here, the `SQL_SCRIPT_KWARGS` environment variable contains the newest user passwords generated as part of the CDK deployment. See [app.py](./sql/app.py) for where the auto-generated passwords are retrieved from Secrets Manager and loaded into the `SQL_SCRIPT_KWARGS`

5. Update the DWH version. The version corresponds to the highest-ordered version number under [version](./sql/versions). The version entry is timestamped in the [changelog](./sql/tables/meta/changelog.sql) table

The current state of tables, views, functions, and stored procedures represents the expected state of the DWH after upgrading to the most recent version

- **Note**: A table created from scratch should match any table updated by the versioning script. E.g. if a versioning script adds a new column to an existing table, add that same column to the table definition.

## FAQ

### _How do I update an existing table?_

When updating a table, existing data must be transformed to match the new format. If the update can be made automatically, a new entry can be added to the [versions](./sql/versions) directory

Example:

I have table 'abc', already created and defined in [tables/abc.py](./sql/tables). This table needs a new column, 'new_col'. We can assume the existing columns all have a default of '-1.

1. Add a new SQL script under the new version, assuming current version is '4' (i.e. create a directory '005')

_versions/005/001_add_new_column.sql_

```sql
ALTER TABLE public.abc ADD COLUMN new_col INT;
UPDATE public.abc SET new_col = -1;
```

2. Update the existing table entry to have the same new column with the same type

_tables/abc.sql_

```sql
CREATE TABLE IF NOT EXISTS public.abc (
  agency TEXT,
  new_col INT
)
```

When the pipeline runs, the new table will have its columns updated automatically. If this process is run on a new DB, the table will be created from scratch with the new column. The DWH will update to version '5'

### _How do I update a materialized view?_

Materialized view (https://docs.aws.amazon.com/redshift/latest/dg/materialized-view-overview.html) are views that store data as a physical table, meaning no re-computing of the view at query time. Updating them requires dropping the materialized view

Example:

I have materialized view 'mv_xyz', already created and defined in [views/mv_xyz.py](./sql/views). This view has changed. 'mv_cde' depends on 'mv_xyz', so both must be updated.

1. Add a new SQL script under the new version, assuming new version '003'

_versions/003/001_drop_views.sql_

```sql
-- 'CASCADE' will drop any dependent views/materialized views
DROP MATERIALIZED VIEW mv_xyz CASCADE;
```

2. Update the view in its original file [views/mv_xyz.sql](./sql/views)

3. Make sure the dependent view, 'mv_cde', will be run after 'mv_xyz'. As 'xyz' is alphanumerically ordered after 'cde', this is not automatic. Update this entry in the [core/constants.py](./sql/core/constants.py) file:

```python
# core/constants.py
...
SQL_FILES = [
  ...
  "views/mv_xyz.sql",
  "views/mv_cde.sql",
  ...
  "views",
  ...
]
```

When the pipeline runs, the existing materialized views will be dropped. The new views will be created when the migration scripts reach the 'views' section. 'views/mv_abc.sql' will be run before 'view/mv_cde.sql', preserving the dependency.

**Note**: If running 'view/mv_abc.sql' causes a failure, any dependeny views will also have a failure

### _Running a migration caused a failure when dropping a user_

`ERROR: user "username" cannot be dropped because some objects depend on it`

If a permissions are added to a user manually, it can cause issues with dropping that user. Many Stack Overflow threads ([1](https://stackoverflow.com/questions/40650426/cant-drop-user-from-redshift), [2](https://stackoverflow.com/questions/33894376/redshift-user-xyz-cannot-be-dropped-because-the-user-owns-some-object), [3](https://dba.stackexchange.com/questions/143938/drop-user-in-redshift-which-has-privilege-on-some-object), ...) are dedicated to resolving this issue, including creating [admin views that generate the DDL for dropping the user](https://github.com/awslabs/amazon-redshift-utils/blob/master/src/AdminViews/v_find_dropuser_objs.sql). The easiest method, by far, is to rename the user and re-run the pipeline:

```sql
ALTER USER <user> RENAME TO <new name>
```

### _Why create a DB management utility from scratch?_

Other frameworks have DB management tools available as library dependencies (e.g. [Liquibase](https://www.liquibase.org/) for Java projects). Other tools are available as a standalone executable (e.g. [Flyway](https://flywaydb.org/)). These options had major issues for our needs:

1. No utility had full support for Redshift or Snowflake, leading to workarounds
2. Standalone projects, like Flyway, lacked automatic generation of SQL. Instead, they only ran migrations with 'up' and 'down' scripts ('up' scripts updated the DB and 'down' scripts reverted the change, on failure). However, there was limited support for organizing these scripts, leading to massive directories of 'up' and 'down' scripts for any change. And these 'down' scripts could cause any problems the 'up' scripts may cause, in an attempt to reverse the change
3. Loading variables into scripts didn't work natively, requiring a separate pre-processing step

Terraform is another DB management option for Snowflake (https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs/resources/table). However, this requires defining SQL scripts within HCL files and the addition of Terraform as a infrastructure management depencency.
