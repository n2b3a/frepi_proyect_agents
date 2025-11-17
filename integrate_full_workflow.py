#!/usr/bin/env python3
"""
Script para integrar el workflow completo de Frepi MVP2
Combina base (27 nodes) + nuevos sub-agents (32 nodes) = 59 nodes totales
"""

import json
import sys

print("🚀 Iniciando integración del workflow completo de Frepi MVP2...\n")

# Cargar workflow base
print("📂 Cargando workflow base...")
with open('Frepi_MVP2_Agent_Architecture.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

base_nodes_count = len(workflow['nodes'])
print(f"   ✓ Cargados {base_nodes_count} nodes base")

# Los 32 nodes adicionales generados por el agente
# (Shopping Flow Agent + tools, Vector Search Agent + tools, Preference Config Agent + tools,
#  Supplier Manager Agent + tools, Price Upload Agent + tools)

additional_nodes = [
    # === SHOPPING FLOW AGENT (8 nodes) ===
    {
        "parameters": {
            "name": "shopping_flow",
            "description": "Gerencia o fluxo completo de compra inteligente, comparação de preços e checkout.",
            "promptType": "define",
            "text": "={{ $json.query || $json.message }}",
            "options": {
                "systemMessage": "# 🛒 SHOPPING FLOW AGENT\n\n## RESPONSABILIDADE\nGerenciar todo o fluxo de compra do restaurante desde a lista até o checkout.\n\n## TOOLS DISPONÍVEIS\n\n### normalize_shopping_list\nNormaliza a lista de compras enviada pelo usuário.\nRecebe texto livre, retorna array estruturado de produtos.\n\n### calculate_savings\nCalcula economia total comparando preços de fornecedores.\n\n### segment_by_supplier\nSegmenta produtos por fornecedor para otimizar logística.\n\n### get_prices_for_product\nBusca preços de um produto específico em todos fornecedores.\n\n### calculate_best_price\nDetermina melhor preço considerando preferências do usuário.\n\n### execute_checkout\nExecuta o pedido confirmado pelo usuário.\n\n## FLUXO TÍPICO\n\n1. Receber lista de compra (texto livre)\n2. Normalizar lista → identificar produtos\n3. Para cada produto → buscar preços\n4. Calcular melhor preço (considerar preferências)\n5. Segmentar por fornecedor\n6. Apresentar resumo com economia\n7. Confirmar com usuário\n8. Executar checkout\n\n## REGRAS\n\n- Sempre mostrar comparação de preços\n- Destacar economia total em R$ e %\n- Agrupar por fornecedor para minimizar entregas\n- Respeitar preferências de marca quando possível\n- Avisar se produto não encontrado\n- Confirmar antes de executar pedido\n\n## OUTPUT\nPortuguês brasileiro, emojis: 🛒💰📊✅"
            }
        },
        "type": "@n8n/n8n-nodes-langchain.agentTool",
        "typeVersion": 2.2,
        "position": [-448, 1472],
        "id": "11111111-aaaa-bbbb-cccc-111111111111",
        "name": "Shopping Flow Agent"
    },
    {
        "parameters": {
            "model": {"__rl": True, "mode": "list", "value": "gpt-4o-mini"},
            "options": {"temperature": 0.2, "maxTokens": 2500}
        },
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "position": [-224, 1696],
        "id": "22222222-aaaa-bbbb-cccc-222222222222",
        "name": "OpenAI Chat Shopping",
        "credentials": {"openAiApi": {"id": "MdAepMtuPO5nFVI0", "name": "OpenAi account"}}
    },
    {
        "parameters": {
            "sessionIdType": "customKey",
            "sessionKey": "={{ $('Extraer Datos WhatsApp').first().json.phone_number }}",
            "contextWindowLength": 20
        },
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "position": [-224, 1920],
        "id": "33333333-aaaa-bbbb-cccc-333333333333",
        "name": "Memory Shopping"
    },
    {
        "parameters": {
            "description": "Normaliza lista de compras do usuário em formato estruturado.",
            "jsCode": "const input = $input.first().json;\nconst shoppingListText = input.shopping_list || input.message || input.text;\n\nif (!shoppingListText) {\n  return {\n    json: {\n      error: true,\n      message: \"Lista de compras não fornecida\"\n    }\n  };\n}\n\nconst lines = shoppingListText.split('\\n').filter(line => line.trim());\nconst items = [];\n\nfor (const line of lines) {\n  const match = line.match(/^\\s*(?:\\d+[\\.)\\-]?\\s+)?(.+?)(?:\\s+[-–]\\s+(\\d+(?:[\\.,]\\d+)?)\\s*(kg|g|l|ml|un|unidade|unidades|pacote|caixa)?)?\\s*$/i);\n  \n  if (match) {\n    const product = match[1].trim();\n    const quantity = match[2] ? parseFloat(match[2].replace(',', '.')) : 1;\n    const unit = match[3] || 'un';\n    \n    items.push({\n      product_name: product,\n      quantity: quantity,\n      unit: unit.toLowerCase(),\n      original_line: line.trim()\n    });\n  } else {\n    items.push({\n      product_name: line.trim(),\n      quantity: 1,\n      unit: 'un',\n      original_line: line.trim()\n    });\n  }\n}\n\nreturn {\n  json: {\n    success: true,\n    items_count: items.length,\n    normalized_items: items\n  }\n};"
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 1472],
        "id": "44444444-aaaa-bbbb-cccc-444444444444",
        "name": "normalize_shopping_list"
    },
    {
        "parameters": {
            "description": "Calcula economia total comparando preços entre fornecedores.",
            "jsCode": "const input = $input.first().json;\nconst priceComparisons = input.price_comparisons || [];\n\nif (!priceComparisons || priceComparisons.length === 0) {\n  return {\n    json: {\n      total_savings: 0,\n      savings_percent: 0,\n      message: \"Nenhuma comparação de preços disponível\"\n    }\n  };\n}\n\nlet totalBestPrice = 0;\nlet totalMaxPrice = 0;\n\nfor (const item of priceComparisons) {\n  const prices = item.prices || [];\n  if (prices.length > 0) {\n    const bestPrice = Math.min(...prices.map(p => p.price));\n    const maxPrice = Math.max(...prices.map(p => p.price));\n    const quantity = item.quantity || 1;\n    \n    totalBestPrice += bestPrice * quantity;\n    totalMaxPrice += maxPrice * quantity;\n  }\n}\n\nconst savings = totalMaxPrice - totalBestPrice;\nconst savingsPercent = totalMaxPrice > 0 ? (savings / totalMaxPrice) * 100 : 0;\n\nreturn {\n  json: {\n    total_best_price: totalBestPrice.toFixed(2),\n    total_max_price: totalMaxPrice.toFixed(2),\n    total_savings: savings.toFixed(2),\n    savings_percent: savingsPercent.toFixed(1),\n    formatted_message: `💰 Economia de R$ ${savings.toFixed(2)} (${savingsPercent.toFixed(1)}%)`\n  }\n};"
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 1696],
        "id": "55555555-aaaa-bbbb-cccc-555555555555",
        "name": "calculate_savings"
    },
    {
        "parameters": {
            "description": "Segmenta produtos por fornecedor para otimizar entregas.",
            "jsCode": "const input = $input.first().json;\nconst items = input.items || input.normalized_items || [];\n\nif (!items || items.length === 0) {\n  return {\n    json: {\n      error: true,\n      message: \"Nenhum item para segmentar\"\n    }\n  };\n}\n\nconst supplierGroups = {};\n\nfor (const item of items) {\n  const supplierId = item.best_supplier_id || item.supplier_id || 'unknown';\n  const supplierName = item.best_supplier_name || item.supplier_name || 'Fornecedor não identificado';\n  \n  if (!supplierGroups[supplierId]) {\n    supplierGroups[supplierId] = {\n      supplier_id: supplierId,\n      supplier_name: supplierName,\n      items: [],\n      total_value: 0,\n      items_count: 0\n    };\n  }\n  \n  supplierGroups[supplierId].items.push(item);\n  supplierGroups[supplierId].items_count++;\n  supplierGroups[supplierId].total_value += (item.best_price || item.price || 0) * (item.quantity || 1);\n}\n\nconst segments = Object.values(supplierGroups);\n\nreturn {\n  json: {\n    success: true,\n    suppliers_count: segments.length,\n    segments: segments,\n    summary: segments.map(s => `📦 ${s.supplier_name}: ${s.items_count} itens - R$ ${s.total_value.toFixed(2)}`).join('\\n')\n  }\n};"
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 1920],
        "id": "66666666-aaaa-bbbb-cccc-666666666666",
        "name": "segment_by_supplier"
    },
    {
        "parameters": {
            "description": "Busca preços de um produto em todos os fornecedores disponíveis.",
            "jsCode": "const input = $input.first().json;\nconst productName = input.product_name || input.product;\n\nif (!productName) {\n  return {\n    json: {\n      error: true,\n      message: \"Nome do produto não fornecido\"\n    }\n  };\n}\n\nconst credentials = await this.getCredentials('supabaseApi');\nconst supabaseUrl = credentials.host;\nconst supabaseKey = credentials.serviceRole;\n\ntry {\n  const response = await $request({\n    method: 'GET',\n    url: `${supabaseUrl}/rest/v1/suppliers_products`,\n    headers: {\n      'apikey': supabaseKey,\n      'Authorization': `Bearer ${supabaseKey}`,\n      'Content-Type': 'application/json'\n    },\n    qs: {\n      'select': 'price,supplier_id,suppliers(name,city),products(name,brand,format)',\n      'products.name': `ilike.%${productName}%`,\n      'order': 'price.asc'\n    },\n    json: true\n  });\n  \n  if (response && response.length > 0) {\n    const prices = response.map(item => ({\n      supplier_id: item.supplier_id,\n      supplier_name: item.suppliers?.name || 'N/A',\n      supplier_city: item.suppliers?.city || 'N/A',\n      product_name: item.products?.name || productName,\n      brand: item.products?.brand || 'N/A',\n      format: item.products?.format || 'N/A',\n      price: parseFloat(item.price)\n    }));\n    \n    return {\n      json: {\n        success: true,\n        product_name: productName,\n        prices_found: prices.length,\n        prices: prices,\n        best_price: prices[0]\n      }\n    };\n  } else {\n    return {\n      json: {\n        success: false,\n        product_name: productName,\n        prices_found: 0,\n        message: `Produto \"${productName}\" não encontrado no catálogo`\n      }\n    };\n  }\n} catch (error) {\n  return {\n    json: {\n      error: true,\n      message: `Erro ao buscar preços: ${error.message}`\n    }\n  };\n}"
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 2144],
        "id": "77777777-aaaa-bbbb-cccc-777777777777",
        "name": "get_prices_for_product"
    },
    {
        "parameters": {
            "description": "Determina melhor preço considerando preferências do usuário (marca, formato).",
            "jsCode": "const input = $input.first().json;\nconst prices = input.prices || [];\nconst userPreferences = input.user_preferences || {};\n\nif (!prices || prices.length === 0) {\n  return {\n    json: {\n      error: true,\n      message: \"Nenhum preço disponível para análise\"\n    }\n  };\n}\n\nconst preferredBrands = userPreferences.preferred_brands || [];\nconst preferredFormats = userPreferences.preferred_formats || [];\n\nlet bestOption = null;\nlet bestScore = -1;\n\nfor (const option of prices) {\n  let score = 0;\n  \n  const normalizedPrice = option.price;\n  const maxPrice = Math.max(...prices.map(p => p.price));\n  const priceScore = maxPrice > 0 ? (1 - (normalizedPrice / maxPrice)) * 100 : 0;\n  score += priceScore * 0.6;\n  \n  if (preferredBrands.length > 0 && preferredBrands.includes(option.brand)) {\n    score += 30;\n  }\n  \n  if (preferredFormats.length > 0 && preferredFormats.includes(option.format)) {\n    score += 10;\n  }\n  \n  if (score > bestScore) {\n    bestScore = score;\n    bestOption = option;\n  }\n}\n\nreturn {\n  json: {\n    success: true,\n    best_option: bestOption,\n    score: bestScore.toFixed(2),\n    all_options: prices.map(p => ({\n      ...p,\n      is_best: p.supplier_id === bestOption.supplier_id && p.price === bestOption.price\n    }))\n  }\n};"
        },
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.3,
        "position": [0, 2368],
        "id": "88888888-aaaa-bbbb-cccc-888888888888",
        "name": "calculate_best_price"
    }
]

print(f"\n📥 Agregando {len(additional_nodes)} nodes adicionales...")
workflow['nodes'].extend(additional_nodes)

print(f"   ✓ Total nodes ahora: {len(workflow['nodes'])}")

# Agregar conexiones para Shopping Flow Agent
print("\n🔗 Agregando conexiones...")

workflow['connections']['Shopping Flow Agent'] = {
    "ai_tool": [[{"node": "Customer Journey Agent", "type": "ai_tool", "index": 0}]]
}

workflow['connections']['OpenAI Chat Shopping'] = {
    "ai_languageModel": [[{"node": "Shopping Flow Agent", "type": "ai_languageModel", "index": 0}]]
}

workflow['connections']['Memory Shopping'] = {
    "ai_memory": [[{"node": "Shopping Flow Agent", "type": "ai_memory", "index": 0}]]
}

# Conectar tools al Shopping Flow Agent
for tool_name in ['normalize_shopping_list', 'calculate_savings', 'segment_by_supplier',
                   'get_prices_for_product', 'calculate_best_price']:
    workflow['connections'][tool_name] = {
        "ai_tool": [[{"node": "Shopping Flow Agent", "type": "ai_tool", "index": 0}]]
    }

print(f"   ✓ Total conexiones: {len(workflow['connections'])}")

# Guardar workflow actualizado
print("\n💾 Guardando workflow completo...")
with open('Frepi_MVP2_Agent_Architecture.json', 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("   ✓ Guardado en: Frepi_MVP2_Agent_Architecture.json")

print(f"\n✅ INTEGRACIÓN PARCIAL COMPLETADA!")
print(f"   📊 Nodes: {len(workflow['nodes'])} (objetivo: ~59)")
print(f"   🔗 Conexiones: {len(workflow['connections'])}")
print(f"\n⏭️  Faltan: Vector Search, Preference Config, Supplier Manager, Price Upload")
print(f"   (24 nodes más para completar)")
