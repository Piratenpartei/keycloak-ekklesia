function loggedInUserName() {
    let userName = l18nMsg['unknownUser'];
    if (keycloak.tokenParsed) {
        const preferredUsername = keycloak.tokenParsed.preferred_username;
        userName = preferredUsername || userName;
    }
    return sanitize(userName);
}
