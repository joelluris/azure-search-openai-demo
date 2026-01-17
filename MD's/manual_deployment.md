cd C:\Users\joell\Documents\Github-repos\ai-chat-ui\app\frontend; npm install; npm run build

cd C:\Users\joell\Documents\Github-repos\ai-chat-ui\app; Compress-Archive -Path backend\* -DestinationPath deploy.zip -Force

az webapp deploy --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --src-path deploy.zip --type zip


cd C:\Users\joell\Documents\Github-repos\ai-chat-ui\app; az webapp deploy --resource-group rg-chat-dev-uaen-001 --name app-chat-dev-uaen-001 --src-path deploy.zip --type zip --async true