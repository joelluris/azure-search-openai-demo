

🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇Copied from Copilot Chat🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇🎇

# Get client ID
az ad app list --display-name "appreg-chat-sso-dev" --query "[0].{appId: appId, displayName: displayName}" -o json

# verifying the sso authentication
az webapp auth show --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --query "{enabled: properties.enabled, defaultProvider: properties.defaultProvider, clientId: properties.identityProviders.azureActiveDirectory.registration.clientId, tenantIssuerUrl: properties.identityProviders.azureActiveDirectory.login.loginParameters[0]}" -o json

# retrieve the app service authentication
az webapp auth show --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' -o json

# migrate the app service to easy auth to auth 2.0
az webapp auth config-version upgrade --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001'

# configures Microsoft Entra ID as the authentication provider for your App Service using the new Auth 2.0 schema.
az webapp auth microsoft update --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --client-id '0e63551f-f0eb-4694-acd7-c54661b071c4' --client-secret-setting-name 'SSO_CLIENT_SECRET' --issuer "https://login.microsoftonline.com/7d1a04ec-981a-405a-951b-dd2733120e4c/v2.0" --allowed-audiences "api://0e63551f-f0eb-4694-acd7-c54661b071c4"

#  turns on authentication for your App Service and forces users to sign in with Microsoft Entra ID before accessing the app.
az webapp auth update --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --enabled true --action 'RedirectToLoginPage' --redirect-provider 'azureactivedirectory'

# querying and filtering your App Service’s authentication configuration so you only see the two pieces that matter for SSO validation:
az webapp auth show --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --query "{identityProvider: identityProviders.azureActiveDirectory, globalValidation: globalValidation}" -o json

# It updates the allowed audiences field in your App Service Auth 2.0 config.
az webapp auth microsoft update --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --allowed-audiences "https://app-chat-dev-uaen-001.azurewebsites.net"

# enables ID token issuance for your Microsoft Entra ID app registration — a required step when your App Service uses Easy Auth (Auth 2.0) and needs an OpenID Connect ID token during login.
az ad app update --id '0e63551f-f0eb-4694-acd7-c54661b071c4' --enable-id-token-issuance true

# command updates the Application ID URI of your Microsoft Entra ID app registration — a key part of how tokens are issued and validated.
az ad app update --id '0e63551f-f0eb-4694-acd7-c54661b071c4' --identifier-uris "api://0e63551f-f0eb-4694-acd7-c54661b071c4"

# download app service logs for troubleshooting app logs
az webapp log download --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --log-file 'webapp-logs.zip'; Expand-Archive -Path 'webapp-logs.zip' -DestinationPath 'webapp-logs' -Force; Get-Content 'webapp-logs\LogFiles\*.log' -Tail 50

# That command is a targeted lookup of your App Service’s application settings, filtered so you only see the value of the setting that stores your Microsoft Entra ID client secret.
az webapp config appsettings list --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --query "[?name=='SSO_CLIENT_SECRET'].{name:name, value:value}" -o json

# command enables the Easy Auth token store, which is an optional but very useful feature when you're working with Microsoft Entra ID authentication on Azure App Service.
az webapp auth update --name 'app-chat-dev-uaen-001' --resource-group 'rg-chat-dev-uaen-001' --token-store true


# command is a clean way to list all client secrets and certificates associated with your Microsoft Entra ID app registration — but filtered so you only see the fields that matter for SSO maintenance.
az ad app credential list --id '0e63551f-f0eb-4694-acd7-c54661b071c4' --query "[].{keyId:keyId, displayName:displayName, endDateTime:endDateTime}" -o json

# az ad app show --id '0e63551f-f0eb-4694-acd7-c54661b071c4' --query "{appId:appId, identifierUris:identifierUris, web:web.redirectUris, oauth2Permissions:api.oauth2PermissionScopes, accessTokenAcceptedVersion:api.requestedAccessTokenVersion}" -o json
That command is a focused inspection of your Microsoft Entra ID app registration. It pulls only the fields that matter for validating an App Service SSO setup 

# That command updates your Microsoft Entra ID app registration so it issues v2 access tokens, which is exactly what your App Service SSO configuration expects
az ad app update --id '0e63551f-f0eb-4694-acd7-c54661b071c4' --set api.requestedAccessTokenVersion=2


# This PATCH ensures the token version aligns with your App Service configuration.
az rest --method PATCH --uri "https://graph.microsoft.com/v1.0/applications/$(az ad app show --id '0e63551f-f0eb-4694-acd7-c54661b071c4' --query id -o tsv)" --headers "Content-Type=application/json" --body '{\"api\":{\"requestedAccessTokenVersion\":2}}'

# list app settings
az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?name=='AZURE_OPENAI_SERVICE' || name=='AZURE_SEARCH_SERVICE' || name=='AZURE_OPENAI_CHATGPT_DEPLOYMENT' || name=='AZURE_USE_AUTHENTICATION'].{Name:name, Value:value}" --output table