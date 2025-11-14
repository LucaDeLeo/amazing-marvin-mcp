#!/usr/bin/env python3
"""
Test script for Amazing Marvin MCP Server

This script verifies that your API token is working and the server can connect
to Amazing Marvin successfully.
"""

import asyncio
import os
import httpx


MARVIN_API_BASE = "https://serv.amazingmarvin.com/api"


async def test_connection():
    """Test connection to Amazing Marvin API"""
    api_token = os.getenv("AMAZING_MARVIN_API_TOKEN")
    
    if not api_token:
        print("❌ ERROR: AMAZING_MARVIN_API_TOKEN environment variable not set")
        print("\nPlease set your API token:")
        print("  export AMAZING_MARVIN_API_TOKEN='your-token-here'")
        return False
    
    print(f"✓ API token found: {api_token[:10]}...")
    
    # Test API connection
    print("\n🔄 Testing connection to Amazing Marvin API...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test with categories endpoint (simple read operation)
            response = await client.get(
                f"{MARVIN_API_BASE}/categories",
                headers={"X-API-Token": api_token}
            )
            
            if response.status_code == 200:
                print("✅ Successfully connected to Amazing Marvin!")
                categories = response.json()
                print(f"   Found {len(categories)} categories/projects")
                return True
            else:
                print(f"❌ Connection failed with status code: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except httpx.HTTPError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_features():
    """Test various API features"""
    api_token = os.getenv("AMAZING_MARVIN_API_TOKEN")
    
    print("\n🧪 Testing API features...\n")
    
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Token": api_token}
        
        # Test 1: Get labels
        print("1. Testing labels endpoint...")
        try:
            response = await client.get(f"{MARVIN_API_BASE}/labels", headers=headers)
            labels = response.json()
            print(f"   ✓ Found {len(labels)} labels")
        except Exception as e:
            print(f"   ✗ Labels test failed: {e}")
        
        # Test 2: Get today's tasks
        print("2. Testing today's tasks endpoint...")
        try:
            response = await client.get(f"{MARVIN_API_BASE}/todayItems", headers=headers)
            tasks = response.json()
            print(f"   ✓ Found {len(tasks)} tasks for today")
        except Exception as e:
            print(f"   ✗ Today's tasks test failed: {e}")
        
        # Test 3: Check due tasks
        print("3. Testing due tasks endpoint...")
        try:
            response = await client.get(f"{MARVIN_API_BASE}/dueItems", headers=headers)
            due_tasks = response.json()
            print(f"   ✓ Found {len(due_tasks)} due/overdue tasks")
        except Exception as e:
            print(f"   ✗ Due tasks test failed: {e}")


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Amazing Marvin MCP Server - Connection Test")
    print("=" * 50)
    
    success = await test_connection()
    
    if success:
        await test_features()
        print("\n" + "=" * 50)
        print("✅ All tests passed! Your setup is ready.")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Add the server to your Claude Desktop config")
        print("2. Restart Claude Desktop")
        print("3. Start using Amazing Marvin through Claude!")
    else:
        print("\n" + "=" * 50)
        print("❌ Tests failed. Please check your setup.")
        print("=" * 50)
        print("\nTroubleshooting:")
        print("1. Verify your API token is correct")
        print("2. Check you have internet connection")
        print("3. Ensure API feature is enabled in Marvin settings")


if __name__ == "__main__":
    asyncio.run(main())
