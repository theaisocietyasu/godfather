import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import runpod
import requests
import jwt
from functools import wraps
import secrets
import hashlib
from file_manager import PodFileManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Log all requests
@app.before_request
def log_request_info():
    logger.info(f'{request.method} {request.path} - {request.remote_addr}')
    if request.get_json(silent=True):
        logger.debug(f'Request body: {request.get_json()}')

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/godfather')
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID')
ADMIN_ROLE_ID = os.getenv('ADMIN_ROLE_ID')

# Initialize MongoDB
client = MongoClient(MONGODB_URI)
db = client.godfather
pods_collection = db.pods
users_collection = db.users
ssh_keys_collection = db.ssh_keys

# Initialize RunPod
runpod.api_key = RUNPOD_API_KEY

def get_discord_id_from_clerk(clerk_user_id):
    """Fetch Discord ID from Clerk API"""
    try:
        logger.info('='*50)
        logger.info('FETCHING DISCORD ID FROM CLERK')
        logger.info(f'Clerk User ID: {clerk_user_id}')
        
        # Use Clerk API to get user's external accounts
        headers = {
            'Authorization': f'Bearer {CLERK_SECRET_KEY}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://api.clerk.com/v1/users/{clerk_user_id}'
        logger.info(f'API URL: {url}')
        logger.info(f'Authorization header present: {bool(CLERK_SECRET_KEY)}')
        logger.info(f'Secret key length: {len(CLERK_SECRET_KEY) if CLERK_SECRET_KEY else 0}')
        
        logger.info('Making request to Clerk API...')
        response = requests.get(url, headers=headers)
        logger.info(f'Response status code: {response.status_code}')
        logger.info(f'Response headers: {dict(response.headers)}')
        
        if response.status_code != 200:
            logger.error(f'Failed to fetch user from Clerk')
            logger.error(f'Status: {response.status_code}')
            logger.error(f'Response body: {response.text[:500]}')  # First 500 chars
            return None
        
        user_data = response.json()
        logger.info(f'Successfully fetched user data')
        logger.info(f'User data keys: {list(user_data.keys())}')
        logger.info(f'User ID: {user_data.get("id")}')
        logger.info(f'Username: {user_data.get("username")}')
        logger.info(f'Email addresses: {[e.get("email_address") for e in user_data.get("email_addresses", [])]}')
        
        # Check external accounts
        external_accounts = user_data.get('external_accounts', [])
        logger.info(f'External accounts count: {len(external_accounts)}')
        
        if not external_accounts:
            logger.warning('No external accounts found!')
            logger.info('User needs to connect Discord in Clerk settings')
            return None
        
        for idx, account in enumerate(external_accounts):
            logger.info(f'--- External Account #{idx + 1} ---')
            logger.info(f'  Provider: {account.get("provider")}')
            logger.info(f'  ID: {account.get("id")}')
            logger.info(f'  Approved scopes: {account.get("approved_scopes")}')
            logger.info(f'  Email: {account.get("email_address")}')
            logger.info(f'  Username: {account.get("username")}')
            logger.info(f'  Provider user ID: {account.get("provider_user_id")}')
            logger.info(f'  Verification: {account.get("verification")}')
            logger.info(f'  All keys: {list(account.keys())}')
            
            if account.get('provider') == 'oauth_discord':
                discord_id = account.get('provider_user_id') or account.get('username')
                logger.info(f'✓ Found Discord account!')
                logger.info(f'✓ Discord ID: {discord_id}')
                logger.info('='*50)
                return discord_id
        
        logger.warning('✗ No Discord (oauth_discord) provider found in external accounts')
        logger.info('Available providers: ' + ', '.join([a.get('provider', 'unknown') for a in external_accounts]))
        logger.info('='*50)
        return None
        
    except Exception as e:
        logger.error('='*50)
        logger.error(f'EXCEPTION in get_discord_id_from_clerk: {e}', exc_info=True)
        logger.error('='*50)
        return None

def verify_discord_admin(discord_user_id):
    """Verify if user has Admin role in Discord server"""
    try:
        logger.info('='*50)
        logger.info('VERIFYING DISCORD ADMIN')
        logger.info(f'Discord User ID: {discord_user_id}')
        logger.info(f'Discord Guild ID: {DISCORD_GUILD_ID}')
        logger.info(f'Bot token present: {bool(DISCORD_BOT_TOKEN)}')
        
        headers = {
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Get guild member
        url = f'https://discord.com/api/v10/guilds/{DISCORD_GUILD_ID}/members/{discord_user_id}'
        logger.info(f'Fetching member from: {url}')
        logger.info('Making request to Discord API...')
        
        response = requests.get(url, headers=headers)
        logger.info(f'Discord API response status: {response.status_code}')
        
        if response.status_code != 200:
            logger.error(f'Failed to fetch Discord member')
            logger.error(f'Status: {response.status_code}')
            logger.error(f'Response: {response.text}')
            
            if response.status_code == 404:
                logger.error('Member not found in guild - user may not be in the Discord server')
            elif response.status_code == 401:
                logger.error('Invalid bot token or insufficient permissions')
            elif response.status_code == 403:
                logger.error('Bot lacks permission to access guild members')
                
            return False
            
        member_data = response.json()
        logger.info(f'✓ Member found in guild')
        logger.info(f'Member username: {member_data.get("user", {}).get("username")}')
        logger.info(f'Member nickname: {member_data.get("nick")}')
        logger.info(f'Member roles (IDs): {member_data.get("roles", [])}')
        logger.info(f'Member roles count: {len(member_data.get("roles", []))}')
        
        # Get guild roles to find Admin role ID
        roles_url = f'https://discord.com/api/v10/guilds/{DISCORD_GUILD_ID}/roles'
        logger.info(f'Fetching guild roles from: {roles_url}')
        
        roles_response = requests.get(roles_url, headers=headers)
        logger.info(f'Roles API response status: {roles_response.status_code}')
        
        if roles_response.status_code != 200:
            logger.error(f'Failed to fetch guild roles')
            logger.error(f'Status: {roles_response.status_code}')
            logger.error(f'Response: {roles_response.text}')
            return False
            
        roles = roles_response.json()
        logger.info(f'Guild has {len(roles)} total roles')
        
        # Log all roles for debugging
        logger.info('--- All Guild Roles ---')
        for role in roles:
            logger.info(f'  Role: "{role.get("name")}" (ID: {role.get("id")})')
        
        admin_role_id = None
        
        # Look for Admin role (case-insensitive)
        for role in roles:
            role_name = role.get('name', '').lower()
            if role_name == 'admin':
                admin_role_id = role['id']
                logger.info(f'✓ Found "Admin" role with ID: {admin_role_id}')
                break
                
        if not admin_role_id:
            logger.warning('✗ Admin role not found in guild!')
            logger.warning('Looking for role named "admin" (case-insensitive)')
            logger.info('Available role names: ' + ', '.join([r.get('name', 'unknown') for r in roles]))
            return False
        
        # Check if user has admin role
        member_role_ids = member_data.get('roles', [])
        has_admin = admin_role_id in member_role_ids
        
        logger.info(f'Checking if {admin_role_id} in {member_role_ids}')
        logger.info(f'{"✓" if has_admin else "✗"} User {"HAS" if has_admin else "DOES NOT HAVE"} admin role')
        logger.info('='*50)
        
        return has_admin
        
    except Exception as e:
        logger.error('='*50)
        logger.error(f'EXCEPTION in verify_discord_admin: {e}', exc_info=True)
        logger.error('='*50)
        return False

def verify_clerk_token(token):
    """Verify Clerk JWT token and extract user info"""
    try:
        logger.info('Verifying Clerk token')
        # In production, fetch the public key from Clerk's JWKS endpoint
        # For now, we'll decode without verification for development
        # You should implement proper JWT verification with Clerk's public key
        import base64
        import json
        
        # Split the JWT token
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning(f'Invalid JWT format: expected 3 parts, got {len(parts)}')
            return None
            
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        decoded_payload = base64.urlsafe_b64decode(payload)
        user_data = json.loads(decoded_payload)
        
        logger.info(f'Successfully decoded token for user: {user_data.get("sub", "unknown")}')
        logger.debug(f'Token payload keys: {list(user_data.keys())}')
        
        return user_data
    except Exception as e:
        logger.error(f"Error verifying Clerk token: {e}", exc_info=True)
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info('='*50)
        logger.info('REQUIRE_AUTH DECORATOR')
        
        token = request.headers.get('Authorization')
        if not token:
            logger.warning('No token provided in Authorization header')
            return jsonify({'error': 'No token provided'}), 401
            
        if token.startswith('Bearer '):
            token = token[7:]
            
        logger.info('Verifying Clerk token...')
        user_data = verify_clerk_token(token)
        if not user_data:
            logger.warning('Invalid token')
            return jsonify({'error': 'Invalid token'}), 401
        
        clerk_user_id = user_data.get('sub')
        logger.info(f'Token verified for Clerk user: {clerk_user_id}')
            
        # Look up Discord user ID from database (stored by /api/auth/verify)
        logger.info('Looking up user in database...')
        user_doc = users_collection.find_one({'clerk_id': clerk_user_id})
        
        if not user_doc:
            logger.warning(f'User {clerk_user_id} not found in database')
            logger.warning('User must call /api/auth/verify first to authenticate')
            return jsonify({'error': 'User not authenticated. Please refresh the page.'}), 401
        
        discord_user_id = user_doc.get('discord_id')
        if not discord_user_id:
            logger.error(f'User {clerk_user_id} has no Discord ID in database')
            return jsonify({'error': 'Discord account not linked'}), 401
        
        logger.info(f'✓ Found Discord ID in database: {discord_user_id}')
            
        # Verify admin role
        logger.info('Verifying admin role...')
        if not verify_discord_admin(discord_user_id):
            logger.warning(f'User {discord_user_id} does not have admin role')
            return jsonify({'error': 'Admin access required'}), 403
        
        logger.info('✓ Authorization successful')
        logger.info('='*50)
        
        request.user = user_data
        request.discord_user_id = discord_user_id
        return f(*args, **kwargs)
    return decorated

@app.route('/api/auth/verify', methods=['POST'])
def verify_auth():
    """Verify user authentication and Discord admin status"""
    logger.info('=== Auth Verification Request ===')
    
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        logger.warning('No token provided in request')
        return jsonify({'error': 'No token provided'}), 400
    
    logger.info(f'Verifying token (length: {len(token)})')
    user_data = verify_clerk_token(token)
    
    if not user_data:
        logger.warning('Invalid token provided')
        return jsonify({'error': 'Invalid token'}), 401
    
    logger.info(f'Token verified. User data: {user_data.get("sub", "unknown")}')
    logger.info(f'Full user data keys: {list(user_data.keys())}')
    
    # Get Clerk user ID
    clerk_user_id = user_data.get('sub')
    if not clerk_user_id:
        logger.error('No Clerk user ID in token')
        return jsonify({'error': 'Invalid token'}), 401
    
    # Fetch Discord ID from Clerk API
    logger.info(f'Fetching Discord ID for Clerk user: {clerk_user_id}')
    discord_user_id = get_discord_id_from_clerk(clerk_user_id)
    
    logger.info(f'Final Discord user ID: {discord_user_id}')
    
    if not discord_user_id:
        logger.warning('Discord account not linked to Clerk account')
        logger.info('Please ensure Discord is connected as an OAuth provider in Clerk')
        return jsonify({
            'error': 'Discord account not linked',
            'hint': 'Go to your Clerk account settings and ensure Discord is connected'
        }), 401
    
    # Verify admin role
    logger.info(f'Checking admin role for Discord user: {discord_user_id}')
    is_admin = verify_discord_admin(discord_user_id)
    logger.info(f'Admin check result: {is_admin}')
    
    if not is_admin:
        logger.warning(f'User {discord_user_id} does not have admin role')
        return jsonify({'error': 'Admin access required'}), 403
    
    # Store/update user in database
    user_doc = {
        'clerk_id': user_data.get('sub'),
        'discord_id': discord_user_id,
        'username': user_data.get('username'),
        'last_login': datetime.utcnow()
    }
    
    users_collection.update_one(
        {'clerk_id': user_data.get('sub')},
        {'$set': user_doc},
        upsert=True
    )
    
    logger.info(f'User {discord_user_id} successfully authenticated')
    return jsonify({'success': True, 'user': user_data})

@app.route('/api/pods', methods=['GET'])
@require_auth
def get_pods():
    """Get all pods"""
    try:
        logger.info('='*50)
        logger.info('GET ALL PODS')
        logger.info(f'User: {request.user.get("sub")}')
        
        # Get pods from RunPod
        logger.info('Fetching pods from RunPod API...')
        runpod_pods = runpod.get_pods()
        logger.info(f'✓ Fetched {len(runpod_pods) if runpod_pods else 0} pods from RunPod')
        
        # Get additional data from MongoDB
        logger.info('Fetching pod metadata from MongoDB...')
        db_pods = list(pods_collection.find())
        logger.info(f'✓ Found {len(db_pods)} pod records in MongoDB')
        
        # Merge data
        pods = []
        for idx, rp_pod in enumerate(runpod_pods):
            pod_id = rp_pod['id']
            logger.info(f'Processing pod {idx + 1}/{len(runpod_pods)}: {pod_id}')
            db_pod = next((p for p in db_pods if p['runpod_id'] == pod_id), {})
            
            pod_data = {
                'id': pod_id,
                'name': rp_pod.get('name'),
                'status': rp_pod.get('desiredStatus'),
                'machine_type': rp_pod.get('machineType'),
                'created_at': rp_pod.get('createdAt'),
                'runtime': rp_pod.get('runtime'),
                'is_public': db_pod.get('is_public', False),
                'allowed_users': db_pod.get('allowed_users', []),
                'custom_config': db_pod.get('custom_config', {})
            }
            pods.append(pod_data)
            logger.info(f'  Name: {pod_data["name"]}, Status: {pod_data["status"]}, Public: {pod_data["is_public"]}')
        
        logger.info(f'✓ Successfully prepared {len(pods)} pods')
        logger.info('='*50)
        return jsonify({'pods': pods})
    except Exception as e:
        logger.error('='*50)
        logger.error(f'ERROR in get_pods: {e}', exc_info=True)
        logger.error('='*50)
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods', methods=['POST'])
@require_auth
def create_pod():
    """Create a new pod"""
    try:
        logger.info('='*50)
        logger.info('CREATE POD')
        logger.info(f'User: {request.user.get("sub")}')
        
        data = request.get_json()
        logger.info(f'Pod name: {data.get("name")}')
        logger.info(f'Image: {data.get("image_name")}')
        logger.info(f'GPU: {data.get("gpu_type_id")}')
        logger.info(f'Public: {data.get("is_public", False)}')
        
        # Configuration for RunPod API
        # Note: RunPod SDK expects specific parameters
        config = {
            'name': data.get('name', f'pod-{secrets.token_hex(4)}'),
            'image_name': data.get('image_name', 'runpod/pytorch:3.10-2.0.0-117'),
            'gpu_type_id': data.get('gpu_type_id', 'NVIDIA RTX A4000'),
            'cloud_type': data.get('cloud_type', 'ALL'),
            'volume_in_gb': data.get('volume_in_gb', 20),
            'container_disk_in_gb': data.get('container_disk_in_gb', 20),
            'ports': data.get('ports', '8888/http,22/tcp'),
            'volume_mount_path': data.get('volume_mount_path', '/workspace'),
        }
        
        # Add optional parameters if provided
        if data.get('docker_args'):
            config['docker_args'] = data.get('docker_args')
        
        if data.get('env'):
            config['env'] = data.get('env')
        
        logger.info('Creating pod via RunPod API...')
        logger.info(f'Config: {config}')
        
        # Create pod via RunPod API
        pod = runpod.create_pod(**config)
        
        if pod and 'id' in pod:
            logger.info(f'✓ Pod created successfully: {pod["id"]}')
            logger.info(f'Pod details: {pod}')
            
            # Store additional data in MongoDB
            pod_doc = {
                'runpod_id': pod['id'],
                'name': config['name'],
                'is_public': data.get('is_public', False),
                'allowed_users': data.get('allowed_users', []),
                'custom_config': config,
                'created_by': request.user.get('sub'),
                'created_at': datetime.utcnow()
            }
            
            logger.info('Storing pod metadata in MongoDB...')
            pods_collection.insert_one(pod_doc)
            logger.info('✓ Pod metadata stored successfully')
            logger.info('='*50)
            
            return jsonify({'success': True, 'pod': pod})
        else:
            logger.error('✗ Failed to create pod - no ID returned')
            logger.error(f'RunPod response: {pod}')
            logger.info('='*50)
            return jsonify({'error': 'Failed to create pod'}), 500
            
    except Exception as e:
        logger.error('='*50)
        logger.error(f'ERROR in create_pod: {e}', exc_info=True)
        logger.error('='*50)
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods/<pod_id>', methods=['GET'])
@require_auth
def get_pod_details(pod_id):
    """Get detailed information about a specific pod"""
    try:
        logger.info('='*50)
        logger.info('GET POD DETAILS')
        logger.info(f'Pod ID: {pod_id}')
        logger.info(f'User: {request.user.get("sub")}')
        
        # Get pod from RunPod
        logger.info('Fetching pod from RunPod API...')
        pod = runpod.get_pod(pod_id)
        
        if not pod:
            logger.warning(f'✗ Pod {pod_id} not found in RunPod')
            logger.info('='*50)
            return jsonify({'error': 'Pod not found'}), 404
        
        logger.info(f'✓ Pod found: {pod.get("name")}')
        logger.info(f'Status: {pod.get("desiredStatus")}')
        logger.info(f'Machine type: {pod.get("machineType")}')
            
        # Get additional data from MongoDB
        logger.info('Fetching pod metadata from MongoDB...')
        db_pod = pods_collection.find_one({'runpod_id': pod_id})
        
        if db_pod:
            logger.info(f'✓ Found metadata - Public: {db_pod.get("is_public")}, Allowed users: {len(db_pod.get("allowed_users", []))}')
        else:
            logger.info('No metadata found in MongoDB')
        
        pod_data = {
            'id': pod['id'],
            'name': pod.get('name'),
            'status': pod.get('desiredStatus'),
            'machine_type': pod.get('machineType'),
            'created_at': pod.get('createdAt'),
            'runtime': pod.get('runtime'),
            'ports': pod.get('ports'),
            'machine': pod.get('machine'),
            'is_public': db_pod.get('is_public', False) if db_pod else False,
            'allowed_users': db_pod.get('allowed_users', []) if db_pod else [],
            'custom_config': db_pod.get('custom_config', {}) if db_pod else {}
        }
        
        logger.info('✓ Successfully prepared pod details')
        logger.info('='*50)
        return jsonify({'pod': pod_data})
    except Exception as e:
        logger.error('='*50)
        logger.error(f'ERROR in get_pod_details: {e}', exc_info=True)
        logger.error('='*50)
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods/<pod_id>', methods=['PUT'])
@require_auth
def update_pod(pod_id):
    """Update pod configuration"""
    try:
        logger.info('='*50)
        logger.info('UPDATE POD')
        logger.info(f'Pod ID: {pod_id}')
        logger.info(f'User: {request.user.get("sub")}')
        
        data = request.get_json()
        logger.info(f'Update data: {data}')
        
        # Update in MongoDB
        update_doc = {}
        if 'is_public' in data:
            update_doc['is_public'] = data['is_public']
            logger.info(f'Setting public: {data["is_public"]}')
        if 'allowed_users' in data:
            update_doc['allowed_users'] = data['allowed_users']
            logger.info(f'Setting allowed users: {data["allowed_users"]}')
            
        if update_doc:
            logger.info('Updating MongoDB...')
            result = pods_collection.update_one(
                {'runpod_id': pod_id},
                {'$set': update_doc}
            )
            logger.info(f'✓ Matched: {result.matched_count}, Modified: {result.modified_count}')
        else:
            logger.info('No updates to apply')
        
        logger.info('='*50)
        return jsonify({'success': True})
    except Exception as e:
        logger.error('='*50)
        logger.error(f'ERROR in update_pod: {e}', exc_info=True)
        logger.error('='*50)
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods/<pod_id>/action', methods=['POST'])
@require_auth
def pod_action(pod_id):
    """Perform actions on a pod (start, stop, restart, terminate)"""
    try:
        logger.info('='*50)
        logger.info('POD ACTION')
        logger.info(f'Pod ID: {pod_id}')
        logger.info(f'User: {request.user.get("sub")}')
        
        data = request.get_json()
        action = data.get('action')
        logger.info(f'Action: {action}')
        
        if action == 'stop':
            logger.info('Stopping pod via RunPod API...')
            result = runpod.stop_pod(pod_id)
            logger.info(f'✓ Stop result: {result}')
        elif action == 'start':
            logger.info('Starting/resuming pod via RunPod API...')
            result = runpod.resume_pod(pod_id)
            logger.info(f'✓ Start result: {result}')
        elif action == 'restart':
            logger.info('Restarting pod (stop then start)...')
            logger.info('  1. Stopping...')
            runpod.stop_pod(pod_id)
            logger.info('  2. Starting...')
            result = runpod.resume_pod(pod_id)
            logger.info(f'✓ Restart result: {result}')
        elif action == 'terminate':
            logger.info('Terminating pod via RunPod API...')
            result = runpod.terminate_pod(pod_id)
            logger.info(f'✓ Terminate result: {result}')
            
            # Remove from MongoDB
            logger.info('Removing pod metadata from MongoDB...')
            delete_result = pods_collection.delete_one({'runpod_id': pod_id})
            logger.info(f'✓ Deleted {delete_result.deleted_count} document(s)')
        else:
            logger.warning(f'✗ Invalid action: {action}')
            logger.info('='*50)
            return jsonify({'error': 'Invalid action'}), 400
        
        logger.info('✓ Action completed successfully')
        logger.info('='*50)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        logger.error('='*50)
        logger.error(f'ERROR in pod_action: {e}', exc_info=True)
        logger.error('='*50)
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods/public', methods=['GET'])
def get_public_pods():
    """Get public pods for CLI users"""
    try:
        # This endpoint doesn't require full auth, just basic token verification
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_data = verify_clerk_token(token)
            if not user_data:
                return jsonify({'error': 'Invalid token'}), 401
        else:
            return jsonify({'error': 'No token provided'}), 401
            
        # Get public pods from MongoDB
        public_pods = list(pods_collection.find({'is_public': True}))
        
        pods = []
        for pod in public_pods:
            # Get current status from RunPod
            try:
                rp_pod = runpod.get_pod(pod['runpod_id'])
                if rp_pod and rp_pod.get('desiredStatus') == 'RUNNING':
                    pods.append({
                        'id': pod['runpod_id'],
                        'name': pod['name'],
                        'status': rp_pod.get('desiredStatus'),
                        'created_at': pod.get('created_at')
                    })
            except:
                continue
                
        return jsonify({'pods': pods})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods/<pod_id>/connect', methods=['POST'])
def connect_to_pod(pod_id):
    """Connect to a pod via CLI"""
    try:
        # Verify token
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_data = verify_clerk_token(token)
            if not user_data:
                return jsonify({'error': 'Invalid token'}), 401
        else:
            return jsonify({'error': 'No token provided'}), 401
            
        # Check if pod is public
        pod_doc = pods_collection.find_one({'runpod_id': pod_id})
        if not pod_doc or not pod_doc.get('is_public'):
            return jsonify({'error': 'Pod not accessible'}), 403
            
        # Get pod details from RunPod
        pod = runpod.get_pod(pod_id)
        if not pod or pod.get('desiredStatus') != 'RUNNING':
            return jsonify({'error': 'Pod not running'}), 400
            
        # Get SSH connection details
        ssh_info = {
            'host': pod.get('machine', {}).get('publicIpAddress'),
            'port': 22,
            'username': 'root',
            'user_folder': user_data.get('username', 'user')
        }
        
        return jsonify({'ssh_info': ssh_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pods/<pod_id>/files', methods=['GET'])
@require_auth
def list_pod_files(pod_id):
    """List files in a pod directory"""
    try:
        path = request.args.get('path', '/workspace')
        
        # Get pod details
        pod = runpod.get_pod(pod_id)
        if not pod or pod.get('desiredStatus') != 'RUNNING':
            return jsonify({'error': 'Pod not running'}), 400
        
        # Get SSH connection details (simplified for demo)
        # In production, you'd retrieve stored SSH keys from database
        host = pod.get('machine', {}).get('publicIpAddress')
        if not host:
            return jsonify({'error': 'Pod host not available'}), 400
        
        # Create file manager instance (this would need proper SSH key management)
        file_manager = PodFileManager(host)
        
        # For now, return mock data since we don't have SSH keys set up
        mock_files = [
            {'name': 'notebooks', 'type': 'directory', 'size': 0, 'modified': 1640995200},
            {'name': 'datasets', 'type': 'directory', 'size': 0, 'modified': 1640995200},
            {'name': 'models', 'type': 'directory', 'size': 0, 'modified': 1640995200},
            {'name': 'requirements.txt', 'type': 'file', 'size': 1024, 'modified': 1640995200},
            {'name': 'main.py', 'type': 'file', 'size': 2048, 'modified': 1640995200},
        ]
        
        return jsonify({'files': mock_files, 'path': path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'godfather-backend',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/pods/<pod_id>/files/upload', methods=['POST'])
@require_auth
def upload_file_to_pod(pod_id):
    """Upload a file to pod"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        remote_path = request.form.get('path', '/workspace')
        
        # In production, implement actual file upload
        return jsonify({'success': True, 'message': 'File upload functionality will be implemented with proper SSH key management'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)