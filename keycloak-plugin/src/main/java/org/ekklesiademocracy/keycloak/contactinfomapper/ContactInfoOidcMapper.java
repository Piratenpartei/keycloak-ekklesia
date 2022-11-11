package org.ekklesiademocracy.keycloak.contactinfomapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.text.SimpleDateFormat;
import java.util.*;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

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
import org.keycloak.util.JsonSerialization;

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

        return cipher.doFinal(plaintext);
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
			byte[] encryptedBytes= encrypt(message.getBytes(StandardCharsets.UTF_8),mykey,iv);
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
        List<String> en_email = userSession.getUser().getAttributes().get("notify_enable_email");
        boolean enable_email = true; // Email notification should be enabled if attribute is not set
        if (en_email.size() > 0) {
            enable_email = Boolean.parseBoolean(en_email.get(0));
        }
        List<String> matrix = userSession.getUser().getAttributes().get("notify_matrix_ids");
        String encryptedMessage = "";

        boolean use_email = email != null && email.trim().length() > 0 && enable_email;
        boolean use_matrix = matrix != null && matrix.size() > 0;
        if (use_email || use_matrix) {
            String secretKeyProperty = mappingModel.getConfig().getOrDefault(CONFIG_PROPERTY_SECRET_KEY, MYSECRET);

            SimpleDateFormat format = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS");
            List<String> matrix_array = new ArrayList<>();
            if (use_matrix)
                for (String i : matrix)
                    if (i != null && i.trim().length() > 0)
                        matrix_array.add(i);

            List<String> mail_array = new ArrayList<>();
            if (use_email)
                mail_array.add(email);

            Properties matrix_json = new Properties();
            matrix_json.put("matrix_ids", matrix_array.toArray());

            Properties mail_json = new Properties();
            mail_json.put("to", mail_array.toArray());

            Properties transports = new Properties();
            transports.put("matrix", matrix_json);
            transports.put("mail", mail_json);

            Properties json = new Properties();
            json.put("timestamp", format.format(new Date()));
            json.put("transports", transports);

            String message;
            try {
                message = JsonSerialization.writeValueAsString(json);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
	        encryptedMessage = encrypt(message, secretKeyProperty);
        }

        Object claimValue = "aesgcm:" + encryptedMessage;
        OIDCAttributeMapperHelper.mapClaim(token, mappingModel, claimValue);
    }
}
