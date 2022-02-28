# Keycloak-ekklesia

Keycloak extensions for Ekklesia.
This project consists of two major parts:
1. Sync scripts to manage users from an external CSV source (see folder `external_sync` with its own Readme file).
2. Keycloak modifications consisting of themes and a plugin which are described in the following.

## Installation

1. Run `mvn clean package` in the main folder
2. Copy the resulting jar file from `target/keycloak-ekklesia.jar` to `<keycloakInstallDir>/standalone/deployments`
3. In the administration interface go to Realm Settings -> Themes and select ekklesia-pirates as Login and Account theme.
4. To set the welcome theme, go to `<keycloakInstallDir>/standalone/configuration/standalone.xml` and change server > profile > subsystem xmlns="urn:jboss:domain:keycloak-server:1.1" > theme > welcomeTheme to ekklesia-pirates
5. To make sure that the client can't modify internal ekklesia attributes, add the following block to the keycloak-server node (server > profile > subsystem xmlns="urn:jboss:domain:keycloak-server:1.1") in `standalone.xml`:
```
<spi name="userProfile">
    <provider name="declarative-user-profile" enabled="true">
        <properties>
            <property name="read-only-attributes" value="[&quot;ekklesia*&quot;]"/>
        </properties>
    </provider>
</spi>
```

## Theme/Account page
Two different themes are present, the first modifies functionality, while the second provides the design:
- ekklesia
  - Adds ekklesia_sync_id field to registration form.
  - Hides the first and last name fields and fills them with default values.
  - Extends the account page with a sync info page and beo settings
- ekklesia-pirates: Pirate design for Keycloak (has the ekklesia theme as parent).

### Maintenance

When keycloak is updated, check if the template files `login/login-update-profile.ftl`, `login/login.ftl` or `login/register.ftl` or any of the account page files were changed inside the `<keycloakInstallDir>/themes/` folder and update them in this theme accordingly.

## Code Extension

Adds a protocol mapper to encrypt recipient info for the
[ekklesia-notify](https://github.com/piratenpartei/ekklesia-notify) component.

### Configuration

TODO: describe how to create the protocol mapper and what user attributes are used.
