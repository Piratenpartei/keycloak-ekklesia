# Keycloak-ekklesia

Keycloak extensions for Ekklesia.

## Theme

- ekklesia
  - Adds sync_id field to registration form.
  - Hides the first and last name fields and fills them with default values.

### Installation

1. Copy the themes/ekklesia folder to <keycloakInstallDir>/themes/
2. In the administration interface go to Realm Settings -> Themes and select ekklesia as Login and Account theme

### Maintenance

When keycloak is updated, check if the template files account/account.ftl and login/login-update-profile.ftl were
changed inside the <keycloakInstallDir>/themes/base folder and update them in this theme accordingly.


## Code Extension

- work in progress, will add a protocol mapper to encrypt recipient info for the
  [ekklesia-notify](https://github.com/piratenpartei/ekklesia-notify) component.
