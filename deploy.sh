#set $KEYCLOAK_HOME to keycloak installation directory
$KEYCLOAK_HOME/bin/jboss-cli.sh --command="module remove --name=org.ekklesiademocracy.auidoidcmapper" 
$KEYCLOAK_HOME/bin/jboss-cli.sh --command="module add --name=org.ekklesiademocracy.auidoidcmapper --resources=target/keycloak-ekklesia-0.0.1-SNAPSHOT.jar --dependencies=org.keycloak.keycloak-core,org.keycloak.keycloak-server-spi"


