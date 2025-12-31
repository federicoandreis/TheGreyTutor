-- Migration: Seed Journey Data
-- Date: 2025-12-30
-- Description: Seeds initial Middle Earth regions, paths, and achievements

-- ============================================================================
-- SEED MIDDLE EARTH REGIONS
-- ============================================================================

INSERT INTO middle_earth_regions (
    name,
    display_name,
    map_coordinates,
    difficulty_level,
    prerequisite_regions,
    knowledge_points_required,
    neo4j_community_tags,
    available_quiz_themes,
    lore_depth,
    description,
    gandalf_introduction,
    completion_reward
) VALUES

-- BEGINNER REGIONS
('the_shire', 'The Shire',
 '{"x": 150, "y": 200, "radius": 25}'::json,
 'beginner',
 '[]'::json,
 0,
 '["hobbits", "peaceful_folk", "shire_culture"]'::json,
 '["hobbit_culture", "shire_geography", "pipeweed", "hobbits"]'::json,
 'surface',
 'The peaceful homeland of the Hobbits, nestled in the green hills of Eriador. A land of rolling fields, cozy holes, and simple pleasures, where your journey into Middle Earth begins.',
 'Ah, the Shire! A fine place to begin, young scholar. Here in this peaceful land, you shall learn of the Halflings and their simple, yet profound ways. The Hobbits may seem unassuming, but their hearts are brave and their history rich.',
 'Hobbit Pipe'
),

('bree', 'Bree',
 '{"x": 220, "y": 180, "radius": 20}'::json,
 'beginner',
 '["the_shire"]'::json,
 50,
 '["humans", "trading", "crossroads"]'::json,
 '["human_culture", "trade_routes", "inns", "rangers"]'::json,
 'surface',
 'A bustling town at the crossroads of Middle Earth, where Big Folk and Little Folk live side by side. The Prancing Pony inn sees travelers from all corners of the world.',
 'Bree stands at the crossroads of Middle Earth, where the Great East Road meets the North Road. Many travelers pass through here - Rangers, Dwarves, and folk from distant lands. Keep your wits about you and your eyes open!',
 'Traveler''s Map'
),

-- INTERMEDIATE REGIONS
('rivendell', 'Rivendell',
 '{"x": 350, "y": 150, "radius": 30}'::json,
 'intermediate',
 '["bree"]'::json,
 150,
 '["elves", "noldor", "high_elves", "first_age"]'::json,
 '["elvish_lore", "first_age", "elrond", "rings_of_power"]'::json,
 'deep',
 'Imladris, the Last Homely House East of the Sea. Founded by Elrond Half-elven, this refuge of the Elves is a sanctuary of wisdom, beauty, and ancient lore.',
 'Rivendell, the house of Elrond! Here ancient wisdom dwells, and the lore of ages past is preserved. The Elves remember what others have forgotten. Listen well, for their knowledge runs deeper than the roots of mountains.',
 'Elven Cloak'
),

('lothlorien', 'Lothlórien',
 '{"x": 400, "y": 250, "radius": 30}'::json,
 'intermediate',
 '["rivendell"]'::json,
 250,
 '["elves", "galadriel", "golden_wood", "silvan_elves"]'::json,
 '["galadriel", "mirror_lore", "mallorn_trees", "elven_magic"]'::json,
 'deep',
 'The Golden Wood of the Galadhrim, realm of the Lady Galadriel and Lord Celeborn. Here time moves differently, and the ancient power of the Eldar still holds sway.',
 'The Golden Wood of the Galadhrim. Few who are not of Elven-kind have walked beneath these mallorn trees. The Lady Galadriel sees far and knows much. Tread carefully, for her gaze pierces through time itself.',
 'Phial of Galadriel'
),

('rohan', 'Rohan',
 '{"x": 300, "y": 350, "radius": 35}'::json,
 'intermediate',
 '["lothlorien"]'::json,
 300,
 '["rohirrim", "horsemen", "riders_of_rohan"]'::json,
 '["rohan_culture", "warfare", "horsemanship", "theoden"]'::json,
 'deep',
 'The Mark of the Riders, land of the horse-lords of Rohan. The Rohirrim are a proud and fierce people, masters of cavalry warfare and loyal allies of Gondor.',
 'The Mark of the Riders! Here dwell the horse-lords of Rohan, fierce and loyal. They are descendants of the Éothéod, who came from the North in ages past. Their cavalry is the finest in Middle Earth.',
 'Horn of Rohan'
),

-- ADVANCED REGIONS
('gondor', 'Gondor',
 '{"x": 450, "y": 400, "radius": 40}'::json,
 'advanced',
 '["rohan"]'::json,
 500,
 '["stewards", "numenor", "gondor_history", "dunedain"]'::json,
 '["gondor_history", "warfare", "numenor", "white_tree", "stewards"]'::json,
 'deep',
 'The greatest realm of Men in Middle Earth, founded by Isildur and Anárion. Though the line of kings has long been broken, the Stewards of Gondor maintain vigilance against the shadow in the East.',
 'Gondor, last bastion of the Dúnedain! The blood of Númenor flows yet in this ancient kingdom, though diminished. The White City of Minas Tirith stands as a bulwark against the darkness. Here you must understand the weight of history and the burden of heritage.',
 'White Tree Sapling'
),

('isengard', 'Isengard',
 '{"x": 250, "y": 300, "radius": 25}'::json,
 'advanced',
 '["rohan"]'::json,
 400,
 '["saruman", "wizards", "corruption", "orthanc"]'::json,
 '["saruman", "wizards", "corruption", "uruk_hai"]'::json,
 'expert',
 'The Ring of Isengard, with the tower of Orthanc at its center. Once a fortress of Gondor, it became the stronghold of Saruman the White - until his corruption and fall.',
 'Isengard, the Ring of Stone. Within stands Orthanc, the tower built by the ancient Númenóreans. Here Saruman the Wise dwelt - until wisdom turned to cunning, and cunning to treachery. A cautionary tale of pride and the lust for power.',
 'Palantír Shard'
),

-- EXPERT REGIONS
('mordor', 'Mordor',
 '{"x": 650, "y": 380, "radius": 45}'::json,
 'expert',
 '["gondor"]'::json,
 800,
 '["sauron", "dark_lands", "ring", "mount_doom"]'::json,
 '["sauron", "ring_lore", "dark_powers", "mount_doom", "eye_of_sauron"]'::json,
 'expert',
 'The Black Land, realm of the Dark Lord Sauron. A wasteland of ash and shadow, where the Eye watches ceaselessly from the Dark Tower of Barad-dûr. Here lies Mount Doom, where the One Ring was forged.',
 'Mordor. Even speaking the name fills me with dread. The Black Land, where the Dark Lord Sauron gathered his power. Here was forged the One Ring, and here alone can it be unmade. Steel yourself, for this knowledge tests the very soul.',
 'Mithril Ore'
),

('mirkwood', 'Mirkwood',
 '{"x": 500, "y": 200, "radius": 30}'::json,
 'advanced',
 '["rivendell"]'::json,
 350,
 '["spiders", "dark_forest", "woodland_realm"]'::json,
 '["mirkwood", "thranduil", "spiders", "forest_lore"]'::json,
 'deep',
 'Once known as Greenwood the Great, this vast forest fell under shadow. Giant spiders lurk in its depths, and the Woodland Realm of King Thranduil guards its northern reaches.',
 'Mirkwood, once Greenwood the Great! A shadow fell upon this forest, and darkness crept beneath its eaves. The Wood-elves of Thranduil''s realm keep watch, but evil things still crawl in the undergrowth. Enter with caution!',
 'Elven Bow'
),

('erebor', 'Erebor',
 '{"x": 600, "y": 100, "radius": 30}'::json,
 'advanced',
 '["rivendell"]'::json,
 450,
 '["dwarves", "lonely_mountain", "dragon", "thorin"]'::json,
 '["dwarves", "erebor_history", "dragon_lore", "thorin_oakenshield"]'::json,
 'deep',
 'The Lonely Mountain, greatest of the Dwarf-kingdoms of old. Once home to the legendary wealth of Thror, it was seized by the dragon Smaug and later reclaimed by Thorin Oakenshield.',
 'Erebor, the Lonely Mountain! Greatest of the Dwarf-kingdoms in the Elder Days. Here dwelt Thrór and his people, until Smaug the Terrible came from the North. The Arkenstone, Heart of the Mountain, lies in its halls - a jewel beyond price.',
 'Arkenstone Fragment'
);

-- ============================================================================
-- SEED JOURNEY PATHS
-- ============================================================================

INSERT INTO journey_paths (
    name,
    display_name,
    description,
    ordered_regions,
    narrative_theme,
    estimated_duration_hours,
    svg_path_data,
    path_color,
    unlock_condition
) VALUES

('fellowship_path', 'The Fellowship Path',
 'Follow the legendary journey of the Fellowship of the Ring, from the peaceful Shire to the fires of Mount Doom. Experience the full scope of the War of the Ring.',
 '["the_shire", "bree", "rivendell", "lothlorien", "rohan", "gondor", "mordor"]'::json,
 'fellowship',
 20,
 'M 150,200 L 220,180 L 350,150 L 400,250 L 300,350 L 450,400 L 650,380',
 '#4A90E2',
 '{"type": "default", "description": "Available from the start"}'::json
),

('northern_path', 'The Northern Path',
 'Explore the northern realms of Middle Earth, from the Shire through Bree to the refuge of Rivendell. A gentler introduction to the lore of Elves and Men.',
 '["the_shire", "bree", "rivendell"]'::json,
 'exploration',
 8,
 'M 150,200 L 220,180 L 350,150',
 '#2ECC71',
 '{"type": "default", "description": "Available from the start"}'::json
),

('elven_path', 'The Path of the Eldar',
 'Journey through the great Elven realms of Middle Earth. Learn the deep lore of the Firstborn, from Rivendell''s ancient library to Lothlórien''s golden woods.',
 '["rivendell", "lothlorien"]'::json,
 'elves',
 12,
 'M 350,150 L 400,250',
 '#9B59B6',
 '{"type": "knowledge", "knowledge_points_required": 150, "description": "Requires 150 knowledge points"}'::json
),

('kingdoms_of_men', 'Kingdoms of Men',
 'Trace the history and might of the kingdoms of Men, from the horse-lords of Rohan to the ancient towers of Gondor.',
 '["rohan", "gondor"]'::json,
 'human',
 10,
 'M 300,350 L 450,400',
 '#E74C3C',
 '{"type": "knowledge", "knowledge_points_required": 300, "description": "Requires 300 knowledge points"}'::json
),

('path_of_darkness', 'Path into Darkness',
 'Confront the corrupted and the evil: from Saruman''s treachery at Isengard to the very heart of Mordor. Only the most learned should walk this path.',
 '["isengard", "mordor"]'::json,
 'darkness',
 15,
 'M 250,300 L 650,380',
 '#34495E',
 '{"type": "knowledge", "knowledge_points_required": 600, "description": "Requires 600 knowledge points and mastery of Gondor"}'::json
),

('hobbit_path', 'There and Back Again',
 'Follow Bilbo''s journey from the Shire to the Lonely Mountain, encountering Dwarves, Dragons, and adventure.',
 '["the_shire", "rivendell", "mirkwood", "erebor"]'::json,
 'hobbit',
 14,
 'M 150,200 L 350,150 L 500,200 L 600,100',
 '#F39C12',
 '{"type": "achievement", "achievement_code": "first_steps", "description": "Unlocked after completing The Shire"}'::json
);

-- ============================================================================
-- SEED ACHIEVEMENTS
-- ============================================================================

INSERT INTO achievements (
    code,
    name,
    description,
    category,
    unlock_criteria,
    icon_name,
    badge_color,
    rarity
) VALUES

-- REGION ACHIEVEMENTS
('first_steps', 'First Steps',
 'Begin your journey in The Shire',
 'region',
 '{"type": "visit_region", "region": "the_shire"}'::json,
 'footsteps',
 '#8BC34A',
 'common'
),

('road_goes_ever_on', 'The Road Goes Ever On',
 'Visit all beginner regions (Shire and Bree)',
 'region',
 '{"type": "visit_all_difficulty", "difficulty": "beginner"}'::json,
 'road',
 '#4CAF50',
 'common'
),

('elvish_scholar', 'Elvish Scholar',
 'Complete all quizzes in Rivendell with 80% or higher',
 'region',
 '{"type": "complete_region", "region": "rivendell", "min_score": 0.8}'::json,
 'book',
 '#9C27B0',
 'rare'
),

('lady_of_light', 'Blessed by the Lady',
 'Complete Lothlórien with perfect scores',
 'region',
 '{"type": "complete_region", "region": "lothlorien", "min_score": 1.0}'::json,
 'star',
 '#FFD700',
 'epic'
),

('rider_of_rohan', 'Rider of Rohan',
 'Master the lore of the horse-lords',
 'region',
 '{"type": "complete_region", "region": "rohan", "min_score": 0.85}'::json,
 'horse',
 '#F57C00',
 'rare'
),

('steward_of_gondor', 'Steward of Gondor',
 'Complete Gondor and earn 500 knowledge points',
 'region',
 '{"type": "complex", "requirements": [{"type": "complete_region", "region": "gondor"}, {"type": "knowledge_points", "amount": 500}]}'::json,
 'crown',
 '#1976D2',
 'epic'
),

('into_mordor', 'One Does Not Simply Walk Into Mordor',
 'Enter Mordor (unlocking it is achievement enough!)',
 'region',
 '{"type": "unlock_region", "region": "mordor"}'::json,
 'eye',
 '#D32F2F',
 'legendary'
),

-- KNOWLEDGE ACHIEVEMENTS
('knowledge_seeker', 'Knowledge Seeker',
 'Earn 500 knowledge points',
 'knowledge',
 '{"type": "knowledge_points", "amount": 500}'::json,
 'scroll',
 '#FFC107',
 'rare'
),

('lore_master', 'Lore Master',
 'Earn 1000 knowledge points',
 'knowledge',
 '{"type": "knowledge_points", "amount": 1000}'::json,
 'tome',
 '#FF9800',
 'epic'
),

('scholar_of_arda', 'Scholar of Arda',
 'Earn 2000 knowledge points',
 'knowledge',
 '{"type": "knowledge_points", "amount": 2000}'::json,
 'library',
 '#FFD700',
 'legendary'
),

-- QUIZ ACHIEVEMENTS
('quick_learner', 'Quick Learner',
 'Complete 10 quizzes',
 'quiz',
 '{"type": "quiz_count", "count": 10}'::json,
 'lightning',
 '#4CAF50',
 'common'
),

('dedicated_student', 'Dedicated Student',
 'Complete 50 quizzes',
 'quiz',
 '{"type": "quiz_count", "count": 50}'::json,
 'study',
 '#2196F3',
 'rare'
),

('perfect_score', 'Perfectionist',
 'Achieve a perfect score on any quiz',
 'quiz',
 '{"type": "perfect_quiz"}'::json,
 'diamond',
 '#00BCD4',
 'rare'
),

-- SPECIAL/PATH ACHIEVEMENTS
('fellowship_complete', 'Fellowship Complete',
 'Finish the entire Fellowship Path from Shire to Mordor',
 'special',
 '{"type": "complete_path", "path": "fellowship_path"}'::json,
 'ring',
 '#FFD700',
 'legendary'
),

('there_and_back', 'There and Back Again',
 'Complete the Hobbit Path',
 'special',
 '{"type": "complete_path", "path": "hobbit_path"}'::json,
 'treasure',
 '#F39C12',
 'epic'
),

('friend_of_elves', 'Friend of the Elves',
 'Complete the Path of the Eldar',
 'special',
 '{"type": "complete_path", "path": "elven_path"}'::json,
 'leaf',
 '#9C27B0',
 'epic'
),

('shadow_walker', 'Walker in Shadow',
 'Complete the Path into Darkness',
 'special',
 '{"type": "complete_path", "path": "path_of_darkness"}'::json,
 'shadow',
 '#34495E',
 'legendary'
),

('map_master', 'Cartographer of Middle Earth',
 'Visit every region in Middle Earth',
 'special',
 '{"type": "visit_all_regions"}'::json,
 'map',
 '#FFD700',
 'legendary'
),

('completionist', 'True Scholar',
 'Achieve 100% completion in all regions',
 'special',
 '{"type": "complete_all_regions", "min_score": 1.0}'::json,
 'trophy',
 '#FFD700',
 'legendary'
);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify data was inserted
DO $$
DECLARE
    region_count INTEGER;
    path_count INTEGER;
    achievement_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO region_count FROM middle_earth_regions;
    SELECT COUNT(*) INTO path_count FROM journey_paths;
    SELECT COUNT(*) INTO achievement_count FROM achievements;

    RAISE NOTICE 'Journey data seeded successfully:';
    RAISE NOTICE '  - % regions', region_count;
    RAISE NOTICE '  - % paths', path_count;
    RAISE NOTICE '  - % achievements', achievement_count;
END $$;
