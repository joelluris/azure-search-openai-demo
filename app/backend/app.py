"""
Simplified chat application with SSO authentication
Just the essentials to make it work
"""
import os
import logging
import jwt
from functools import wraps
from quart import Quart, jsonify, request, send_from_directory
from quart_cors import cors
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = Quart(__name__)
app = cors(app, allow_origin="*")

# SSO Configuration
USE_AUTHENTICATION = os.getenv("AZURE_USE_AUTHENTICATION", "false").lower() == "true"
AZURE_CLIENT_APP_ID = os.getenv("AZURE_CLIENT_APP_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_AUTH_TENANT_ID = os.getenv("AZURE_AUTH_TENANT_ID", AZURE_TENANT_ID)

# Global clients (initialized on first request, not at startup)
_search_client = None
_openai_client = None
_credential = None


def require_auth(f):
    """Decorator to require authentication on endpoints"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not USE_AUTHENTICATION:
            return await f(*args, **kwargs)
        
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            return jsonify({"error": "Unauthorized"}), 401
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            # Decode and validate JWT token
            # Note: In production, you should verify the signature with Azure AD public keys
            decoded = jwt.decode(
                token,
                options={"verify_signature": False},  # Simplified - validate signature in production!
                audience=AZURE_CLIENT_APP_ID
            )
            
            # Store user info in request context
            request.user_id = decoded.get("oid") or decoded.get("sub")
            request.user_name = decoded.get("name") or decoded.get("preferred_username")
            logger.info(f"Authenticated user: {request.user_name}")
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return jsonify({"error": "Invalid token"}), 401
        
        return await f(*args, **kwargs)
    
    return decorated_function


def get_credential():
    """Get Azure credential - cached globally"""
    global _credential
    if _credential is None:
        client_id = os.getenv("AZURE_CLIENT_ID")
        if client_id:
            logger.info(f"Using ManagedIdentityCredential with client_id: {client_id}")
            _credential = ManagedIdentityCredential(client_id=client_id)
        else:
            logger.info("Using DefaultAzureCredential")
            _credential = DefaultAzureCredential()
    return _credential


def get_search_client():
    """Get Search client - initialized lazily"""
    global _search_client
    if _search_client is None:
        service = os.getenv("AZURE_SEARCH_SERVICE")
        index = os.getenv("AZURE_SEARCH_INDEX")
        endpoint = f"https://{service}.search.windows.net"
        
        logger.info(f"Initializing Search client for {endpoint}")
        _search_client = SearchClient(
            endpoint=endpoint,
            index_name=index,
            credential=get_credential()
        )
    return _search_client


def get_openai_client():
    """Get OpenAI client - initialized lazily"""
    global _openai_client
    if _openai_client is None:
        service = os.getenv("AZURE_OPENAI_SERVICE")
        endpoint = f"https://{service}.openai.azure.com"
        
        logger.info(f"Initializing OpenAI client for {endpoint}")
        
        # Try with managed identity first
        try:
            from azure.identity import get_bearer_token_provider
            token_provider = get_bearer_token_provider(
                get_credential(),
                "https://cognitiveservices.azure.com/.default"
            )
            _openai_client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2024-02-01"
            )
        except Exception as e:
            logger.warning(f"Failed to init OpenAI with MI: {e}")
            # Fallback to API key if MI fails
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if api_key:
                _openai_client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version="2024-02-01"
                )
    return _openai_client


@app.route("/")
async def index():
    """Serve the frontend"""
    return await send_from_directory("static", "index.html")


@app.route("/<path:path>")
async def static_files(path):
    """Serve static files"""
    return await send_from_directory("static", path)


@app.route("/config", methods=["GET"])
async def config():
    """Return configuration for frontend"""
    return jsonify({
        "showGPT4VOptions": False,
        "showSemanticRankerOption": True,
        "showVectorOption": True,
        "showUserUpload": False,
        "showSpeechInput": False,
        "showSpeechOutputBrowser": False,
        "showSpeechOutputAzure": False,
        "showChatHistoryBrowser": False,
        "showChatHistoryCosmos": False,
        "showLanguagePicker": False,
        "showAgenticKnowledgebase": False,
        "showWebSource": False,
        "showSharePointSource": False,
        # SSO Configuration
        "useLogin": USE_AUTHENTICATION,
        "msalConfig": {
            "auth": {
                "clientId": AZURE_CLIENT_APP_ID,
                "authority": f"https://login.microsoftonline.com/{AZURE_AUTH_TENANT_ID}",
                "redirectUri": "/redirect"
            },
            "cache": {
                "cacheLocation": "sessionStorage"
            }
        } if USE_AUTHENTICATION else None
    })


@app.route("/auth_setup", methods=["GET"])
async def auth_setup():
    """Return authentication configuration"""
    if not USE_AUTHENTICATION:
        return jsonify({"useLogin": False})
    
    return jsonify({
        "useLogin": True,
        "msalConfig": {
            "auth": {
                "clientId": AZURE_CLIENT_APP_ID,
                "authority": f"https://login.microsoftonline.com/{AZURE_AUTH_TENANT_ID}",
                "redirectUri": "/redirect"
            },
            "cache": {
                "cacheLocation": "sessionStorage"
            }
        },
        "loginRequest": {
            "scopes": [f"api://{AZURE_CLIENT_APP_ID}/access_as_user"]
        }
    })


@app.route("/chat", methods=["POST"])
@require_auth
async def chat():
    """Simple chat endpoint"""
    try:
        data = await request.get_json()
        messages = data.get("messages", [])
        
        # Get last user message
        user_message = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "Hello"
        )
        
        logger.info(f"Processing chat request: {user_message[:50]}...")
        
        # Simple search
        try:
            search = get_search_client()
            results = list(search.search(
                search_text=user_message,
                top=3,
                select="content,sourcepage"
            ))
            context = "\n\n".join([r.get("content", "") for r in results])
            logger.info(f"Found {len(results)} search results")
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            context = ""
        
        # Get OpenAI response
        try:
            client = get_openai_client()
            deployment = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
            
            system_message = "You are a helpful AI assistant."
            if context:
                system_message += f"\n\nUse this context to answer:\n{context[:2000]}"
            
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            answer = response.choices[0].message.content
            logger.info("Generated response successfully")
            
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            answer = f"I encountered an error: {str(e)}"
        
        return jsonify({
            "message": {
                "content": answer,
                "role": "assistant"
            },
            "context": {
                "data_points": {
                    "text": [r.get("sourcepage", "") for r in results] if results else []
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
async def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    # For local testing only
    app.run(host="0.0.0.0", port=50505, debug=True)
