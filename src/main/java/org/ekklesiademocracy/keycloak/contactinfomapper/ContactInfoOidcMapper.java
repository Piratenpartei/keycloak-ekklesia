package org.ekklesiademocracy.keycloak.contactinfomapper;

import java.security.SecureRandom;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Base64;
import java.util.Date;
import java.util.List;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import javax.json.Json;
import javax.json.JsonArrayBuilder;
import javax.json.JsonBuilderFactory;
import javax.json.JsonObject;

import org.jboss.logging.Logger;
import org.keycloak.models.ClientSessionContext;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.ProtocolMapperModel;
import org.keycloak.models.UserSessionModel;
import org.keycloak.protocol.oidc.mappers.AbstractOIDCProtocolMapper;
import org.keycloak.protocol.oidc.mappers.OIDCAccessTokenMapper;
import org.keycloak.protocol.oidc.mappers.OIDCAttributeMapperHelper;
import org.keycloak.protocol.oidc.mappers.OIDCIDTokenMapper;
import org.keycloak.protocol.oidc.mappers.UserInfoTokenMapper;
import org.keycloak.protocol.oidc.mappers.UserPropertyMapper;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.provider.ProviderConfigurationBuilder;
import org.keycloak.representations.IDToken;

public class ContactInfoOidcMapper extends AbstractOIDCProtocolMapper implements OIDCAccessTokenMapper, OIDCIDTokenMapper, UserInfoTokenMapper {

    private static final String PROVIDER_ID = "ekklesia-notify-mapper";

    private static final Logger LOGGER = Logger.getLogger(ContactInfoOidcMapper.class);

    private static final List<ProviderConfigProperty> CONFIG_PROPERTIES;

    private static final String CONFIG_PROPERTY_SECRET_KEY = "contact_info_secret_key";

    private static final String MYSECRET= "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=";

    public static final int GCM_IV_LENGTH = 12;
    public static final int GCM_TAG_LENGTH = 16;

    static {

        CONFIG_PROPERTIES = ProviderConfigurationBuilder.create()
                .property()
                .name(CONFIG_PROPERTY_SECRET_KEY)
                .type(ProviderConfigProperty.STRING_TYPE)
                .label("Contact Info Secret Key")
                .helpText("Key for contact info encryption")
                .defaultValue("")
                .add()

                .build();

        OIDCAttributeMapperHelper.addAttributeConfig(CONFIG_PROPERTIES, UserPropertyMapper.class);
    }

    @Override
    public String getDisplayCategory() {
        return TOKEN_MAPPER_CATEGORY;
    }

    @Override
    public String getDisplayType() {
        return "Ekklesia Notify Mapper";
    }

    @Override
    public String getHelpText() {
        return "Encrypts contact info (email + matrix) into a string suitable for ekklesia-notify";
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return CONFIG_PROPERTIES;
    }

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    private byte[] generateGcmIv() {
    	byte[] IV = new byte[GCM_IV_LENGTH];
        SecureRandom random = new SecureRandom();
        random.nextBytes(IV);
        return IV;
    }

    private byte[] encrypt(byte[] plaintext, SecretKey key, byte[] IV) throws Exception
    {
        Cipher cipher = Cipher.getInstance("AES_256/GCM/NoPadding");
        GCMParameterSpec gcmParameterSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, IV);
        cipher.init(Cipher.ENCRYPT_MODE, key, gcmParameterSpec);
        byte[] cipherText = cipher.doFinal(plaintext);

        return cipherText;
    }

    private byte[] decrypt(byte[] cipherText, SecretKey key, byte[] IV) throws Exception
    {
        Cipher cipher = Cipher.getInstance("AES_256/GCM/NoPadding");
        GCMParameterSpec gcmParameterSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, IV);
        cipher.init(Cipher.DECRYPT_MODE, key, gcmParameterSpec);
        byte[] decryptedText = cipher.doFinal(cipherText);

        return decryptedText;
    }

    private SecretKey setKey(String myKey)
    {
        byte[] key;
        SecretKey secretKey=null;

        key = Base64.getDecoder().decode(myKey);
 		key = Arrays.copyOf(key, 32);
		secretKey = new SecretKeySpec(key, "AES");
        return secretKey;
    }

    private String encrypt(String message, String secret) {
        String encryptedMessage= null;

        try {
			SecretKey mykey= setKey(secret);
			byte[] iv= generateGcmIv();
			byte[] encryptedBytes= encrypt(message.getBytes("UTF-8"),mykey,iv);
			byte[] resultBytes = new byte[iv.length + encryptedBytes.length];
			System.arraycopy(iv, 0, resultBytes, 0, iv.length);
			System.arraycopy(encryptedBytes, 0, resultBytes, iv.length, encryptedBytes.length);
			encryptedMessage= Base64.getEncoder().encodeToString(resultBytes);
		} catch (Exception e) {
			LOGGER.errorf(e, "encrypt contact info");
		}
        return encryptedMessage;
    }

    @Override
    protected void setClaim(IDToken token, ProtocolMapperModel mappingModel, UserSessionModel userSession, KeycloakSession keycloakSession, ClientSessionContext clientSessionCtx) {
        String email= userSession.getUser().getEmail();
        List<String> matrix= userSession.getUser().getAttribute("ekklesia_matrix_id");
        String encryptedMessage="";

        if (email!=null && email.trim().length()>0 || matrix!=null && matrix.size()>0) {
	        String secretKeyProperty= mappingModel.getConfig().getOrDefault(CONFIG_PROPERTY_SECRET_KEY, "");

	        JsonBuilderFactory jsonFactory= Json.createBuilderFactory(null);
	        SimpleDateFormat format= new SimpleDateFormat("YYYY-MM-dd'T'HH:mm:ss.SSS");
	        JsonArrayBuilder matrixArrayBuilder=jsonFactory.createArrayBuilder();
	        if (matrix!=null && matrix.size()>0)
	        	for (String i: matrix)
	        		if (i!=null && i.trim().length()>0)
	        			matrixArrayBuilder.add(i);
	        JsonArrayBuilder emailArrayBuilder=jsonFactory.createArrayBuilder();
	        if (email!=null && email.trim().length()>0)
	        	emailArrayBuilder.add(email);
	        JsonObject json= jsonFactory.createObjectBuilder().add("timestamp", format.format(new Date()))
	        		.add("transports", jsonFactory.createObjectBuilder()
	        		    .add("matrix",
	        				jsonFactory.createObjectBuilder().add("matrix_ids", matrixArrayBuilder)
	        				)
	        		    .add("mail",
	        		    	jsonFactory.createObjectBuilder().add("to", emailArrayBuilder)
	        		    	)
	        		    )
	                .build();

	        String message=json.toString();
	        LOGGER.infof("message %s", message);
	        String usedSecretKey= secretKeyProperty!=null && secretKeyProperty.trim().length()>0 ? secretKeyProperty : MYSECRET;
	        encryptedMessage= encrypt(message,usedSecretKey);
        }

        Object claimValue = "aesgcm:"+encryptedMessage;

        LOGGER.infof("setClaim %s=%s", mappingModel.getName(), claimValue);
        OIDCAttributeMapperHelper.mapClaim(token, mappingModel, claimValue);
    }
}
