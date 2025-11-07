"""Pod file management routes"""
from flask import Blueprint, request, jsonify, send_file
from middleware.auth import require_auth
from services.ssh_service import SSHService
from services.pod_service import PodService
from file_manager import PodFileManager
from utils.logger import get_logger
import tempfile
import os

logger = get_logger(__name__)

files_bp = Blueprint('files', __name__, url_prefix='/api/pods')


def get_file_manager_for_pod(pod_id: str):
    """Helper to create file manager instance for a pod
    Returns tuple of (file_manager, key_path) on success
    Returns tuple of (None, error_response) on failure
    """
    # Get SSH info
    ssh_info = PodService.get_pod_ssh_info(pod_id)
    if not ssh_info:
        return None, (jsonify({'error': 'Pod network information not available'}), 503)
    
    # Get SSH key
    private_key = SSHService.get_private_key()
    if not private_key:
        return None, (jsonify({'error': 'SSH key not configured'}), 500)
    
    # Save key to temp file
    key_path = SSHService.save_key_to_temp_file(private_key)
    if not key_path:
        return None, (jsonify({'error': 'Failed to setup SSH key'}), 500)
    
    # Create file manager
    file_manager = PodFileManager(
        host=ssh_info['host'],
        port=ssh_info['port'],
        username=ssh_info['username'],
        ssh_key_path=key_path
    )
    
    if not file_manager.connect():
        SSHService.cleanup_temp_key(key_path)
        return None, (jsonify({'error': 'Failed to connect to pod'}), 500)
    
    return file_manager, key_path


@files_bp.route('/<pod_id>/files', methods=['GET'])
@require_auth
def list_pod_files(pod_id):
    """List files in a pod directory"""
    try:
        path = request.args.get('path', '/workspace')
        logger.info(f'List files in {path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        # List directory
        files = file_manager.list_directory(path)
        
        # Cleanup
        file_manager.disconnect()
        SSHService.cleanup_temp_key(key_path)
        
        return jsonify({'files': files, 'path': path})
        
    except Exception as e:
        logger.error(f'Error in list_pod_files: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/upload', methods=['POST'])
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
        logger.info(f'Upload {file.filename} to {remote_path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            local_path = temp_file.name
        
        try:
            # Upload file
            full_remote_path = f"{remote_path.rstrip('/')}/{file.filename}"
            
            if not file_manager.upload_file(local_path, full_remote_path):
                return jsonify({'error': 'Failed to upload file'}), 500
            
            logger.info('File uploaded successfully')
            
            return jsonify({
                'success': True,
                'message': f'File {file.filename} uploaded successfully',
                'path': full_remote_path
            })
        finally:
            # Cleanup
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
            if os.path.exists(local_path):
                os.unlink(local_path)
        
    except Exception as e:
        logger.error(f'Error in upload_file_to_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/download', methods=['POST'])
@require_auth
def download_file_from_pod(pod_id):
    """Download a file from pod"""
    try:
        data = request.get_json()
        remote_path = data.get('path')
        
        if not remote_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        logger.info(f'Download {remote_path} from pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        # Create temp file for download
        temp_download = tempfile.NamedTemporaryFile(delete=False)
        temp_download.close()
        local_path = temp_download.name
        
        try:
            # Download file
            if not file_manager.download_file(remote_path, local_path):
                return jsonify({'error': 'Failed to download file'}), 500
            
            filename = os.path.basename(remote_path)
            
            return send_file(
                local_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in download_file_from_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/delete', methods=['DELETE'])
@require_auth
def delete_file_from_pod(pod_id):
    """Delete a file or directory from pod"""
    try:
        data = request.get_json()
        file_path = data.get('path')
        file_type = data.get('type', 'file')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        logger.info(f'Delete {file_type} {file_path} from pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            # Delete file or directory
            if file_type == 'directory':
                success = file_manager.delete_directory(file_path)
            else:
                success = file_manager.delete_file(file_path)
            
            if not success:
                return jsonify({'error': 'Failed to delete item'}), 500
            
            return jsonify({'success': True, 'message': 'Item deleted successfully'})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in delete_file_from_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/mkdir', methods=['POST'])
@require_auth
def create_directory_in_pod(pod_id):
    """Create a directory in pod"""
    try:
        data = request.get_json()
        dir_path = data.get('path')
        
        if not dir_path:
            return jsonify({'error': 'No directory path provided'}), 400
        
        logger.info(f'Create directory {dir_path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            if not file_manager.create_directory(dir_path):
                return jsonify({'error': 'Failed to create directory'}), 500
            
            return jsonify({'success': True, 'message': 'Directory created successfully'})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in create_directory_in_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/read', methods=['POST'])
@require_auth
def read_file_from_pod(pod_id):
    """Read file content from pod"""
    try:
        data = request.get_json()
        file_path = data.get('path')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        logger.info(f'Read file {file_path} from pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            content = file_manager.read_file(file_path)
            if content is None:
                return jsonify({'error': 'Failed to read file'}), 500
            
            return jsonify({'success': True, 'content': content, 'path': file_path})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in read_file_from_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/write', methods=['POST'])
@require_auth
def write_file_to_pod(pod_id):
    """Write content to a file on pod"""
    try:
        data = request.get_json()
        file_path = data.get('path')
        content = data.get('content')
        
        if not file_path or content is None:
            return jsonify({'error': 'Missing file path or content'}), 400
        
        logger.info(f'Write file {file_path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            if not file_manager.write_file(file_path, content):
                return jsonify({'error': 'Failed to write file'}), 500
            
            return jsonify({'success': True, 'message': 'File saved successfully'})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in write_file_to_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/rename', methods=['POST'])
@require_auth
def rename_file_in_pod(pod_id):
    """Rename a file or directory in pod"""
    try:
        data = request.get_json()
        old_path = data.get('old_path')
        new_path = data.get('new_path')
        
        if not old_path or not new_path:
            return jsonify({'error': 'Missing old_path or new_path'}), 400
        
        logger.info(f'Rename {old_path} to {new_path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            if not file_manager.rename(old_path, new_path):
                return jsonify({'error': 'Failed to rename item'}), 500
            
            return jsonify({'success': True, 'message': 'Item renamed successfully'})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in rename_file_in_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/copy', methods=['POST'])
@require_auth
def copy_file_in_pod(pod_id):
    """Copy a file or directory in pod"""
    try:
        data = request.get_json()
        source_path = data.get('source_path')
        dest_path = data.get('dest_path')
        
        if not source_path or not dest_path:
            return jsonify({'error': 'Missing source_path or dest_path'}), 400
        
        logger.info(f'Copy {source_path} to {dest_path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            if not file_manager.copy(source_path, dest_path):
                return jsonify({'error': 'Failed to copy item'}), 500
            
            return jsonify({'success': True, 'message': 'Item copied successfully'})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in copy_file_in_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<pod_id>/files/search', methods=['GET'])
@require_auth
def search_files_in_pod(pod_id):
    """Search for files in pod by name pattern"""
    try:
        query = request.args.get('query', '')
        path = request.args.get('path', '/workspace')
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400
        
        logger.info(f'Search for "{query}" in {path} on pod {pod_id}')
        
        file_manager, result = get_file_manager_for_pod(pod_id)
        if not file_manager:
            return result  # Returns error tuple (jsonify, status_code)
        
        key_path = result
        
        try:
            results = file_manager.search_files(path, query)
            return jsonify({'success': True, 'results': results})
        finally:
            file_manager.disconnect()
            SSHService.cleanup_temp_key(key_path)
        
    except Exception as e:
        logger.error(f'Error in search_files_in_pod: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
