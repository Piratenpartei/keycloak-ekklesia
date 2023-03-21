FROM quay.io/keycloak/keycloak:21.0.1 as builder
ENV KC_DB=postgres
COPY target/keycloak-ekklesia.jar /opt/keycloak/providers/
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:21.0.1
COPY --from=builder /opt/keycloak/ /opt/keycloak/
WORKDIR /opt/keycloak
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start", "--optimized", "--spi-theme-welcome-theme=keycloak-ekklesia-pirates", "--spi-user-profile-declarative-user-profile-read-only-attributes=ekklesia*"]
