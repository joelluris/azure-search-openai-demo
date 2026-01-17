# Shows real-time streaming logs from the Azure Web App
az webapp log show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001

# Displays the current web app configuration, specifically Linux runtime version and startup command
az webapp config show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "{linuxFxVersion:linuxFxVersion, appCommandLine:appCommandLine}" --output table

# Sets the startup command for the web app to run Python with Gunicorn
az webapp config set --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --startup-file "python3 -m gunicorn main:app"

# Configures logging settings for both application and web server logs to use filesystem with verbose level
az webapp log config --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --application-logging filesystem --level verbose --web-server-logging filesystem

# Downloads all web app logs as a zip file
az webapp log download --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --log-file app-logs.zip

# Extracts the downloaded logs and shows the last 50 lines of all log files
Expand-Archive -Path app-logs.zip -DestinationPath app-logs -Force; Get-Content app-logs\LogFiles\*.log -Tail 50

# Finds the most recent application log file and shows the last 100 lines
Get-ChildItem app-logs\LogFiles\Application -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 100

# Shows real-time streaming logs again (duplicate command)
az webapp log show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001

# Downloads logs again and extracts them, then shows last 100 lines of most recent application log
az webapp log download --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --log-file app-logs.zip
Expand-Archive -Path app-logs.zip -DestinationPath app-logs -Force; Get-ChildItem app-logs\LogFiles\Application -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 100

# Shows last 50 lines of the 3 most recent log files with headers
Get-ChildItem app-logs\LogFiles -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 3 | ForEach-Object { Write-Host "`n=== $($_.FullName) ===`n" -ForegroundColor Cyan; Get-Content $_.FullName -Tail 50 }

# Shows web app configuration including Linux runtime, startup command, and health check path
az webapp config show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "{linuxFxVersion:linuxFxVersion, appCommandLine:appCommandLine, healthCheckPath:healthCheckPath}" --output table

# Shows web app state and health check path configuration
az webapp show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "{state:state, healthCheckPath:siteConfig.healthCheckPath}" --output table

# Updates the health check path to root ("/")
az webapp update --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --set siteConfig.healthCheckPath="/"

# Restarts the web application
az webapp restart --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001

# Waits 30 seconds after restart, then starts streaming logs
Start-Sleep -Seconds 30; az webapp log tail --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001

# Lists app settings that contain 'OPENAI', 'AZURE', or 'SEARCH' in their names
az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?contains(name, 'OPENAI') || contains(name, 'AZURE') || contains(name, 'SEARCH')].{name:name, value:value}" --output table

# Opens the web app in the default browser
az webapp browse --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001

# Downloads logs, extracts them, and shows last 200 lines of most recent Docker log
az webapp log download --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --log-file app-logs-new.zip; Expand-Archive -Path app-logs-new.zip -DestinationPath app-logs-new -Force; Get-ChildItem app-logs-new\LogFiles -Recurse -File | Where-Object { $_.Name -like '*default_docker*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 200

# Streams logs and filters for error-related patterns with context
az webapp log tail --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 2>&1 | Select-String -Pattern "error|Error|ERROR|exception|Exception|EXCEPTION|failed|Failed|FAILED" -Context 2,2

# Gets Azure access token and retrieves app settings via REST API (more detailed than CLI)
$token = (az account get-access-token --resource https://management.azure.com --query accessToken -o tsv); $headers = @{ Authorization = "Bearer $token" }; Invoke-RestMethod -Uri "https://management.azure.com/subscriptions/43731ed3-ead8-4406-b85d-18e966dfdb9f/resourceGroups/rg-chat-dev-uaen-001/providers/Microsoft.Web/sites/app-chat-dev-uaen-001/config/appsettings/list?api-version=2022-03-01" -Headers $headers -Method POST | Select-Object -ExpandProperty properties | Select-Object AZURE_OPENAI_SERVICE, AZURE_SEARCH_SERVICE, AZURE_STORAGE_ACCOUNT

# Lists ALL app settings (duplicate commands below)
az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[].{name:name, value:value}" --output table
az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[].{name:name, value:value}" --output table

# Saves logs to file and searches for error patterns with context
az webapp log show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 | Out-File -FilePath app-service-logs.txt; Get-Content app-service-logs.txt | Select-String -Pattern "Error|Exception|Traceback|KeyError|failed" -Context 3

# Same as above (duplicate)
az webapp log show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 | Out-File -FilePath app-service-logs.txt; Get-Content app-service-logs.txt | Select-String -Pattern "Error|Exception|Traceback|KeyError|failed" -Context 3

# Tests the web app endpoint with curl and shows the last 30 lines of verbose output
curl https://app-chat-dev-uaen-001.azurewebsites.net/ -v 2>&1 | Select-Object -Last 30

az webapp log download --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --log-file latest-logs.zip; Expand-Archive -Path latest-logs.zip -DestinationPath latest-logs -Force; Get-ChildItem latest-logs\LogFiles -Recurse -File | Where-Object { $_.Name -like '*default_docker*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content

az webapp identity show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "{type:type, userAssignedIdentities:userAssignedIdentities}" --output json

az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?name=='AZURE_CLIENT_ID'].{name:name, value:value}" --output table

az webapp config appsettings set --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --settings AZURE_CLIENT_ID=f9fa4ea2-e465-4295-bcab-770431cd66ee AZURE_CLIENT_APP_ID=0e63551f-f0eb-4694-acd7-c54661b071c4

Start-Sleep -Seconds 45; az webapp log download --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --log-file startup-logs.zip; Expand-Archive -Path startup-logs.zip -DestinationPath startup-logs -Force; Get-ChildItem startup-logs\LogFiles -Recurse -File | Where-Object { $_.Name -like '*default_docker*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 100

az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?name=='AZURE_CLIENT_ID' || name=='AZURE_CLIENT_APP_ID'].{Name:name, Value:value}" -o table

az webapp identity show --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001

$searchService = "gptkb-" + (az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?name=='AZURE_SEARCH_SERVICE'].value" -o tsv); az role assignment list --assignee f9fa4ea2-e465-4295-bcab-770431cd66ee --scope "/subscriptions/43731ed3-ead8-4406-b85d-18e966dfdb9f/resourceGroups/rg-chat-dev-uaen-001" --query "[].{Role:roleDefinitionName, Scope:scope}" -o table

$searchService = "gptkb-" + (az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?name=='AZURE_SEARCH_SERVICE'].value" -o tsv); az role assignment list --assignee f9fa4ea2-e465-4295-bcab-770431cd66ee --scope "/subscriptions/43731ed3-ead8-4406-b85d-18e966dfdb9f/resourceGroups/rg-chat-dev-uaen-001" --query "[].{Role:roleDefinitionName, Scope:scope}" -o table

az webapp config appsettings list --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --query "[?name=='AZURE_SEARCH_SERVICE'].{Name:name, Value:value}" -o table

az webapp restart --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001; Start-Sleep -Seconds 45; az webapp log download --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --log-file latest-logs.zip; Expand-Archive -Path latest-logs.zip -DestinationPath latest-logs -Force; Get-ChildItem latest-logs\LogFiles -Recurse -File | Where-Object { $_.Name -like '*default_docker*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Tail 50

curl https://app-chat-dev-uaen-001.azurewebsites.net/ --max-time 15 -I

Get-Job | Receive-Job -Keep | Select-Object -Last 100; Get-Job | Remove-Job -Force