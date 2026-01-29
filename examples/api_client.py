#!/usr/bin/env python3
"""
Example API client for ANPR System

Shows how to interact with the ANPR API.
"""

import requests
import json

class ANPRClient:
    """Simple API client for ANPR System"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def health_check(self):
        """Check system health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_cameras(self):
        """Get all cameras"""
        response = requests.get(f"{self.base_url}/api/v1/cameras")
        return response.json()
    
    def get_results(self, limit=10):
        """Get recent results"""
        response = requests.get(
            f"{self.base_url}/api/v1/results",
            params={"limit": limit}
        )
        return response.json()

if __name__ == "__main__":
    client = ANPRClient()
    
    print("ANPR API Client Example")
    print("=" * 50)
    
    # Health check
    print("\n1. Health Check:")
    try:
        health = client.health_check()
        print(f"   Status: {health}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. Get Cameras:")
    try:
        cameras = client.get_cameras()
        print(f"   Cameras: {len(cameras)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Get Results:")
    try:
        results = client.get_results(limit=5)
        print(f"   Results: {len(results)}")
    except Exception as e:
        print(f"   Error: {e}")