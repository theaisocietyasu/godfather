"""CLI Pod Operations module"""
import requests
from typing import List, Dict, Optional


class PodManager:
    """Handle pod operations"""
    
    def __init__(self, api_base: str):
        self.api_base = api_base
    
    def get_public_pods(self, token: str) -> List[Dict]:
        """Get list of public pods available for connection"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                f'{self.api_base}/api/pods/public',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('pods', [])
            elif response.status_code == 401:
                print("❌ Token expired. Please re-authenticate.")
                return []
            else:
                error = response.json().get('error', 'Failed to fetch pods')
                print(f"❌ Error: {error}")
                return []
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return []
    
    def get_connection_info(self, pod_id: str, token: str) -> Optional[Dict]:
        """Get SSH connection information for a pod"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(
                f'{self.api_base}/api/pods/{pod_id}/connect',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('ssh_info')
            else:
                error = response.json().get('error', 'Connection failed')
                print(f"❌ Connection failed: {error}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def list_pods(self, token: str):
        """List available public pods"""
        print("📡 Fetching available pods...")
        pods = self.get_public_pods(token)
        
        if not pods:
            print("😔 No public pods available at the moment.")
            print("   Ask an admin to create and make pods public.")
            return
        
        print(f"\n🚀 Found {len(pods)} available pod(s):\n")
        
        for i, pod in enumerate(pods, 1):
            status_emoji = "🟢" if pod.get('status') == 'RUNNING' else "🔴"
            print(f"  {i}. {status_emoji} {pod['name']}")
            print(f"     ID: {pod['id']}")
            print(f"     Status: {pod.get('status', 'Unknown')}")
            print(f"     Created: {pod.get('created_at', 'Unknown')}")
            print()
    
    def select_pod(self, token: str) -> Optional[str]:
        """Interactive pod selection"""
        pods = self.get_public_pods(token)
        
        if not pods:
            print("😔 No public pods available.")
            return None
        
        print("\n🚀 Available pods:")
        for i, pod in enumerate(pods, 1):
            status_emoji = "🟢" if pod.get('status') == 'RUNNING' else "🔴"
            print(f"  {i}. {status_emoji} {pod['name']} ({pod['id'][:8]}...)")
        
        try:
            choice = int(input(f"\nSelect a pod (1-{len(pods)}): "))
            if 1 <= choice <= len(pods):
                return pods[choice - 1]['id']
            else:
                print("❌ Invalid selection")
                return None
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input or cancelled")
            return None
