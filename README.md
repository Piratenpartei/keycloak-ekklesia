# Keycloak-ekklesia

Keycloak extensions for Ekklesia.
This project consists of two major parts:
1. Sync scripts to manage users from an external CSV source (see folder `external_sync` with its own Readme file).
2. Keycloak modifications consisting of themes and a plugin which are described in the following.

## Installation

1. Run `mvn clean package` in the main folder
2. Run `docker build . -t ekklesia-keycloak` to build a keycloak container with the extensions installed
3. Start the container. Example docker-compose:
```
keycloak:
    image: ekklesia-keycloak:latest
    restart: always
    environment:
      - KC_DB_USERNAME=<username>
      - KC_DB_PASSWORD=<password>
      - KC_DB_URL_HOST=<host>:<port>
      - KC_DB_URL_DATABASE=<database>
      - KC_HTTPS_CERTIFICATE_FILE=/etc/x509/https/tls.crt
      - KC_HTTPS_CERTIFICATE_KEY_FILE=/etc/x509/https/tls.key
    ports:
      - "8443:8443"
    volumes:
      - type: bind
        source: ${PWD}/keycloak/tls.crt
        target: /etc/x509/https/tls.crt
      - type: bind
        source: ${PWD}/keycloak/tls.key
        target: /etc/x509/https/tls.key
```
4. In the administration interface go to Realm Settings -> Themes and select ekklesia-pirates as Login and Account theme.

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
