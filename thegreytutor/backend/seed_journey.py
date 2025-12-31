"""
Seed script for Journey Agent data.

This script initializes the journey tables with Middle Earth regions,
paths, and achievements.
"""

import sys
import os

# Add parent directory to path so we can import from the backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import get_db_session
from src.database.models.journey import MiddleEarthRegion, JourneyPath, Achievement
from sqlalchemy import text


def check_existing_data(db):
    """Check if journey data already exists."""
    regions_count = db.query(MiddleEarthRegion).count()
    paths_count = db.query(JourneyPath).count()
    achievements_count = db.query(Achievement).count()

    print(f"Current data:")
    print(f"  Regions: {regions_count}")
    print(f"  Paths: {paths_count}")
    print(f"  Achievements: {achievements_count}")

    return regions_count > 0 or paths_count > 0 or achievements_count > 0


def seed_regions(db):
    """Seed Middle Earth regions."""
    print("\nSeeding regions...")

    regions_data = [
        {
            "name": "shire",
            "display_name": "The Shire",
            "description": "A peaceful land of rolling hills, where hobbits live in comfortable hobbit-holes. Begin your journey in this idyllic corner of Middle Earth.",
            "difficulty_level": "beginner",
            "map_coordinates": {"x": 150, "y": 200, "radius": 25},
            "prerequisite_regions": [],
            "knowledge_points_required": 0,
            "available_quiz_themes": ["hobbits", "farming", "pipe-weed", "genealogy"],
        },
        {
            "name": "bree",
            "display_name": "Bree",
            "description": "A bustling town where Men and Hobbits live side by side. The Prancing Pony inn is famous throughout the land.",
            "difficulty_level": "beginner",
            "map_coordinates": {"x": 250, "y": 220, "radius": 25},
            "prerequisite_regions": ["shire"],
            "knowledge_points_required": 50,
            "available_quiz_themes": ["men-of-bree", "inns", "rangers"],
        },
        {
            "name": "rivendell",
            "display_name": "Rivendell",
            "description": "The Last Homely House, refuge of the Elves. Here Elrond holds council and ancient lore is preserved.",
            "difficulty_level": "intermediate",
            "map_coordinates": {"x": 350, "y": 150, "radius": 30},
            "prerequisite_regions": ["bree"],
            "knowledge_points_required": 150,
            "available_quiz_themes": ["elves", "council-of-elrond", "elvish-lore", "healing"],
        },
        {
            "name": "moria",
            "display_name": "Mines of Moria",
            "description": "The ancient underground realm of the Dwarves, now fallen into darkness. Danger lurks in every shadow.",
            "difficulty_level": "advanced",
            "map_coordinates": {"x": 400, "y": 250, "radius": 30},
            "prerequisite_regions": ["rivendell"],
            "knowledge_points_required": 300,
            "available_quiz_themes": ["dwarves", "balrog", "gandalf", "ancient-kingdoms"],
        },
        {
            "name": "lothlorien",
            "display_name": "Lothlórien",
            "description": "The Golden Wood, realm of Lady Galadriel. Time flows differently in this enchanted forest.",
            "difficulty_level": "intermediate",
            "map_coordinates": {"x": 500, "y": 220, "radius": 30},
            "prerequisite_regions": ["moria"],
            "knowledge_points_required": 400,
            "available_quiz_themes": ["galadriel", "elven-magic", "gifts", "mirror-of-galadriel"],
        },
        {
            "name": "rohan",
            "display_name": "Rohan",
            "description": "Land of the horse-lords, where the Rohirrim ride across vast plains. Edoras stands proud upon its hill.",
            "difficulty_level": "intermediate",
            "map_coordinates": {"x": 450, "y": 350, "radius": 30},
            "prerequisite_regions": ["lothlorien"],
            "knowledge_points_required": 500,
            "available_quiz_themes": ["rohirrim", "horses", "theoden", "eowyn"],
        },
        {
            "name": "gondor",
            "display_name": "Gondor",
            "description": "The realm of Men, with Minas Tirith the White City standing guard against Mordor.",
            "difficulty_level": "advanced",
            "map_coordinates": {"x": 550, "y": 400, "radius": 35},
            "prerequisite_regions": ["rohan"],
            "knowledge_points_required": 700,
            "available_quiz_themes": ["stewards", "minas-tirith", "aragorn", "warfare"],
        },
        {
            "name": "mordor",
            "display_name": "Mordor",
            "description": "The Dark Lord's realm, where Mount Doom burns. Only the bravest dare enter this land of shadow.",
            "difficulty_level": "expert",
            "map_coordinates": {"x": 650, "y": 450, "radius": 40},
            "prerequisite_regions": ["gondor"],
            "knowledge_points_required": 1000,
            "available_quiz_themes": ["sauron", "ring", "sam-and-frodo", "mount-doom", "final-battle"],
        },
    ]

    for region_data in regions_data:
        existing = db.query(MiddleEarthRegion).filter_by(name=region_data["name"]).first()
        if not existing:
            region = MiddleEarthRegion(**region_data)
            db.add(region)
            print(f"  Added region: {region_data['display_name']}")
        else:
            print(f"  Region already exists: {region_data['display_name']}")

    db.commit()
    print(f"✓ Seeded {len(regions_data)} regions")


def seed_paths(db):
    """Seed journey paths."""
    print("\nSeeding journey paths...")

    paths_data = [
        {
            "name": "fellowship",
            "display_name": "The Fellowship of the Ring",
            "description": "Follow the path of the Fellowship from the Shire to the breaking at Amon Hen",
            "ordered_regions": ["shire", "bree", "rivendell", "moria", "lothlorien"],
            "narrative_theme": "The forming and journey of the Nine Companions",
            "estimated_duration_hours": 15,
            "path_color": "#4A90E2",
        },
        {
            "name": "two-towers",
            "display_name": "The Two Towers",
            "description": "The paths diverge as the Fellowship splits - follow both Aragorn and Frodo's journeys",
            "ordered_regions": ["lothlorien", "rohan", "gondor"],
            "narrative_theme": "The sundering of the Fellowship and the gathering storm",
            "estimated_duration_hours": 12,
            "path_color": "#E27D60",
        },
        {
            "name": "return-king",
            "display_name": "The Return of the King",
            "description": "The final march to victory and the destruction of the Ring",
            "ordered_regions": ["gondor", "mordor"],
            "narrative_theme": "The War of the Ring and the triumph of the West",
            "estimated_duration_hours": 10,
            "path_color": "#85CDCA",
        },
    ]

    for path_data in paths_data:
        existing = db.query(JourneyPath).filter_by(name=path_data["name"]).first()
        if not existing:
            path = JourneyPath(**path_data)
            db.add(path)
            print(f"  Added path: {path_data['display_name']}")
        else:
            print(f"  Path already exists: {path_data['display_name']}")

    db.commit()
    print(f"✓ Seeded {len(paths_data)} journey paths")


def seed_achievements(db):
    """Seed achievements."""
    print("\nSeeding achievements...")

    achievements_data = [
        {
            "code": "first_steps",
            "name": "First Steps",
            "description": "Complete your first quiz in the Shire",
            "category": "learning",
            "rarity": "common",
            "icon_name": "footsteps",
            "badge_color": "#95E1D3",
        },
        {
            "code": "shire_master",
            "name": "Master of the Shire",
            "description": "Complete all quizzes in the Shire with 90%+ average",
            "category": "mastery",
            "rarity": "rare",
            "icon_name": "home",
            "badge_color": "#FFD93D",
        },
        {
            "code": "fellowship_member",
            "name": "Member of the Fellowship",
            "description": "Unlock Rivendell and attend the Council of Elrond",
            "category": "exploration",
            "rarity": "uncommon",
            "icon_name": "people",
            "badge_color": "#6BCB77",
        },
        {
            "code": "knowledge_seeker",
            "name": "Knowledge Seeker",
            "description": "Earn 500 knowledge points",
            "category": "learning",
            "rarity": "uncommon",
            "icon_name": "book",
            "badge_color": "#4D96FF",
        },
        {
            "code": "moria_survivor",
            "name": "Survivor of Moria",
            "description": "Complete the Mines of Moria challenges",
            "category": "exploration",
            "rarity": "rare",
            "icon_name": "shield",
            "badge_color": "#FF6B6B",
        },
        {
            "code": "galadriel_gift",
            "name": "Galadriel's Gift",
            "description": "Receive a perfect score in Lothlórien",
            "category": "mastery",
            "rarity": "epic",
            "icon_name": "star",
            "badge_color": "#FFD700",
        },
        {
            "code": "rohirrim_rider",
            "name": "Rider of Rohan",
            "description": "Master all Rohan quiz themes",
            "category": "mastery",
            "rarity": "rare",
            "icon_name": "horse",
            "badge_color": "#8BC34A",
        },
        {
            "code": "white_city",
            "name": "Defender of the White City",
            "description": "Complete all Gondor challenges",
            "category": "exploration",
            "rarity": "epic",
            "icon_name": "castle",
            "badge_color": "#E8E8E8",
        },
        {
            "code": "ring_bearer",
            "name": "Bearer of the Ring",
            "description": "Reach Mordor",
            "category": "exploration",
            "rarity": "legendary",
            "icon_name": "ring",
            "badge_color": "#FFD700",
        },
        {
            "code": "ring_destroyer",
            "name": "Destroyer of the Ring",
            "description": "Complete all quizzes in Mordor and destroy the Ring",
            "category": "mastery",
            "rarity": "legendary",
            "icon_name": "flame",
            "badge_color": "#FF4444",
        },
        {
            "code": "scholar",
            "name": "Scholar of Middle Earth",
            "description": "Earn 1000 knowledge points",
            "category": "learning",
            "rarity": "epic",
            "icon_name": "school",
            "badge_color": "#9C27B0",
        },
        {
            "code": "grey_pilgrim",
            "name": "The Grey Pilgrim",
            "description": "Complete the entire journey from Shire to Mordor",
            "category": "special",
            "rarity": "legendary",
            "icon_name": "wizard",
            "badge_color": "#808080",
        },
    ]

    for achievement_data in achievements_data:
        existing = db.query(Achievement).filter_by(code=achievement_data["code"]).first()
        if not existing:
            achievement = Achievement(**achievement_data)
            db.add(achievement)
            print(f"  Added achievement: {achievement_data['name']}")
        else:
            print(f"  Achievement already exists: {achievement_data['name']}")

    db.commit()
    print(f"✓ Seeded {len(achievements_data)} achievements")


def main():
    """Main seeding function."""
    print("=== Journey Agent Data Seeding ===\n")

    with get_db_session() as db:
        # Check existing data
        has_data = check_existing_data(db)

        if has_data:
            response = input("\nData already exists. Do you want to re-seed? (y/n): ")
            if response.lower() != 'y':
                print("Seeding cancelled.")
                return

            # Clear existing data
            print("\nClearing existing data...")
            db.query(Achievement).delete()
            db.query(JourneyPath).delete()
            db.query(MiddleEarthRegion).delete()
            db.commit()
            print("✓ Cleared existing data")

        # Seed data
        seed_regions(db)
        seed_paths(db)
        seed_achievements(db)

        print("\n=== Seeding Complete! ===")
        print("\nYou can now:")
        print("  1. Start the backend server")
        print("  2. Open the app and navigate to the Journey Map")
        print("  3. See all 8 Middle Earth regions on the map!")


if __name__ == "__main__":
    main()
