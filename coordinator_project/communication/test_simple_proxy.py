#!/usr/bin/env python3
"""
Test simple pour vérifier le comportement du proxy avec les canaux ouverts - Version corrigée
"""

import asyncio
import json
import time

async def test_open_channel():
    """Test avec un canal ouvert (pas d'authentification)"""
    print("🧪 Test canal ouvert sans authentification")
    
    # Subscriber
    try:
        reader1, writer1 = await asyncio.open_connection('localhost', 6380)
        
        # S'abonner au canal ouvert avec nom correct
        channel_name = "test/channel"
        subscribe_cmd = f"*2\r\n$9\r\nSUBSCRIBE\r\n${len(channel_name)}\r\n{channel_name}\r\n".encode()
        
        print(f"📤 Commande SUBSCRIBE: {subscribe_cmd}")
        writer1.write(subscribe_cmd)
        await writer1.drain()
        
        # Lire la confirmation
        confirmation = await reader1.read(1024)
        print(f"📥 Confirmation SUBSCRIBE: {confirmation}")
        
        # Publisher
        reader2, writer2 = await asyncio.open_connection('localhost', 6380)
        
        # Attendre un peu
        await asyncio.sleep(1)
        
        # Publier un message simple sur canal ouvert
        test_message = {
            "message_id": "test_001",
            "content": "Hello from open channel!",
            "timestamp": time.time()
        }
        message_json = json.dumps(test_message)
        
        publish_cmd = f"*3\r\n$7\r\nPUBLISH\r\n${len(channel_name)}\r\n{channel_name}\r\n${len(message_json)}\r\n{message_json}\r\n"
        
        print(f"📤 Envoi message: {test_message}")
        print(f"📤 Commande PUBLISH: {publish_cmd.encode()}")
        writer2.write(publish_cmd.encode())
        await writer2.drain()
        
        # Lire la réponse du PUBLISH
        publish_response = await reader2.read(1024)
        print(f"📨 Réponse PUBLISH: {publish_response}")
        
        # Lire le message reçu par le subscriber
        print("📥 Attente du message...")
        received_data = await asyncio.wait_for(reader1.read(4096), timeout=10.0)
        print(f"📥 Message reçu par subscriber: {received_data}")
        
        # Parser le message
        received_str = received_data.decode('utf-8', errors='replace')
        print(f"📄 Message décodé: {received_str}")
        
        # Fermer les connexions
        writer1.close()
        writer2.close()
        await writer1.wait_closed()
        await writer2.wait_closed()
        
        print("✅ Test canal ouvert terminé")
        
    except Exception as e:
        print(f"❌ Erreur test canal ouvert: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🚀 Test simple du proxy - Canaux ouverts (Version corrigée)")
    print("=" * 60)
    
    await test_open_channel()

if __name__ == "__main__":
    asyncio.run(main())