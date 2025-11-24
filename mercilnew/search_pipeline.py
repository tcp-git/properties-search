import os
from dotenv import load_dotenv 
load_dotenv() 

import json
import logging
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

import requests
from sentence_transformers import SentenceTransformer
import chromadb

# ============ CONFIGURATION ============
VECTOR_DB_PATH = Path("npa_vectorstore") 
COLLECTION_NAME = "npa_assets_v2" 

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("⚠️ WARNING: OPENROUTER_API_KEY is not set.")

EMB_MODEL_NAME = "thenlper/gte-large"
TOP_K_RESULTS = 100 # กวาดมาเยอะๆ ก่อนกันหลุด
FINAL_TOP_N = 5 
LLM_MODEL = "openai/gpt-4o-mini" 

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("search_pipeline")

# ============ PROMPT ENGINEERING ============

ENHANCED_INTENT_DETECTION_PROMPT = """
คุณคือผู้เชี่ยวชาญด้านอสังหาริมทรัพย์ในไทย หน้าที่ของคุณคือวิเคราะห์คำค้นหา (Query) ที่ผู้ใช้ป้อนมา และแปลงมันเป็น JSON structure ที่ชัดเจน

(ไม่ต้องใส่ Query: "{query}" ตรงนี้)

จงวิเคราะห์ Query ที่ผู้ใช้ป้อนมา และตอบกลับเป็น JSON object เท่านั้น โดยมีโครงสร้างดังนี้:
{{
  "asset_types": ["ประเภท1", "ประเภท2", ...],
  "must_have": ["poi1", "poi2", ...],
  "nice_to_have": ["poi1", "poi2", ...],
  "avoid_poi": ["poi1", "poi2", ...],
  "pet_friendly": true/false/null,
  "price_range": {{
    "min": null_or_number,
    "max": null_or_number
  }}
}}

คำอธิบาย Field:
1.  "asset_types":
    * ประเภทของอสังหาฯ ที่ผู้ใช้มองหา (ระบุให้ชัดเจนที่สุด)
    * ตัวเลือก: ["คอนโด", "บ้านเดี่ยว", "บ้านแฝด", "ทาวน์โฮม", "อาคารพาณิชย์", "ที่ดิน"]
    * ถ้าบอกรวมๆ ว่า "บ้าน" ให้ใส่: ["บ้านเดี่ยว", "บ้านแฝด"]
    * ถ้าไม่ระบุ ให้เป็น: []
2.  "must_have":
    * POI ที่ผู้ใช้ "ต้องมี" (ใช้ POI key มาตรฐาน)
    * ถ้าไม่ระบุ ให้เป็น: []
3.  "nice_to_have":
    * POI ที่ผู้ใช้ "อยากได้" (ใช้ POI key มาตรฐาน)
    * ถ้าไม่ระบุ ให้เป็น: []
4.  "pet_friendly":
    * `true` (ถ้า "เลี้ยงสัตว์"), `false` (ถ้า "ไม่เลี้ยงสัตว์"), `null` (ถ้า "ไม่พูดถึง")
5.  "price_range":
    * ช่วงงบประมาณของผู้ใช้ (แปลงเป็นตัวเลขเท่านั้น)
    * "5 ล้าน" -> 5000000, "10m" -> 10000000, "2.5 ล." -> 2500000
    * "ไม่เกิน 5 ล้าน" -> {{ "min": null, "max": 5000000 }}
    * "3-5 ล้าน" -> {{ "min": 3000000, "max": 5000000 }}
    * ถ้าไม่พูดถึงราคา ให้เป็น: {{ "min": null, "max": null }}
6.  "avoid_poi":
    * POI ที่ผู้ใช้ "ไม่ต้องการ", "ไม่อยากอยู่ใกล้", "หนีห่าง" (ใช้ POI key มาตรฐาน)
    * เช่น "ไม่เอาใกล้โรงเรียน", "หนีความวุ่นวาย (market/mall)"
    * ถ้าไม่ระบุ ให้เป็น: []

[กฎ POI key มาตรฐาน]
* "bts", "รถไฟฟ้า", "บีทีเอส" -> "bts_station"
* "เซเว่น", "7-11", "ร้านสะดวกซื้อ" -> "convenience_store"
* "mrt", "ใต้ดิน" -> "mrt"
* "ห้าง", "สรรพสินค้า" -> "shopping_mall"
* "โรงเรียน", "มหาลัย" -> "school" (หรือ "university")
* "โรงพยาบาล", "คลินิก" -> "hospital"
* "สวน", "สวนสาธารณะ" -> "park"
* "ตลาด" -> "market"
* "ร้านอาหาร" -> "restaurant"
* "คาเฟ่" -> "cafe"

ตอบกลับเป็น JSON เท่านั้น:
"""

RAG_SYSTEM_PROMPT = """
คุณคือ "Mercil" ผู้ช่วย AI ด้านอสังหาฯ ที่เป็นมิตรและฉลาด
หน้าที่ของคุณคือ สรุปจุดเด่นและจุดด้อยของทรัพย์สิน โดยอิงตาม "ข้อมูล" และ "ผลการวิเคราะห์" ที่ผู้ใช้ป้อนมา

[ข้อบังคับ]
1.  **สรุปจากผลวิเคราะห์:** ห้ามคิดเองเด็ดขาด!
2.  **พูดความจริง:** ถ้าผลวิเคราะห์บอกว่า "ไม่ตรง" (Penalties) คุณต้องพูดถึงมัน
3.  **สั้นกระชับ:** สรุปไม่เกิน 2-3 ประโยค
4.  **เป็นธรรมชาติ:** เขียนเหมือนคุยกับเพื่อน
5.  **เน้นข้อมูล:** ถ้าในผลวิเคราะห์มี "ชื่อสถานที่" หรือ "ระยะทาง" (เช่น 500 ม.) ให้ระบุลงไปในคำสรุปด้วยเสมอ! 

[งานของคุณ]
จงเขียนคำอธิบายสั้นๆ โดยสรุปจาก "ผลการวิเคราะห์" ที่ผู้ใช้ป้อนมา
"""

def create_rag_user_content(query: str, meta: Dict, reasons: List[str], penalties: List[str]) -> str:
    return f"""
[ข้อมูลสำหรับวิเคราะห์]
User Query: {query}

Verified Data (ข้อมูลจริงของทรัพย์สิน):
- ชื่อ: {meta.get("name_th", "N/A")}
- ประเภท: {meta.get("asset_type_fixed", "N/A")} (ID: {meta.get('asset_type_id', 'N/A')})
- ราคา: {float(meta.get("asset_details_selling_price", 0)):,.0f} บาท
- รายละเอียด: {str(meta.get("asset_details_description_th", "N/A"))[:150]}

[ผลการวิเคราะห์ (ใช้ข้อมูลนี้เป็นหลัก)]
✅ จุดเด่นที่ตรงใจ (Reasons): {str(reasons) if reasons else "ไม่มี"}
⚠️ จุดที่ไม่ตรงใจ (Penalties): {str(penalties) if penalties else "ไม่มี"}
"""

# ✅ POI Config (Version 2025 Updated)
POI_CONFIG = {
    # === 🚆 TRANSPORTATION ===
    "bts_station": {"radius": 1200, "weight": 1.2, "curve": "exponential"}, 
    "mrt": {"radius": 1200, "weight": 1.2, "curve": "exponential"},
    "train_station": {"radius": 2000, "weight": 0.5, "curve": "linear"},
    "bus_station": {"radius": 2000, "weight": 0.5, "curve": "linear"},

    # === 🏪 CONVENIENCE ===
    "convenience_store": {"radius": 800, "weight": 0.5, "curve": "exponential"},
    "market": {"radius": 1500, "weight": 0.4, "curve": "linear"},
    "supermarket": {"radius": 2000, "weight": 0.5, "curve": "linear"},

    # === 🛍️ LIFESTYLE ===
    "shopping_mall": {"radius": 3000, "weight": 0.9, "curve": "linear"},
    "restaurant": {"radius": 1000, "weight": 0.4, "curve": "linear"},
    "cafe": {"radius": 1000, "weight": 0.4, "curve": "linear"},
    
    # === 🏥 HEALTH & WELLNESS ===
    "hospital": {"radius": 3000, "weight": 0.7, "curve": "linear"},
    "park": {"radius": 2000, "weight": 0.6, "curve": "linear"},
    "gym": {"radius": 1500, "weight": 0.5, "curve": "linear"},
    "spa": {"radius": 1500, "weight": 0.2, "curve": "linear"},

    # === 🐶 PET FRIENDLY ===
    "veterinary": {"radius": 2000, "weight": 0.5, "curve": "linear"},

    # === 🏫 OTHERS ===
    "school": {"radius": 3000, "weight": 0.5, "curve": "linear"},
    "university": {"radius": 3000, "weight": 0.3, "curve": "linear"},
    "river": {"radius": 1500, "weight": 0.4, "curve": "linear"}, 
    "beach": {"radius": 3000, "weight": 0.4, "curve": "linear"},
    "viewpoint": {"radius": 3000, "weight": 0.2, "curve": "linear"},
    "temple": {"radius": 1500, "weight": 0.1, "curve": "linear"},
    "museum": {"radius": 5000, "weight": 0.1, "curve": "linear"},
    "tourist_attraction": {"radius": 3000, "weight": 0.2, "curve": "linear"},
    "hotel": {"radius": 2000, "weight": 0.1, "curve": "linear"},
    "golf_course": {"radius": 5000, "weight": 0.2, "curve": "linear"},
}

# ✅ ASSET ID MAPPING (Corrected)
ASSET_ID_MAPPING = {
    "ทาวน์โฮม": [1],
    "ทาวน์เฮ้าส์": [1],
    "บ้านแฝด": [15], 
    "คอนโด": [3],
    "อาคารชุด": [3],
    "บ้านเดี่ยว": [4],
    "บ้าน": [4, 15], 
    "อาคารพาณิชย์": [5] 
}

# ============ SERVICE FUNCTIONS ============\

def get_embedding_model(model_name: str) -> SentenceTransformer:
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info("✅ Embedding model loaded.")
        return model
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
        raise

def get_chroma_collection(db_path: Path, collection_name: str) -> chromadb.Collection:
    if not db_path.exists():
        logger.error(f"❌ Vector DB path not found: {db_path}")
        raise FileNotFoundError(f"Vector DB path not found: {db_path}")
    logger.info(f"Connecting to ChromaDB at: {db_path}")
    client = chromadb.PersistentClient(path=str(db_path))
    try:
        collection = client.get_collection(name=collection_name)
        logger.info(f"✅ Connected to collection '{collection_name}' ({collection.count()} documents)")
        return collection
    except Exception as e:
        logger.error(f"❌ Failed to connect to collection '{collection_name}'.")
        raise e

def call_openrouter(system_prompt: str, user_content: str, model: str) -> str:
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set. Cannot call OpenRouter.")
        return "{}"
    try:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            data=json.dumps({"model": model, "messages": messages})
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return content
    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        return "{}"

# ============ SEARCH PIPELINE FUNCTIONS ============\

def enhanced_intent_detection(query: str) -> Dict[str, Any]:
    system_prompt = ENHANCED_INTENT_DETECTION_PROMPT
    user_content = query
    logger.info("Detecting intent...")
    raw_response = call_openrouter(system_prompt, user_content, LLM_MODEL)
    try:
        match = re.search(r'```json\n(.*?)\n```', raw_response, re.DOTALL)
        if match: json_str = match.group(1)
        else:
            json_str = raw_response.strip()
            if not json_str.startswith("{"):
                 start = json_str.find("{")
                 if start != -1: json_str = json_str[start:]
        intent_json = json.loads(json_str)
        validated_intent = {
                "asset_types": intent_json.get("asset_types", []),
                "must_have": intent_json.get("must_have", []),
                "nice_to_have": intent_json.get("nice_to_have", []),
                "avoid_poi": intent_json.get("avoid_poi", []),
                "pet_friendly": intent_json.get("pet_friendly", None),
                "price_range": intent_json.get("price_range", {"min": None, "max": None})
            }
        logger.info(f"Intent detected: {validated_intent}")
        return validated_intent
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from LLM response: {raw_response}")
        return { "asset_types": [], "must_have": [], "nice_to_have": [], "avoid_poi": [], "pet_friendly": None, "price_range": {"min": None, "max": None} }

def chroma_query(collection: chromadb.Collection, embed_model: SentenceTransformer, query: str, k: int, filters: Dict = {}) -> List[Dict[str, Any]]:
    logger.info("Performing semantic search...")
    query_embedding = embed_model.encode([query]).tolist()
    chroma_filter = None 
    if filters:
        filter_list = []
        if "max_price" in filters and filters["max_price"] > 0:
            filter_list.append({"asset_details_selling_price": {"$lte": filters["max_price"]}})
        if "province" in filters and isinstance(filters["province"], str):
            filter_list.append({"province_th": {"$eq": filters["province"]}})
        if filter_list:
            chroma_filter = {"$and": filter_list} if len(filter_list) > 1 else filter_list[0]
    try:
        results = collection.query(query_embeddings=query_embedding, n_results=k, where=chroma_filter, include=["metadatas", "distances"])
        processed_results = []
        if 'ids' not in results or not results['ids']:
            logger.warning("ChromaDB query returned no results.")
            return []
        for i, dist in enumerate(results['distances'][0]):
            meta = results['metadatas'][0][i]
            semantic_score = max(0, 1 - (dist / 2.0))
            processed_results.append({"id": results['ids'][0][i], "semantic_score": semantic_score, "metadata": meta})
        return processed_results
    except Exception as e:
        logger.error(f"❌ Error during Chroma query: {e}", exc_info=True)
        return []

def apply_filters(results: List[Dict], filters_cli: Dict, intent: Dict) -> List[Dict]:
    if not filters_cli and not intent.get("price_range"): return results 
    filtered_results = []
    price_range = intent.get("price_range", {})
    final_max_price = filters_cli.get("max_price") if filters_cli.get("max_price") is not None else price_range.get("max")
    final_min_price = price_range.get("min")
    final_province = filters_cli.get("province")
    for r in results:
        meta = r.get("metadata", {})
        keep = True
        price = float(meta.get("asset_details_selling_price", 0))
        if final_max_price is not None and price > final_max_price: keep = False
        if final_min_price is not None and price < final_min_price: keep = False
        if final_province:
            if final_province.replace("มหานคร", "").strip() not in meta.get("province_th", "N/A").replace("มหานคร", "").strip(): keep = False
        if keep: filtered_results.append(r)
    return filtered_results

def compute_intent_match_score(metadata: Dict[str, Any], intent: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """
    คำนวณคะแนน "ความตรงใจ" (Intent Score) โดยใช้ ID และ POI Config (Dynamic Radius)
    """
    score = 0.0
    reasons = [] 
    penalties = [] 
    
    # 1. Asset Type Matching (By ID)
    intent_types = intent.get("asset_types", [])
    if intent_types:
        asset_id = metadata.get("asset_type_id", 0)
        asset_type_name = metadata.get("asset_type_fixed", "N/A")
        
        accepted_ids = []
        for t in intent_types:
            accepted_ids.extend(ASSET_ID_MAPPING.get(t, []))
            
        if asset_id in accepted_ids:
            score += 1.0 
            reasons.append(f"ตรงประเภท ({asset_type_name})")
        else:
            score -= 10.0
            penalties.append(f"ผิดประเภท (ต้องการ {', '.join(intent_types)})")

    # 2. Pet-Friendly Matching
    intent_pet = intent.get("pet_friendly") 
    if intent_pet is True: 
        meta_pet_explicit = metadata.get("pet_friendly", False) 
        asset_id = metadata.get("asset_type_id", 0)
        vet_dist = metadata.get("veterinary", 99999) 
        intent_asset_types = intent.get("asset_types", []) 

        if meta_pet_explicit is True:
            score += 1.5; reasons.append("เลี้ยงสัตว์ได้ (ระบุในประกาศ)")
        else:
            if asset_id == 3: 
                if "คอนโด" in intent_asset_types:
                    score += 0.0; penalties.append("โปรดตรวจสอบกับนิติบุคคล (คอนโดส่วนใหญ่ห้าม)")
                else:
                    score -= 10.0; penalties.append("เลี้ยงสัตว์ไม่ได้ (คอนโดส่วนใหญ่ไม่อนุญาต)")
            elif asset_id == 4: 
                score += 1.0; reasons.append("เลี้ยงสัตว์ได้ (เป็นบ้านเดี่ยว)")
            elif asset_id in [1, 15, 5]: 
                score -= 0.5; penalties.append("ไม่ระบุว่าเลี้ยงสัตว์ได้ (แต่เป็นบ้านแนวราบ)")
            else: 
                score -= 10.0; penalties.append("ไม่เหมาะกับการเลี้ยงสัตว์ (ไม่ระบุ)")

        if vet_dist <= 2000: 
            score += 0.5; reasons.append(f"ใกล้ รพ.สัตว์ ({vet_dist:.0f} ม.)")
    
    elif intent_pet is False: 
         meta_pet_explicit = metadata.get("pet_friendly", False)
         if meta_pet_explicit is True:
            score -= 10.0; penalties.append("เลี้ยงสัตว์ได้ (ไม่ต้องการ)")

    # 3. Must-Have POI (Dynamic Radius)
    must_haves = intent.get("must_have", [])
    for poi_key in must_haves: 
        if poi_key in POI_CONFIG:
            distance = metadata.get(poi_key, 99999) 
            poi_name = metadata.get(f"{poi_key}_name", poi_key) 
            limit_radius = POI_CONFIG[poi_key].get("radius", 2000)
            
            if distance <= limit_radius: 
                score += 1.0
                reasons.append(f"ใกล้ {poi_name} ({distance:.0f} ม.)")
            else:
                score -= 1.0
                penalties.append(f"ไม่ใกล้ {poi_name} ({distance:.0f} ม.)")
                
    # 4. Avoid POI (Dynamic Radius)
    avoid_pois = intent.get("avoid_poi", [])
    for poi_key in avoid_pois:
        if poi_key in POI_CONFIG:
            distance = metadata.get(poi_key, 99999)
            poi_name = metadata.get(f"{poi_key}_name", poi_key)
            limit_radius = POI_CONFIG[poi_key].get("radius", 2000)

            if distance <= limit_radius:
                score -= 5.0
                penalties.append(f"อยู่ใกล้ {poi_name} ({distance:.0f} ม.) (ซึ่งคุณไม่ต้องการ)")
            else:
                score += 1.0
                reasons.append(f"ไกลจาก {poi_name} ({distance:.0f} ม.) ตามที่ขอ")
    
    return score, reasons, penalties

def apply_nice_to_have_boost(metadata: Dict[str, Any], intent: Dict[str, Any]) -> Tuple[float, List[str]]:
    nice_boost = 0.0
    nice_reasons = []
    nice_to_haves = intent.get("nice_to_have", [])
    for poi_key in nice_to_haves:
        if poi_key in POI_CONFIG:
            distance = metadata.get(poi_key, 99999)
            poi_name = metadata.get(f"{poi_key}_name", poi_key)
            limit_radius = POI_CONFIG[poi_key].get("radius", 2000)
            
            if distance <= limit_radius: 
                nice_boost += 0.25 
                nice_reasons.append(f"มี {poi_name} ใกล้ๆ ({distance:.0f} ม.)")
    return nice_boost, nice_reasons

def rag_explain_single_item(query: str, intent: Dict, result: Dict, reasons: List[str], penalties: List[str]) -> str:
    meta = result.get("metadata", {})
    system_prompt = RAG_SYSTEM_PROMPT
    user_content = create_rag_user_content(query, meta, reasons, penalties)
    try:
        explanation = call_openrouter(system_prompt, user_content, LLM_MODEL)
        if explanation.strip() == "{}":
            return "ไม่สามารถสร้างคำอธิบายได้"
        return explanation.strip().replace('"', '') 
    except Exception as e:
        logger.warning(f"Failed to generate RAG explanation: {e}")
        return "ไม่สามารถสร้างคำอธิบายได้"

def execute_search(query: str, filters: Dict, embed_model: SentenceTransformer, collection: chromadb.Collection) -> Dict[str, Any]:
    query_intent = enhanced_intent_detection(query)
    results = chroma_query(collection, embed_model, query, TOP_K_RESULTS, filters)
    if not results:
        return { "query": query, "intent_detected": query_intent, "results": [], "message": f"🤷 ไม่พบผลลัพธ์ที่ตรงกับคำค้นหา: \"{query}\"" }
    
    filtered_results = apply_filters(results, filters, query_intent)
    logger.info("Re-ranking results...")
    ranked_results = []
    for r in filtered_results:
        meta = r.get("metadata", {})
        lifestyle_score = float(meta.get("lifestyle_score", 0))
        intent_score, reasons, penalties = compute_intent_match_score(meta, query_intent)
        nice_boost, nice_reasons = apply_nice_to_have_boost(meta, query_intent)
        r["intent_reasons"] = reasons + nice_reasons
        r["intent_penalties"] = penalties
        final_score = ((intent_score * 0.7) + (r["semantic_score"] * 0.2) + (lifestyle_score * 0.05) + (nice_boost * 0.05))
        r["final_score"] = final_score
        r["intent_score"] = intent_score
        r["lifestyle_score"] = lifestyle_score 
        ranked_results.append(r)

    ranked_results.sort(key=lambda x: x["final_score"], reverse=True)
    
    # ✅ [QUALITY GATE] เพิ่มตรงนี้! ถ้าคะแนนต่ำเกินไป ตัดจบเลย
    if not ranked_results or ranked_results[0]['final_score'] < 0.35:
        return {
            "query": query,
            "intent_detected": query_intent,
            "results": [],
            "message": "🤔 ไม่พบทรัพย์สินที่ตรงกับความต้องการ หรือคำค้นหาอาจไม่ชัดเจนครับ (Low Matching Score)"
        }
    
    final_results_list = []
    for r in ranked_results[:FINAL_TOP_N]:
        meta = r.get("metadata", {})
        summary_text = rag_explain_single_item(query, query_intent, r, r.get('intent_reasons', []), r.get('intent_penalties', []))
        final_results_list.append({
            "id": r['id'],
            "final_score": round(r['final_score'], 2),
            "intent_score": round(r['intent_score'], 2),
            "summary": summary_text,
            "reasons": r.get('intent_reasons', []),
            "penalties": r.get('intent_penalties', []),
            "asset_details": {
                "name": meta.get('name_th', 'N/A'),
                "price": float(meta.get('asset_details_selling_price', 0)),
                "location": meta.get('province_th', 'N/A'), 
                "bedroom": meta.get('bedroom', 'N/A'),
                "bathroom": meta.get('bathroom', 'N/A'),
                "type_id": meta.get('asset_type_id', 'N/A') 
            }
        })
    
    return { "query": query, "intent_detected": query_intent, "results": final_results_list, "message": "Search completed successfully." }