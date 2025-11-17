#!/usr/bin/env python3
"""
Arreglar los problemas REALES del workflow
"""

import json
import uuid

with open('Frepi_MVP2_Agent_Architecture.json', 'r') as f:
    w = json.load(f)

print("=== ARREGLANDO PROBLEMAS REALES ===\n")

# PROBLEMA 1: Supplier Journey Agent - conectar LLM y Memory
print("1. Conectando Supplier Journey Agent a su LLM y Memory...")

if 'OpenAI Chat Supplier' in {n['name'] for n in w['nodes']}:
    # Existe un nodo que se llama "OpenAI Chat Supplier"
    # PERO Supplier Journey Agent necesita su propio LLM
    # Crear uno nuevo o reusar?
    # Revisemos qué tiene conectado OpenAI Chat Supplier
    if 'OpenAI Chat Supplier' in w['connections']:
        current_target = w['connections']['OpenAI Chat Supplier']['ai_languageModel'][0][0]['node']
        print(f"   OpenAI Chat Supplier actualmente → {current_target}")
        # Si ya está conectado a Supplier Manager Agent, necesitamos uno diferente para Supplier Journey

# Buscar si existe un LLM para Supplier Journey
has_supplier_journey_llm = False
for node_name, conn_data in w['connections'].items():
    if 'OpenAI' in node_name and 'ai_languageModel' in conn_data:
        for conn_list in conn_data['ai_languageModel']:
            for conn in conn_list:
                if conn['node'] == 'Supplier Journey Agent':
                    has_supplier_journey_llm = True
                    print(f"   ✅ {node_name} ya conectado a Supplier Journey Agent")

if not has_supplier_journey_llm:
    # Crear nuevos nodos LLM y Memory para Supplier Journey Agent
    print("   Creando OpenAI Chat Supplier Journey...")

    llm_node = {
        "parameters": {
            "model": "gpt-4o-mini",
            "options": {}
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1,
        "position": [-640, 920],
        "id": str(uuid.uuid4()),
        "name": "OpenAI Chat Supplier Journey",
        "credentials": {
            "openAiApi": {
                "id": "tGY4ih3okXdhCsCt",
                "name": "OpenAi account"
            }
        }
    }
    w['nodes'].append(llm_node)

    memory_node = {
        "parameters": {
            "sessionKey": "={{ $json.phone_number }}",
            "contextWindowLength": 5
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.2,
        "position": [-640, 1080],
        "id": str(uuid.uuid4()),
        "name": "Memory Supplier Journey"
    }
    w['nodes'].append(memory_node)

    # Conectar a Supplier Journey Agent
    w['connections']['OpenAI Chat Supplier Journey'] = {
        "ai_languageModel": [[{"node": "Supplier Journey Agent", "type": "ai_languageModel", "index": 0}]]
    }

    w['connections']['Memory Supplier Journey'] = {
        "ai_memory": [[{"node": "Supplier Journey Agent", "type": "ai_memory", "index": 0}]]
    }

    print("   ✅ OpenAI Chat Supplier Journey creado y conectado")
    print("   ✅ Memory Supplier Journey creado y conectado")

# PROBLEMA 2: Onboarding Flow Agent - crear y conectar LLM y Memory
print("\n2. Creando LLM y Memory para Onboarding Flow Agent...")

onboarding_llm_exists = any(n['name'] == 'OpenAI Chat Onboarding' for n in w['nodes'])

if not onboarding_llm_exists:
    llm_node = {
        "parameters": {
            "model": "gpt-4o-mini",
            "options": {}
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1,
        "position": [-2240, 760],
        "id": str(uuid.uuid4()),
        "name": "OpenAI Chat Onboarding",
        "credentials": {
            "openAiApi": {
                "id": "tGY4ih3okXdhCsCt",
                "name": "OpenAi account"
            }
        }
    }
    w['nodes'].append(llm_node)

    memory_node = {
        "parameters": {
            "sessionKey": "={{ $json.phone_number }}",
            "contextWindowLength": 3
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.2,
        "position": [-2240, 920],
        "id": str(uuid.uuid4()),
        "name": "Memory Onboarding"
    }
    w['nodes'].append(memory_node)

    # Conectar a Onboarding Flow Agent
    w['connections']['OpenAI Chat Onboarding'] = {
        "ai_languageModel": [[{"node": "Onboarding Flow Agent", "type": "ai_languageModel", "index": 0}]]
    }

    w['connections']['Memory Onboarding'] = {
        "ai_memory": [[{"node": "Onboarding Flow Agent", "type": "ai_memory", "index": 0}]]
    }

    print("   ✅ OpenAI Chat Onboarding creado y conectado")
    print("   ✅ Memory Onboarding creado y conectado")
else:
    print("   ℹ️  OpenAI Chat Onboarding ya existe")

# Guardar
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(w, f, indent=2, ensure_ascii=False)

print(f"\n✅ ARREGLOS APLICADOS")
print(f"Total nodos: {len(w['nodes'])}")
print(f"Total connections: {len(w['connections'])}")
