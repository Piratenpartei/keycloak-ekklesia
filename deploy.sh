#set $KEYCLOAK_HOME to keycloak installation directory
$KEYCLOAK_HOME/bin/jboss-cli.sh --command="module remove --name=org.ekklesiademocracy.keycloak.auidmapper.AuidOidcMapper" 
$KEYCLOAK_HOME/bin/jboss-cli.sh --command="module add --name=org.ekklesiademocracy.keycloak.auidmapper.AuidOidcMapper --resources=target/keycloak-ekklesia-0.0.1-SNAPSHOT.jar --dependencies=org.keycloak.keycloak-core,org.keycloak.keycloak-server-spi"


