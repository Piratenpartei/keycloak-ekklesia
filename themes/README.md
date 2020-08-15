# Themes
- ekklesia: Hides the first and last name fields for the user and fills them with default values
- ekklesia-pirates: Contains a pirate theme for keycloak (has the ekklesia theme as parent)

# Installation
1. Copy the ekklesia and ekklesia-pirates folders to `<keycloakInstallDir>/themes/`
2. In the administration interface go to Realm Settings -> Themes and select the required theme (ekklesia or ekklesia-pirates) as Login, Account and optionally Admin theme

# Maintenance
When keycloak is updated, check if the template files `account/account.ftl` and `login/login-update-profile.ftl` were changed inside the `<keycloakInstallDir>/themes/base` folder and update them in this theme accordingly.
