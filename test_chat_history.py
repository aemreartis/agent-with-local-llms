#!/usr/bin/env python3
"""
Test Chat History Storage in PostgreSQL
Demonstrates how chat history is stored and retrieved
"""

import asyncio
import json
import subprocess
from datetime import datetime

def test_postgresql_connection():
    """Test PostgreSQL connection and table structure"""
    print("🗄️ Testing PostgreSQL Connection...")
    
    # Test connection
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgresql", "psql", "-U", "rag_user", "-d", "agentic_rag", "-c", "SELECT version();"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ PostgreSQL: Connected")
    else:
        print(f"❌ PostgreSQL: Failed - {result.stderr}")
        return False
    
    # Check if conversation_memory table exists
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgresql", "psql", "-U", "rag_user", "-d", "agentic_rag", "-c", "\\dt conversation_memory"
    ], capture_output=True, text=True)
    
    if result.returncode == 0 and "conversation_memory" in result.stdout:
        print("✅ conversation_memory table: Exists")
    else:
        print("❌ conversation_memory table: Not found")
        return False
    
    return True

def create_sample_chat_history():
    """Create sample chat history in the database"""
    print("\n💬 Creating Sample Chat History...")
    
    # Sample conversation data
    conversation_id = "test_conversation_123"
    messages = [
        {
            "role": "user",
            "content": "Hello! How are you today?",
            "timestamp": datetime.now().isoformat()
        },
        {
            "role": "assistant", 
            "content": "Hello! I'm doing well, thank you for asking. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        },
        {
            "role": "user",
            "content": "Can you tell me about artificial intelligence?",
            "timestamp": datetime.now().isoformat()
        },
        {
            "role": "assistant",
            "content": "Artificial Intelligence (AI) is a branch of computer science that aims to create systems capable of performing tasks that typically require human intelligence. This includes learning, reasoning, problem-solving, perception, and language understanding.",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Insert messages into database
    for i, message in enumerate(messages):
        key_name = f"{conversation_id}_{i}"
        data_json = json.dumps(message)
        
        result = subprocess.run([
            "docker-compose", "exec", "-T", "postgresql", "psql", "-U", "rag_user", "-d", "agentic_rag", 
            "-c", f"INSERT INTO conversation_memory (key_name, data) VALUES ('{key_name}', '{data_json}'::jsonb);"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Message {i+1}: Stored")
        else:
            print(f"❌ Message {i+1}: Failed - {result.stderr}")
    
    return conversation_id

def query_chat_history(conversation_id):
    """Query and display chat history"""
    print(f"\n📖 Querying Chat History for: {conversation_id}")
    
    # Query all messages for this conversation
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgresql", "psql", "-U", "rag_user", "-d", "agentic_rag",
        "-c", f"SELECT key_name, data, created_at FROM conversation_memory WHERE key_name LIKE '{conversation_id}%' ORDER BY created_at;"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Chat History Retrieved:")
        print("-" * 60)
        
        lines = result.stdout.strip().split('\n')
        for line in lines[2:]:  # Skip header lines
            if line.strip():
                parts = line.split('|')
                if len(parts) >= 3:
                    key = parts[0].strip()
                    data = parts[1].strip()
                    timestamp = parts[2].strip()
                    
                    try:
                        message_data = json.loads(data)
                        role = message_data.get('role', 'unknown')
                        content = message_data.get('content', '')[:50] + "..." if len(message_data.get('content', '')) > 50 else message_data.get('content', '')
                        
                        print(f"👤 {role.upper()}: {content}")
                        print(f"   📅 {timestamp}")
                        print()
                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse message data: {data}")
    else:
        print(f"❌ Failed to query chat history: {result.stderr}")

def show_database_stats():
    """Show database statistics"""
    print("\n📊 Database Statistics...")
    
    # Count total conversations
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgresql", "psql", "-U", "rag_user", "-d", "agentic_rag",
        "-c", "SELECT COUNT(*) as total_messages FROM conversation_memory;"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Total messages stored:", result.stdout.strip().split('\n')[2].strip())
    
    # Show recent conversations
    result = subprocess.run([
        "docker-compose", "exec", "-T", "postgresql", "psql", "-U", "rag_user", "-d", "agentic_rag",
        "-c", "SELECT key_name, created_at FROM conversation_memory ORDER BY created_at DESC LIMIT 5;"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n📅 Recent Messages:")
        lines = result.stdout.strip().split('\n')
        for line in lines[2:]:  # Skip header lines
            if line.strip():
                print(f"   {line.strip()}")

def show_query_examples():
    """Show examples of how to query chat history"""
    print("\n🔍 Query Examples for Chat History:")
    print("=" * 60)
    
    queries = [
        {
            "name": "All messages for a conversation",
            "sql": "SELECT * FROM conversation_memory WHERE key_name LIKE 'conv_123%' ORDER BY created_at;"
        },
        {
            "name": "Recent messages (last 10)",
            "sql": "SELECT * FROM conversation_memory ORDER BY created_at DESC LIMIT 10;"
        },
        {
            "name": "Messages by role (user only)",
            "sql": "SELECT * FROM conversation_memory WHERE data->>'role' = 'user' ORDER BY created_at;"
        },
        {
            "name": "Messages by role (assistant only)", 
            "sql": "SELECT * FROM conversation_memory WHERE data->>'role' = 'assistant' ORDER BY created_at;"
        },
        {
            "name": "Messages containing specific text",
            "sql": "SELECT * FROM conversation_memory WHERE data->>'content' ILIKE '%AI%' ORDER BY created_at;"
        },
        {
            "name": "Messages from today",
            "sql": "SELECT * FROM conversation_memory WHERE DATE(created_at) = CURRENT_DATE ORDER BY created_at;"
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query['name']}")
        print(f"   SQL: {query['sql']}")
        print()

def main():
    """Main test function"""
    print("🚀 Chat History Storage Test")
    print("=" * 60)
    
    # Test PostgreSQL connection
    if not test_postgresql_connection():
        print("❌ PostgreSQL connection failed. Exiting.")
        return
    
    # Create sample chat history
    conversation_id = create_sample_chat_history()
    
    # Query the chat history
    query_chat_history(conversation_id)
    
    # Show database stats
    show_database_stats()
    
    # Show query examples
    show_query_examples()
    
    print("\n🎉 Chat History Storage Test Complete!")
    print("\n💡 To query chat history manually:")
    print("   docker-compose exec postgresql psql -U rag_user -d agentic_rag")
    print("   SELECT * FROM conversation_memory ORDER BY created_at DESC;")

if __name__ == "__main__":
    main() 