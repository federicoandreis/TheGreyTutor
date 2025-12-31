# Journey Agent Integration Guide

This guide explains how to integrate the Journey Agent with other systems in TheGreyTutor application.

## Overview

The Journey Agent provides a gamified progression system through Middle Earth regions. It integrates with:
- **Quiz System**: Awards knowledge points and unlocks regions based on quiz performance
- **Chat System**: Gandalf can reference user's journey progress
- **Profile System**: Displays achievements and journey stats
- **Analytics System**: Tracks learning progress across regions

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│ Quiz System │────────▶│ Journey Agent│────────▶│ Neo4j Graph │
└─────────────┘         └──────────────┘         └─────────────┘
                               │
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │ (User State) │
                        └──────────────┘
```

## Database Schema

### Core Tables

**middle_earth_regions**
- Defines all available regions with metadata
- Contains map coordinates, difficulty levels, prerequisites
- Quiz themes available in each region

**journey_paths**
- Predefined learning paths through Middle Earth
- Ordered sequences of regions
- Narrative themes and estimated duration

**user_journey_state**
- Stores user's current position and progress
- Knowledge points earned
- Unlocked regions and completed regions
- Achievement badges

**user_journey_progress**
- Detailed progress per region
- Completion percentage
- Visit count and quiz history
- Mastered themes

**achievements**
- Achievement definitions
- Categories, rarity levels, requirements

## API Endpoints

### GET /api/journey/state
Get complete journey state for current user

**Response:**
```json
{
  "current_region": "shire",
  "current_path": "fellowship",
  "knowledge_points": 150,
  "unlocked_regions": ["shire", "bree"],
  "region_statuses": [
    {
      "name": "shire",
      "display_name": "The Shire",
      "difficulty_level": "beginner",
      "is_unlocked": true,
      "completion_percentage": 100,
      "map_coordinates": {"x": 100, "y": 150, "radius": 20}
    }
  ]
}
```

### POST /api/journey/travel
Travel to a new region

**Request:**
```json
{
  "region_name": "bree"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Gandalf's narration about arriving in Bree...",
  "region_data": {
    "name": "bree",
    "display_name": "Bree",
    "available_quiz_themes": ["inns", "rangers"]
  }
}
```

### POST /api/journey/complete-quiz
Record quiz completion and award progress

**Request:**
```json
{
  "region_name": "shire",
  "quiz_id": "quiz-123",
  "score": 0.8,
  "questions_answered": 10,
  "answers": [
    {
      "question_id": "q1",
      "is_correct": true,
      "concept_uri": "hobbit:bilbo_baggins"
    }
  ]
}
```

**Response:**
```json
{
  "knowledge_points_earned": 50,
  "new_completion_percentage": 75,
  "achievements_earned": [
    {
      "code": "first_quiz",
      "name": "First Steps",
      "description": "Completed your first quiz"
    }
  ],
  "regions_unlocked": ["bree"]
}
```

## Integrating with Quiz System

### Step 1: Quiz Completion Handler

When a user completes a quiz, call the Journey Agent:

```python
from src.agents.journey_agent import JourneyAgent
from database.connection import get_db_session

def on_quiz_complete(user_id: str, quiz_data: dict):
    """Handle quiz completion and update journey."""

    with get_db_session() as db:
        agent = JourneyAgent(db_session=db, neo4j_driver=None)

        # Process quiz completion
        result = agent.complete_quiz_in_region(
            user_id=user_id,
            region_name=quiz_data['region'],
            quiz_id=quiz_data['quiz_id'],
            score=quiz_data['score'],
            questions_answered=len(quiz_data['answers']),
            answers=quiz_data['answers']
        )

        # Notify user of rewards
        if result['achievements_earned']:
            notify_achievements(user_id, result['achievements_earned'])

        if result['regions_unlocked']:
            notify_new_regions(user_id, result['regions_unlocked'])

        return result
```

### Step 2: Map Quiz Themes to Regions

Quizzes should be tagged with their region:

```python
# In quiz generation
quiz_metadata = {
    'region': 'shire',  # Which region this quiz belongs to
    'theme': 'hobbits',  # Specific theme within region
    'difficulty': 'beginner'
}
```

### Step 3: Calculate Concept Mastery

Track which concepts the user has mastered:

```python
def process_quiz_answers(answers: list) -> dict:
    """Extract concept URIs and correctness from answers."""

    concept_tracking = {}

    for answer in answers:
        concept = answer['concept_uri']
        if concept not in concept_tracking:
            concept_tracking[concept] = {
                'total': 0,
                'correct': 0
            }

        concept_tracking[concept]['total'] += 1
        if answer['is_correct']:
            concept_tracking[concept]['correct'] += 1

    # Determine mastered concepts (e.g., 80% accuracy threshold)
    mastered = [
        concept for concept, stats in concept_tracking.items()
        if stats['correct'] / stats['total'] >= 0.8
    ]

    return {
        'concept_tracking': concept_tracking,
        'mastered_concepts': mastered
    }
```

## Frontend Integration

### Using Journey Store

```typescript
import { useJourneyStore, initializeJourney, completeQuiz } from '@/store/journeyStore';

function QuizCompletionScreen() {
  const { state, dispatch } = useJourneyStore();

  const handleQuizComplete = async (quizData) => {
    const result = await completeQuiz(dispatch, {
      region_name: 'shire',
      quiz_id: quizData.id,
      score: quizData.score / quizData.maxScore,
      questions_answered: quizData.totalQuestions,
      answers: quizData.answers
    });

    // Show rewards
    if (result?.knowledge_points_earned) {
      showRewardAnimation(result.knowledge_points_earned);
    }

    if (result?.achievements_earned?.length > 0) {
      showAchievements(result.achievements_earned);
    }
  };

  return (
    // Quiz UI with completion handler
  );
}
```

### Displaying Journey Progress in Profile

```typescript
import { useJourneyStore } from '@/store/journeyStore';

function ProfileScreen() {
  const { state } = useJourneyStore();

  if (!state.journeyState) return null;

  return (
    <View>
      <Text>Knowledge Points: {state.journeyState.knowledge_points}</Text>
      <Text>Regions Unlocked: {state.journeyState.unlocked_regions.length}</Text>
      <Text>Quizzes Taken: {state.journeyState.total_quizzes_taken}</Text>

      {/* Achievement badges */}
      <View>
        {state.journeyState.achievement_badges.map(badge => (
          <AchievementBadge key={badge.code} badge={badge} />
        ))}
      </View>
    </View>
  );
}
```

## Knowledge Points System

### Point Calculation

Knowledge points are awarded based on:
- **Quiz score**: Base points multiplied by percentage score
- **Difficulty multiplier**:
  - Beginner: 1.0x
  - Intermediate: 1.5x
  - Advanced: 2.0x
  - Expert: 2.5x
- **First-time bonus**: +50% for first quiz in a region
- **Perfect score bonus**: +25% for 100% score

**Example:**
```
Quiz with 10 questions, score 8/10, intermediate difficulty
Base points = 10 * 10 = 100
Score multiplier = 0.8
Difficulty multiplier = 1.5
Total = 100 * 0.8 * 1.5 = 120 points
```

### Unlock Requirements

Regions unlock when:
1. **Knowledge points threshold met** (e.g., 100 points for Bree)
2. **Prerequisite regions completed** (e.g., must finish Shire before Rivendell)
3. **Required themes mastered** (e.g., must master "hobbits" theme)

## Achievements System

### Achievement Categories

- **Learning**: Quiz-based achievements
- **Exploration**: Region unlocking achievements
- **Time**: Streak and consistency achievements
- **Mastery**: Theme mastery achievements
- **Special**: Unique narrative achievements

### Example Achievements

```python
{
    'code': 'first_steps',
    'name': 'First Steps',
    'category': 'learning',
    'rarity': 'common',
    'trigger': 'complete first quiz'
}

{
    'code': 'shire_master',
    'name': 'Master of the Shire',
    'category': 'mastery',
    'rarity': 'rare',
    'trigger': 'complete all Shire quizzes with 90%+ average'
}

{
    'code': 'fellowship_complete',
    'name': 'The Fellowship',
    'category': 'exploration',
    'rarity': 'epic',
    'trigger': 'unlock all regions in Fellowship path'
}
```

## Testing Integration

### Backend Tests

```python
def test_quiz_completion_awards_points():
    """Test that completing quiz awards knowledge points."""
    agent = JourneyAgent(db_session, neo4j_driver)

    initial_state = agent.get_journey_state(user_id)
    initial_points = initial_state['knowledge_points']

    result = agent.complete_quiz_in_region(
        user_id=user_id,
        region_name='shire',
        quiz_id='test-quiz',
        score=0.8,
        questions_answered=10,
        answers=[]
    )

    assert result['knowledge_points_earned'] > 0

    new_state = agent.get_journey_state(user_id)
    assert new_state['knowledge_points'] > initial_points
```

### Frontend Tests

```typescript
it('shows achievement notification after quiz', async () => {
  const mockQuizResult = {
    achievements_earned: [{
      code: 'first_quiz',
      name: 'First Steps'
    }]
  };

  (completeQuiz as jest.Mock).mockResolvedValue(mockQuizResult);

  const { getByText } = render(<QuizScreen />);

  // Complete quiz
  fireEvent.press(getByText('Submit Quiz'));

  await waitFor(() => {
    expect(getByText('Achievement Unlocked!')).toBeTruthy();
    expect(getByText('First Steps')).toBeTruthy();
  });
});
```

## Migration Guide

### Adding Journey to Existing Quiz Flow

1. **Update quiz completion endpoint:**
```python
@router.post("/quiz/complete")
async def complete_quiz(
    quiz_data: QuizCompletionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db_session)
):
    # Existing quiz processing
    quiz_result = process_quiz(quiz_data)

    # NEW: Update journey progress
    from src.agents.journey_agent import JourneyAgent
    agent = JourneyAgent(db_session=db, neo4j_driver=None)

    journey_result = agent.complete_quiz_in_region(
        user_id=user_id,
        region_name=quiz_data.region,
        quiz_id=quiz_data.quiz_id,
        score=quiz_result.score,
        questions_answered=len(quiz_data.answers),
        answers=quiz_data.answers
    )

    # Return combined result
    return {
        **quiz_result,
        'journey': journey_result
    }
```

2. **Update frontend quiz completion:**
```typescript
const handleQuizComplete = async () => {
  const result = await submitQuiz(quizData);

  // Existing logic
  showQuizResults(result);

  // NEW: Handle journey rewards
  if (result.journey) {
    if (result.journey.achievements_earned?.length > 0) {
      showAchievementModal(result.journey.achievements_earned);
    }

    if (result.journey.regions_unlocked?.length > 0) {
      showRegionUnlockedModal(result.journey.regions_unlocked);
    }
  }
};
```

## Best Practices

1. **Always initialize journey on user login:**
```typescript
useEffect(() => {
  if (isAuthenticated) {
    initializeJourney(dispatch);
  }
}, [isAuthenticated]);
```

2. **Handle offline state gracefully:**
```typescript
try {
  await completeQuiz(dispatch, quizData);
} catch (error) {
  // Queue for retry when online
  queueOfflineAction('complete-quiz', quizData);
}
```

3. **Show progress incrementally:**
```typescript
// Animate knowledge points count-up
animateValue(
  oldPoints,
  newPoints,
  1000  // 1 second animation
);
```

4. **Cache journey state:**
```typescript
// Store in AsyncStorage for offline access
await AsyncStorage.setItem(
  'journey-state',
  JSON.stringify(state.journeyState)
);
```

## Troubleshooting

### Common Issues

**Quiz completion not awarding points:**
- Check that `region_name` matches a valid region
- Verify user has traveled to the region first
- Check quiz answers include concept URIs

**Regions not unlocking:**
- Verify knowledge points threshold met
- Check prerequisite regions are completed
- Ensure required themes are mastered

**Frontend not showing updates:**
- Call `refreshJourneyState()` after quiz completion
- Check JourneyProvider wraps components
- Verify API authentication token is valid

## Future Enhancements

- **Real-time updates**: WebSocket notifications for achievements
- **Leaderboards**: Compare progress with other users
- **Daily quests**: Time-limited challenges in regions
- **Custom paths**: User-created learning journeys
- **Social features**: Share achievements, co-op quizzes

## Support

For questions or issues with Journey Agent integration:
- Backend: See [thegreytutor/backend/src/agents/journey_agent.py](../thegreytutor/backend/src/agents/journey_agent.py)
- Frontend: See [thegreytutor/frontend/src/store/journeyStore.ts](../thegreytutor/frontend/src/store/journeyStore.ts)
- API Docs: See [thegreytutor/backend/src/api/routes/journey.py](../thegreytutor/backend/src/api/routes/journey.py)
