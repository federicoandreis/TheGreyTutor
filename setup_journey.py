"""
Quick setup script to create journey tables and seed data.
Run this from the project root.
"""

from database.connection import engine, SessionLocal, Base
from database.models.journey import (
    MiddleEarthRegion,
    JourneyPath,
    Achievement,
    UserJourneyState,
    UserJourneyProgress
)

print("Creating journey tables...")
Base.metadata.create_all(bind=engine, tables=[
    MiddleEarthRegion.__table__,
    JourneyPath.__table__,
    Achievement.__table__,
    UserJourneyState.__table__,
    UserJourneyProgress.__table__,
])
print("[OK] Tables created")

# Now seed the data
session = SessionLocal()

print("\n=== Seeding Journey Data ===\n")

# Seed regions
print("Seeding regions...")
regions_data = [
    {
        "name": "shire",
        "display_name": "The Shire",
        "description": "A peaceful land of rolling hills, where hobbits live in comfortable hobbit-holes.",
        "difficulty_level": "beginner",
        "map_coordinates": {"x": 150, "y": 200, "radius": 25},
        "prerequisite_regions": [],
        "knowledge_points_required": 0,
        "available_quiz_themes": ["hobbits", "farming", "pipe-weed"],
    },
    {
        "name": "bree",
        "display_name": "Bree",
        "description": "A bustling town where Men and Hobbits live side by side.",
        "difficulty_level": "beginner",
        "map_coordinates": {"x": 250, "y": 220, "radius": 25},
        "prerequisite_regions": ["shire"],
        "knowledge_points_required": 50,
        "available_quiz_themes": ["men-of-bree", "inns", "rangers"],
    },
    {
        "name": "rivendell",
        "display_name": "Rivendell",
        "description": "The Last Homely House, refuge of the Elves.",
        "difficulty_level": "intermediate",
        "map_coordinates": {"x": 350, "y": 150, "radius": 30},
        "prerequisite_regions": ["bree"],
        "knowledge_points_required": 150,
        "available_quiz_themes": ["elves", "council-of-elrond", "healing"],
    },
    {
        "name": "moria",
        "display_name": "Mines of Moria",
        "description": "The ancient underground realm of the Dwarves.",
        "difficulty_level": "advanced",
        "map_coordinates": {"x": 400, "y": 250, "radius": 30},
        "prerequisite_regions": ["rivendell"],
        "knowledge_points_required": 300,
        "available_quiz_themes": ["dwarves", "balrog", "gandalf"],
    },
    {
        "name": "lothlorien",
        "display_name": "Lothlórien",
        "description": "The Golden Wood, realm of Lady Galadriel.",
        "difficulty_level": "intermediate",
        "map_coordinates": {"x": 500, "y": 220, "radius": 30},
        "prerequisite_regions": ["moria"],
        "knowledge_points_required": 400,
        "available_quiz_themes": ["galadriel", "elven-magic", "gifts"],
    },
    {
        "name": "rohan",
        "display_name": "Rohan",
        "description": "Land of the horse-lords.",
        "difficulty_level": "intermediate",
        "map_coordinates": {"x": 450, "y": 350, "radius": 30},
        "prerequisite_regions": ["lothlorien"],
        "knowledge_points_required": 500,
        "available_quiz_themes": ["rohirrim", "horses", "theoden"],
    },
    {
        "name": "gondor",
        "display_name": "Gondor",
        "description": "The realm of Men, with Minas Tirith the White City.",
        "difficulty_level": "advanced",
        "map_coordinates": {"x": 550, "y": 400, "radius": 35},
        "prerequisite_regions": ["rohan"],
        "knowledge_points_required": 700,
        "available_quiz_themes": ["stewards", "minas-tirith", "aragorn"],
    },
    {
        "name": "mordor",
        "display_name": "Mordor",
        "description": "The Dark Lord's realm, where Mount Doom burns.",
        "difficulty_level": "expert",
        "map_coordinates": {"x": 650, "y": 450, "radius": 40},
        "prerequisite_regions": ["gondor"],
        "knowledge_points_required": 1000,
        "available_quiz_themes": ["sauron", "ring", "mount-doom"],
    },
]

for region_data in regions_data:
    region = MiddleEarthRegion(**region_data)
    session.add(region)
    print(f"  Added: {region_data['display_name']}")

session.commit()
print(f"[OK] Seeded {len(regions_data)} regions\n")

# Seed paths
print("Seeding journey paths...")
paths_data = [
    {
        "name": "fellowship",
        "display_name": "The Fellowship of the Ring",
        "description": "Follow the path of the Fellowship",
        "ordered_regions": ["shire", "bree", "rivendell", "moria", "lothlorien"],
        "narrative_theme": "The forming of the Nine Companions",
        "estimated_duration_hours": 15,
        "path_color": "#4A90E2",
    },
    {
        "name": "two-towers",
        "display_name": "The Two Towers",
        "description": "The paths diverge",
        "ordered_regions": ["lothlorien", "rohan", "gondor"],
        "narrative_theme": "The sundering of the Fellowship",
        "estimated_duration_hours": 12,
        "path_color": "#E27D60",
    },
    {
        "name": "return-king",
        "display_name": "The Return of the King",
        "description": "The final march to victory",
        "ordered_regions": ["gondor", "mordor"],
        "narrative_theme": "The War of the Ring",
        "estimated_duration_hours": 10,
        "path_color": "#85CDCA",
    },
]

for path_data in paths_data:
    path = JourneyPath(**path_data)
    session.add(path)
    print(f"  Added: {path_data['display_name']}")

session.commit()
print(f"[OK] Seeded {len(paths_data)} paths\n")

# Seed achievements
print("Seeding achievements...")
achievements_data = [
    {
        "code": "first_steps",
        "name": "First Steps",
        "description": "Complete your first quiz",
        "category": "learning",
        "rarity": "common",
        "icon_name": "footsteps",
        "badge_color": "#95E1D3",
    },
    {
        "code": "shire_master",
        "name": "Master of the Shire",
        "description": "Complete all Shire quizzes",
        "category": "mastery",
        "rarity": "rare",
        "icon_name": "home",
        "badge_color": "#FFD93D",
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
]

for achievement_data in achievements_data:
    achievement = Achievement(**achievement_data)
    session.add(achievement)
    print(f"  Added: {achievement_data['name']}")

session.commit()
print(f"[OK] Seeded {len(achievements_data)} achievements\n")

session.close()

print("=== Setup Complete! ===")
print("\nYour Journey Map now has:")
print("  - 8 Middle Earth regions")
print("  - 3 journey paths")
print("  - 3 achievements")
print("\nReload your app and tap the Journey Map tab!")
