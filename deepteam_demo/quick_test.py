"""Quick test script to verify demo suite works."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_settings
from config.logging_config import setup_logging
from demos.attack_demo import AttackDemo

def main():
    """Run a quick test."""
    settings = get_settings()
    logger, tracer = setup_logging(level="INFO", service_name="quick_test")
    
    logger.info("Running quick test...")
    
    # Create demo with minimal configuration
    demo = AttackDemo(settings=settings)
    
    # Get just the first app
    apps = demo.get_applications()
    if apps:
        logger.info(f"Testing with {apps[0].name}")
        results = demo.run(app=apps[0])
        logger.info("Quick test completed!")
        return results
    else:
        logger.error("No applications found")
        return None

if __name__ == "__main__":
    main()

