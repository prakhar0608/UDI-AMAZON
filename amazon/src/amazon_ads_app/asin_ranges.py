import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_asin_ranges(project_root: Path, profile_id: int) -> dict[str, dict[str, str]]:
    """Load ASIN to {Range, Subcat} mapping from CSV in the 'ranges' folder."""
    # Try multiple ways to find the ranges folder
    ranges_dir = project_root / "ranges"
    if not ranges_dir.exists():
        # Fallback to current working directory
        ranges_dir = Path(".").resolve() / "ranges"
    
    csv_path = ranges_dir / f"{profile_id}.csv"
    
    print(f">>> DEBUG: Loading ranges/subcat for profile {profile_id}")
    print(f">>> DEBUG: Checking path: {csv_path.absolute()}")
    
    mapping = {}
    if not csv_path.exists():
        print(f">>> DEBUG: File NOT FOUND: {csv_path.absolute()}")
        return mapping
        
    try:
        # Expected columns: Asins, Ranges, Subcat
        df = pd.read_csv(csv_path)
        print(f">>> DEBUG: Loaded CSV with {len(df)} rows. Columns: {df.columns.tolist()}")
        
        # Normalize column names
        df.columns = [c.strip().title() for c in df.columns]
        asin_col = "Asins" if "Asins" in df.columns else "Asin"
        range_col = "Ranges" if "Ranges" in df.columns else "Range"
        subcat_col = "Subcat" if "Subcat" in df.columns else "Subcat"
        
        if asin_col in df.columns:
            df = df.dropna(subset=[asin_col])
            for _, row in df.iterrows():
                asin = str(row[asin_col]).strip().upper()
                rng = str(row[range_col]).strip() if range_col in df.columns else "0"
                scat = str(row[subcat_col]).strip() if subcat_col in df.columns else "0"
                mapping[asin] = {"range": rng, "subcat": scat}
            print(f">>> DEBUG: Successfully built mapping with {len(mapping)} entries")
        else:
            print(f">>> DEBUG: ASIN COLUMN MISSING. Found: {df.columns.tolist()}")
    except Exception as e:
        print(f">>> DEBUG: ERROR LOADING CSV: {e}")
        
    return mapping

def apply_asin_ranges(df: pd.DataFrame, mapping: dict[str, dict[str, str]]) -> pd.DataFrame:
    """Add 'range' and 'subcat' columns to the dataframe based on 'asin' column."""
    if df.empty:
        return df
        
    if "asin" not in df.columns:
        print(">>> DEBUG: 'asin' column missing from dataframe, cannot apply mapping")
        return df
    
    # Ensure asin column is string and clean
    df["asin"] = df["asin"].astype(str).str.strip()
    
    if not mapping:
        print(">>> DEBUG: Mapping is empty, defaulting all to '0'")
        df["range"] = "0"
        df["subcat"] = "0"
        return df
    
    # Ensure lookups are case-insensitive
    search_col = df["asin"].str.upper()
    df["range"] = search_col.map(lambda x: mapping.get(x, {}).get("range", "0"))
    df["subcat"] = search_col.map(lambda x: mapping.get(x, {}).get("subcat", "0"))
    
    mapped_count = (df["range"] != "0").sum()
    print(f">>> DEBUG: Applied mapping. Mapped {mapped_count} out of {len(df)} rows.")
    return df
