#!/usr/bin/env python3
"""
Test Neo4j connection using configuration from .env.devel
"""

import sys
import os
from pathlib import Path

# Load .env.devel
from dotenv import load_dotenv

# Load from .env.devel instead of .env
env_devel_path = Path(__file__).parent / ".env.devel"
load_dotenv(env_devel_path)

from src.config import neo4j_config

def test_neo4j_connection():
    """Test Neo4j connection with loaded configuration."""
    
    print("=" * 100)
    print("NEO4J CONNECTION TEST")
    print("=" * 100)
    
    # Display configuration (without password)
    print("\n📋 Configuration Loaded:")
    print(f"  URI:      {neo4j_config.uri}")
    print(f"  User:     {neo4j_config.user}")
    print(f"  Database: {neo4j_config.database}")
    print(f"  Encrypted: {neo4j_config.encrypted}")
    print(f"  Auth:     {neo4j_config.auth_enabled}")
    
    try:
        from neo4j import GraphDatabase
        
        print("\n🔌 Attempting connection...")
        
        # Create driver
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password),
            encrypted=neo4j_config.encrypted
        )
        
        # Test connection
        with driver.session(database=neo4j_config.database) as session:
            result = session.run("RETURN 'Connection successful!' as message")
            record = result.single()
            if record:
                message = record["message"]
            else:
                message = "Connection successful!"
            
            print(f"\n✅ {message}")
            
            # Get database info
            result = session.run("""
                CALL dbms.components() 
                YIELD name, versions 
                RETURN name, versions[0] as version
            """)
            
            for record in result:
                print(f"   {record['name']}: {record['version']}")
            
            # Get node count
            result = session.run("MATCH (n) RETURN COUNT(n) as count")
            record = result.single()
            if record:
                count = record["count"]
                print(f"\n📊 Current Nodes in Database: {count}")
            else:
                print(f"\n📊 Current Nodes in Database: 0")
        
        driver.close()
        print("\n" + "=" * 100)
        print("✅ NEO4J CONNECTION TEST PASSED")
        print("=" * 100)
        return True
        
    except ImportError:
        print("\n❌ neo4j package not installed")
        print("   Install with: pip install neo4j")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}")
        print(f"   {str(e)}")
        print("\n🔍 Troubleshooting:")
        print(f"   1. Check Neo4j is running on {neo4j_config.uri}")
        print(f"   2. Verify credentials in .env.devel")
        print(f"   3. Check firewall/network connectivity")
        print("\n" + "=" * 100)
        print("❌ NEO4J CONNECTION TEST FAILED")
        print("=" * 100)
        return False

if __name__ == "__main__":
    success = test_neo4j_connection()
    sys.exit(0 if success else 1)
