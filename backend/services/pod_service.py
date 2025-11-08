"""Pod management service"""
import runpod
from typing import Optional, List, Dict
from datetime import datetime
from config.settings import settings
from config.database import pods_collection
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize RunPod
runpod.api_key = settings.RUNPOD_API_KEY


class PodService:
    """Handle pod operations with RunPod"""
    
    @staticmethod
    def get_all_pods() -> List[Dict]:
        """Get all pods from RunPod"""
        try:
            logger.info('Fetching pods from RunPod API')
            runpod_pods = runpod.get_pods()
            logger.info(f'Fetched {len(runpod_pods) if runpod_pods else 0} pods from RunPod')
            
            # Get additional data from MongoDB
            db_pods = list(pods_collection.find())
            logger.info(f'Found {len(db_pods)} pod records in MongoDB')
            
            # Merge data
            pods = []
            for rp_pod in runpod_pods:
                pod_id = rp_pod['id']
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
            
            return pods
        except Exception as e:
            logger.error(f'Error fetching pods: {e}', exc_info=True)
            raise
    
    @staticmethod
    def get_pod(pod_id: str) -> Optional[Dict]:
        """Get a specific pod"""
        try:
            logger.info(f'Fetching pod {pod_id} from RunPod')
            pod = runpod.get_pod(pod_id)
            
            if not pod:
                logger.warning(f'Pod {pod_id} not found in RunPod')
                return None
            
            # Get additional data from MongoDB
            db_pod = pods_collection.find_one({'runpod_id': pod_id})
            
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
            
            return pod_data
        except Exception as e:
            logger.error(f'Error fetching pod {pod_id}: {e}', exc_info=True)
            raise
    
    @staticmethod
    def create_pod(config: Dict, creator_id: str, ssh_public_key: str) -> Optional[Dict]:
        """Create a new pod"""
        try:
            logger.info(f'Creating pod: {config.get("name")}')
            
            # Extract custom fields that shouldn't be sent to RunPod API
            is_public = config.pop('is_public', False)
            allowed_users = config.pop('allowed_users', [])
            use_cpu_only = config.pop('use_cpu_only', False)
            
            # Add SSH public key as environment variable
            env = config.get('env', {})
            env['GODFATHER_SSH_PUBLIC_KEY'] = ssh_public_key
            env['GODFATHER_SETUP'] = 'true'
            config['env'] = env
            
            # Handle CPU vs GPU configuration
            # For CPU-only pods, use instanceIds and computeType instead of gpu_type_id
            if use_cpu_only:
                # Remove gpu_type_id if present
                config.pop('gpu_type_id', None)
                config.pop('instance_id', None)  # Remove singular form if present
                
                # Set computeType to CPU (camelCase for GraphQL)
                config['computeType'] = 'CPU'
                
                # Set instanceIds (plural, array, camelCase) for CPU if not already set
                if 'instanceIds' not in config and 'instance_ids' not in config:
                    # Default CPU instance type - must be an array
                    config['instanceIds'] = ['cpu3c-2-4']
                elif 'instance_ids' in config:
                    # Convert snake_case to camelCase
                    config['instanceIds'] = config.pop('instance_ids')
                    
                # Set gpuCount to 0 for CPU-only pods
                config['gpuCount'] = 0
                
                logger.info(f'Creating CPU-only pod with instanceIds: {config.get("instanceIds")} and computeType: CPU')
                logger.info(f'Full CPU config: {config}')
            else:
                # For GPU pods, remove CPU-specific fields if present
                config.pop('instance_id', None)
                config.pop('instance_ids', None)
                config.pop('instanceIds', None)
                config.pop('compute_type', None)
                config.pop('computeType', None)
                logger.info(f'Creating GPU pod with gpu_type_id: {config.get("gpu_type_id")}')
            
            # Create pod via RunPod API
            logger.info(f'Calling runpod.create_pod with config keys: {list(config.keys())}')
            pod = runpod.create_pod(**config)
            
            if pod and 'id' in pod:
                logger.info(f'Pod created successfully: {pod["id"]}')
                
                # Store additional data in MongoDB
                pod_doc = {
                    'runpod_id': pod['id'],
                    'name': config['name'],
                    'is_public': is_public,
                    'allowed_users': allowed_users,
                    'custom_config': config,
                    'ssh_public_key': ssh_public_key,
                    'created_by': creator_id,
                    'created_at': datetime.utcnow()
                }
                
                pods_collection.insert_one(pod_doc)
                logger.info('Pod metadata stored successfully')
                
                return pod
            else:
                logger.error('Failed to create pod - no ID returned')
                return None
                
        except Exception as e:
            logger.error(f'Error creating pod: {e}', exc_info=True)
            raise
    
    @staticmethod
    def update_pod(pod_id: str, updates: Dict) -> bool:
        """Update pod configuration in database"""
        try:
            logger.info(f'Updating pod {pod_id}')
            
            update_doc = {}
            if 'is_public' in updates:
                update_doc['is_public'] = updates['is_public']
            if 'allowed_users' in updates:
                update_doc['allowed_users'] = updates['allowed_users']
            
            if update_doc:
                result = pods_collection.update_one(
                    {'runpod_id': pod_id},
                    {'$set': update_doc}
                )
                logger.info(f'Matched: {result.matched_count}, Modified: {result.modified_count}')
                return result.modified_count > 0
            
            return False
        except Exception as e:
            logger.error(f'Error updating pod {pod_id}: {e}', exc_info=True)
            raise
    
    @staticmethod
    def stop_pod(pod_id: str) -> Dict:
        """Stop a pod"""
        try:
            logger.info(f'Stopping pod {pod_id}')
            result = runpod.stop_pod(pod_id)
            logger.info('Pod stopped successfully')
            return result
        except Exception as e:
            logger.error(f'Error stopping pod {pod_id}: {e}', exc_info=True)
            raise
    
    @staticmethod
    def start_pod(pod_id: str) -> Dict:
        """Start/resume a pod"""
        try:
            logger.info(f'Starting pod {pod_id}')
            result = runpod.resume_pod(pod_id)
            logger.info('Pod started successfully')
            return result
        except Exception as e:
            logger.error(f'Error starting pod {pod_id}: {e}', exc_info=True)
            raise
    
    @staticmethod
    def restart_pod(pod_id: str) -> Dict:
        """Restart a pod"""
        try:
            logger.info(f'Restarting pod {pod_id}')
            runpod.stop_pod(pod_id)
            result = runpod.resume_pod(pod_id)
            logger.info('Pod restarted successfully')
            return result
        except Exception as e:
            logger.error(f'Error restarting pod {pod_id}: {e}', exc_info=True)
            raise
    
    @staticmethod
    def terminate_pod(pod_id: str) -> Dict:
        """Terminate a pod"""
        try:
            logger.info(f'Terminating pod {pod_id}')
            result = runpod.terminate_pod(pod_id)
            
            # Remove from MongoDB
            delete_result = pods_collection.delete_one({'runpod_id': pod_id})
            logger.info(f'Deleted {delete_result.deleted_count} document(s) from MongoDB')
            
            return result
        except Exception as e:
            logger.error(f'Error terminating pod {pod_id}: {e}', exc_info=True)
            raise
    
    @staticmethod
    def get_accessible_pods(discord_user_id: str) -> List[Dict]:
        """Get pods accessible to a user (public or explicitly allowed)"""
        try:
            query = {
                '$or': [
                    {'is_public': True},
                    {'allowed_users': discord_user_id}
                ]
            }
            
            accessible_pods = list(pods_collection.find(query))
            logger.info(f'Found {len(accessible_pods)} accessible pods for user {discord_user_id}')
            
            pods = []
            for pod in accessible_pods:
                try:
                    rp_pod = runpod.get_pod(pod['runpod_id'])
                    if rp_pod and rp_pod.get('desiredStatus') == 'RUNNING':
                        pod_info = {
                            'id': pod['runpod_id'],
                            'name': pod['name'],
                            'status': rp_pod.get('desiredStatus'),
                            'created_at': pod.get('created_at'),
                            'is_public': pod.get('is_public', False)
                        }
                        pods.append(pod_info)
                except Exception as e:
                    logger.error(f'Error checking pod {pod.get("runpod_id")}: {e}')
                    continue
            
            return pods
        except Exception as e:
            logger.error(f'Error fetching accessible pods: {e}', exc_info=True)
            raise
    
    @staticmethod
    def check_pod_access(pod_id: str, discord_user_id: str) -> bool:
        """Check if user has access to a pod"""
        try:
            pod_doc = pods_collection.find_one({'runpod_id': pod_id})
            
            if not pod_doc:
                return False
            
            is_public = pod_doc.get('is_public', False)
            allowed_users = pod_doc.get('allowed_users', [])
            
            return is_public or (discord_user_id in allowed_users)
        except Exception as e:
            logger.error(f'Error checking pod access: {e}', exc_info=True)
            return False
    
    @staticmethod
    def get_pod_ssh_info(pod_id: str) -> Optional[Dict]:
        """Get SSH connection information for a pod"""
        try:
            pod = runpod.get_pod(pod_id)
            
            if not pod:
                logger.error(f'Pod {pod_id} not found')
                return None
            
            if pod.get('desiredStatus') != 'RUNNING':
                logger.warning(f'Pod {pod_id} is not running')
                return None
            
            runtime = pod.get('runtime')
            if not runtime:
                logger.warning('Pod runtime not yet available')
                return None
            
            # Get host and port from runtime
            host = None
            port = 22
            
            if runtime.get('ports'):
                for port_info in runtime.get('ports', []):
                    if port_info.get('privatePort') == 22:
                        host = port_info.get('ip')
                        port = port_info.get('publicPort', 22)
                        break
            
            if not host and pod.get('machine'):
                host = pod.get('machine', {}).get('podHostId')
            
            if not host:
                logger.error('No host information available')
                return None
            
            return {
                'host': host,
                'port': port,
                'username': 'root'
            }
        except Exception as e:
            logger.error(f'Error getting pod SSH info: {e}', exc_info=True)
            return None
