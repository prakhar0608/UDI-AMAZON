
import sys
from pathlib import Path
import logging

# Add src to sys.path
sys.path.append(str(Path("src")))

from amazon_ads_app.config import load_app_config, ProfileConfig
from amazon_ads_app.profile_cache import load_cache, default_cache_path
from amazon_ads_app.pipeline import run_bulk_profiles

logging.basicConfig(level=logging.INFO)

def test_v3_errors():
    try:
        app_cfg = load_app_config()
        cache_path = default_cache_path(app_cfg.project_root)
        cached = load_cache(cache_path)
        
        if not cached or not cached.profiles:
            print("No profiles in cache.")
            return

        # Pick one profile to test
        target_profiles = [cached.profiles[0]]
        print(f"Testing for: {target_profiles[0].display_name}")

        results = run_bulk_profiles(
            app_cfg,
            target_profiles,
            report_type="spProducts",
            explicit_start_date="2026-05-12",
            explicit_end_date="2026-05-14"
        )
        print(f"Results: {len(results)}")
            
    except Exception as e:
        print(f"Captured Exception: {e}")

if __name__ == "__main__":
    test_v3_errors()
