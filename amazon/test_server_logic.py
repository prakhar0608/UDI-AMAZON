
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config
from amazon_ads_app.profile_cache import load_cache, default_cache_path

def test_get_profiles():
    try:
        app_cfg = load_app_config()
        cache_path = default_cache_path(app_cfg.project_root)
        print(f"Checking cache at: {cache_path}")
        
        cached = load_cache(cache_path)
        if not cached:
            print("Cache is None.")
            return
            
        print(f"Found {len(cached.profiles)} profiles in cache.")
        if cached.profiles:
            p = cached.profiles[0]
            print(f"First profile dict: {p.__dict__}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_profiles()
