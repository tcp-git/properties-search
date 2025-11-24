import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
import argparse
import logging
import math
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("build_vectorstore")

# Asset type mapping (ใช้สำหรับสร้าง embedding text)
ASSET_TYPE_MAPPING = {
    "คอนโด": "อาคารชุด",
    "บ้าน": "บ้าน",
    "ทาวน์โฮม": "ทาวน์เฮ้าส์/ทาวน์โฮม",
    "อาคารพาณิชย์": "อาคารพาณิชย์"
}


POI_CONFIG = {
    
    # รัศมี 1 กม. คือระยะที่พอเดินหรือนั่งวินฯ ได้สะดวก ถ้าไกลกว่านี้คะแนนจะร่วงฮวบ (Exponential)
    "bts_station": {"radius": 1200, "weight": 1.2, "curve": "exponential"}, 
    "mrt": {"radius": 1200, "weight": 1.2, "curve": "exponential"},
    
    # สถานีรถไฟ/ขนส่ง สำคัญรองลงมาสำหรับคนเดินทางไกล
    "train_station": {"radius": 2000, "weight": 0.5, "curve": "linear"},
    "bus_station": {"radius": 2000, "weight": 0.5, "curve": "linear"},

    
    # ร้านสะดวกซื้อต้องใกล้จริง (เดินไปซื้อน้ำแข็งได้) 
    "convenience_store": {"radius": 1000, "weight": 0.5, "curve": "exponential"},
    # ตลาด/ซุปเปอร์ ขับรถไปได้ ให้รัศมีกว้างหน่อย
    "market": {"radius": 1500, "weight": 0.4, "curve": "linear"},
    "supermarket": {"radius": 2000, "weight": 0.5, "curve": "linear"}, 

    
    # ห้างสรรพสินค้าคือทุกอย่างของคนไทย (ตากแอร์/กินข้าว) ให้ Weight สูง
    "shopping_mall": {"radius": 3000, "weight": 0.9, "curve": "linear"},
    # คาเฟ่คือสถานที่ทำงานที่ 2 (Work from Anywhere)
    "cafe": {"radius": 1000, "weight": 0.4, "curve": "linear"},
    "restaurant": {"radius": 1000, "weight": 0.4, "curve": "linear"},
    "community_mall": {"radius": 2000, "weight": 0.6, "curve": "linear"}, 

    
    # โรงพยาบาลสำคัญมากสำหรับครอบครัวที่มีผู้สูงอายุ
    "hospital": {"radius": 3000, "weight": 0.7, "curve": "linear"},
    # สวนสาธารณะ/ยิม สำคัญสำหรับคนทำงานออฟฟิศ
    "park": {"radius": 3000, "weight": 0.6, "curve": "linear"},
    "gym": {"radius": 3500, "weight": 0.5, "curve": "linear"},
    "spa": {"radius":3000, "weight": 0.2, "curve": "linear"},

    
    # สัตวแพทย์ต้องอยู่ไม่ไกล เผื่อฉุกเฉิน
    "veterinary": {"radius": 2000, "weight": 0.5, "curve": "linear"},

    # (เฉพาะกลุ่มครอบครัว) 
    "school": {"radius": 3000, "weight": 0.5, "curve": "linear"},
    "university": {"radius": 3000, "weight": 0.3, "curve": "linear"},

    #  NICHE / RELAXATION 
    "river": {"radius": 1500, "weight": 0.4, "curve": "linear"}, 
    "beach": {"radius": 3000, "weight": 0.0, "curve": "linear"},
    "viewpoint": {"radius": 3000, "weight": 0.2, "curve": "linear"},
    "temple": {"radius": 1500, "weight": 0.1, "curve": "linear"}, 
    "museum": {"radius": 5000, "weight": 0.1, "curve": "linear"},
    "tourist_attraction": {"radius": 3000, "weight": 0.2, "curve": "linear"},
    "hotel": {"radius": 2000, "weight": 0.1, "curve": "linear"},
    "golf_course": {"radius": 5000, "weight": 0.2, "curve": "linear"},
}

def fix_asset_type(row):
    """Fix asset type text based on name and description"""
    name = str(row.get('name_th', '')).lower()
    desc = str(row.get('asset_details_description_th', '')).lower()
    eng_name = str(row.get('name_en', '')).lower()
    current_type = str(row.get('fixed_type', '')).strip() # ใช้ fixed_type จาก CSV ถ้ามี
    
    if current_type and current_type != 'nan':
        return current_type

    if any([
        "condominium" in eng_name or " คอนโด" in name or "คอนโด " in name or
        "อาคารชุด" in desc or "ห้องชุด" in desc
    ]):
        return ASSET_TYPE_MAPPING["คอนโด"]
    
    if any([
        "townhouse" in eng_name or "townhome" in eng_name or
        "ทาวน์เฮ้าส์" in name or "ทาวน์โฮม" in name
    ]):
        return ASSET_TYPE_MAPPING["ทาวน์โฮม"]

    if any([
        "commercial" in eng_name or "shophouse" in eng_name or
        "อาคารพาณิชย์" in name or "ตึกแถว" in name
    ]):
        return ASSET_TYPE_MAPPING["อาคารพาณิชย์"]

    return ASSET_TYPE_MAPPING["บ้าน"]

def compute_poi_percentiles(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    logger.info("Calculating POI percentiles...")
    percentiles_data = {}
    found_cols = 0
    for col_name in POI_CONFIG.keys():
        if col_name in df.columns:
            distances = df[col_name].dropna()
            distances = pd.to_numeric(distances, errors='coerce').dropna()
            
            if not distances.empty:
                percentiles_data[col_name] = {
                    "p10": np.percentile(distances, 10),
                    "p50": np.percentile(distances, 50),
                    "p90": np.percentile(distances, 90),
                }
                found_cols += 1
    
    logger.info(f" Calculated percentiles for {found_cols} POI types.")
    return percentiles_data

def compute_lifestyle_score(row: pd.Series, percentiles: Dict[str, Dict[str, float]]) -> float:
    total_score = 0
    for col_name, config in POI_CONFIG.items():
        if col_name in row and pd.notna(row[col_name]):
            try:
                distance = float(row[col_name])
            except:
                continue 
                
            radius = config["radius"]
            weight = config["weight"]
            
            if distance <= radius:
                score = 0
                if config.get("curve") == "exponential":
                    score = (1 - (distance / radius)) ** 2
                else:
                    score = 1 - (distance / radius)
                total_score += max(0, score * weight)
                
    total_weight = sum(c['weight'] for c in POI_CONFIG.values())
    if total_weight == 0: return 0.0
    
    normalized_score = min(10, (total_score / total_weight) * 10)
    return normalized_score

def extract_features(row: pd.Series) -> Dict[str, Any]:
    features = {}
    features['bedroom'] = row.get('asset_details_number_of_bedrooms', 'N/A')
    features['bathroom'] = row.get('asset_details_number_of_bathrooms', 'N/A')
    
    desc_th = str(row.get('asset_details_description_th', '')).lower()
    desc_en = str(row.get('asset_details_description_en', '')).lower()
    if "สัตว์เลี้ยง" in desc_th or "pet-friendly" in desc_en or "pet friendly" in desc_en:
        features['pet_friendly'] = True
    else:
        features['pet_friendly'] = False
        
    return features

def main(csv_path: str, db_path: str, model_name: str, collection_name: str):
    logger.info(f"🚀 Starting vector store build from: {csv_path}")
    logger.info(f"🗂️ Database path: {db_path}")
    logger.info(f"📦 Collection name: {collection_name}")

    # 1. Load Data
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return
    
    logger.info(f"Loaded {len(df)} rows from CSV.")
    
    # 2. Pre-processing
    logger.info("⚙️ Processing data and engineering features...")
    
    # Fix asset type (Text)
    df['asset_type_fixed'] = df.apply(fix_asset_type, axis=1)
    
    # Calculate Percentiles & Lifestyle Score
    percentiles = compute_poi_percentiles(df)
    df['lifestyle_score'] = df.apply(lambda row: compute_lifestyle_score(row, percentiles), axis=1)
    
    # Extract other features
    df_features = df.apply(extract_features, axis=1)
    df = pd.concat([df, pd.json_normalize(df_features)], axis=1)
    
    logger.info("✅ Processing complete.")

    # 3. Create Embeddings
    logger.info("Embedding text...")
    
    # สร้าง Text สำหรับ Semantic Search (รวม ID เข้าไปด้วยเผื่อช่วย)
    df['text_for_embedding'] = df['name_th'].fillna('') + " | " + \
                               df['asset_type_fixed'].fillna('') + " | " + \
                               df['asset_details_description_th'].fillna('')
    texts = df['text_for_embedding'].tolist()
    
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    logger.info("Generating embeddings... (This may take a while)")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    logger.info("✅ Embeddings generated.")

    # 4. Prepare Metadata (The Most Critical Part)
    logger.info("Preparing metadata for ChromaDB...")
    
    # ✅ [CRITICAL] กำหนด Columns ที่ต้องมีให้ครบ โดยเฉพาะ asset_type_id
    metadata_cols = [
            'id', 'name_th', 'name_en', 'asset_type_fixed', 'province_th', 'district_th',
            'asset_details_selling_price', 'location_latitude', 'location_longitude',
            'asset_details_description_th', 'asset_details_description_en',
            'bedroom', 'bathroom', 'pet_friendly', 
            'lifestyle_score',
            'asset_type_id' # <--- ต้องมีตัวนี้ 100%
        ]
    
    # เพิ่ม POI columns
    for poi_key in POI_CONFIG.keys():
        metadata_cols.append(poi_key)
        metadata_cols.append(f"{poi_key}_name")

    # กรองเอาเฉพาะที่มีจริงใน CSV
    final_metadata_cols = [col for col in metadata_cols if col in df.columns]
    
    logger.info(f"Saving {len(final_metadata_cols)} fields to metadata.")
    
    # สร้าง Metadata Dict
    df_metadata = df[final_metadata_cols].copy()
    
    # Handle NaN Values (ChromaDB ไม่รับ NaN)
    for col in df_metadata.columns:
        if df_metadata[col].dtype == 'object':
            df_metadata[col] = df_metadata[col].fillna('N/A')
        elif np.issubdtype(df_metadata[col].dtype, np.number):
            if col in POI_CONFIG: # Distance
                df_metadata[col] = df_metadata[col].fillna(99999.0)
            elif col == 'asset_type_id': # ID
                df_metadata[col] = df_metadata[col].fillna(0).astype(int) # แปลงเป็น int
            else:
                df_metadata[col] = df_metadata[col].fillna(0.0)

    metadatas = df_metadata.to_dict(orient="records")
    ids_list = df["id"].astype(str).tolist()

    # 5. Build ChromaDB
    logger.info(f"Setting up ChromaDB client at path: {db_path}")
    client = chromadb.PersistentClient(path=db_path)
    
    # Reset Collection
    try:
        if collection_name in [c.name for c in client.list_collections()]:
            logger.warning(f"Collection '{collection_name}' already exists. Deleting and rebuilding.")
            client.delete_collection(name=collection_name)
    except:
        pass
    
    collection = client.create_collection(name=collection_name)

    # Add to collection
    logger.info(f"Adding {len(df)} documents to collection...")
    
    BATCH_SIZE = 1000
    for i in range(0, len(ids_list), BATCH_SIZE):
        batch_ids = ids_list[i:i+BATCH_SIZE]
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_embeddings_list = embeddings[i:i+BATCH_SIZE].tolist()
        batch_metadatas = metadatas[i:i+BATCH_SIZE]
        
        try:
            collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings_list,
                documents=batch_texts,
                metadatas=batch_metadatas
            )
            logger.info(f"Added batch {i // BATCH_SIZE + 1} / {math.ceil(len(ids_list) / BATCH_SIZE)}")
        except Exception as e:
            logger.error(f"❌ Error adding batch {i // BATCH_SIZE + 1}: {e}")
            logger.error(f"Sample metadata: {json.dumps(batch_metadatas[0], indent=2, ensure_ascii=False)}")

    print("\n" + "="*80)
    print(f"✅ DONE: Vector DB built at {db_path}")
    print(f"   📊 Collection: {collection_name}")
    print(f"   📦 Documents: {collection.count()}")
    print("="*80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Chroma Vector Store")
    parser.add_argument("--csv_path", type=str, required=True)
    parser.add_argument("--db_path", type=str, default="npa_vectorstore")
    parser.add_argument("--model", type=str, default="thenlper/gte-large")
    parser.add_argument("--collection", type=str, default="npa_assets_v2")
    args = parser.parse_args()
    
    main(csv_path=args.csv_path, 
         db_path=args.db_path, 
         model_name=args.model, 
         collection_name=args.collection)