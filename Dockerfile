FROM quay.io/keycloak/keycloak:18.0.0
ENV KC_FEATURES=admin2
ENV KC_DB=postgres
COPY target/keycloak-ekklesia.jar /opt/keycloak/providers/
RUN /opt/keycloak/bin/kc.sh build
WORKDIR /opt/keycloak
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start", "--spi-theme-welcome-theme=keycloak-ekklesia-pirates", "--spi-user-profile-declarative-user-profile-read-only-attributes=ekklesia*"]
