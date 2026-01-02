// User and Authentication Types
export interface User {
  id: string;
  email: string;
  username: string;
  displayName: string;
  avatar?: string;
  createdAt: string;
  lastLoginAt: string;
  preferences: UserPreferences;
  subscription: SubscriptionTier;
  stats: UserStats;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: NotificationSettings;
  privacy: PrivacySettings;
  accessibility: AccessibilitySettings;
}

export interface NotificationSettings {
  pushEnabled: boolean;
  emailEnabled: boolean;
  dailyReminders: boolean;
  achievementAlerts: boolean;
  weeklyProgress: boolean;
}

export interface PrivacySettings {
  dataCollection: 'full' | 'minimal' | 'anonymous';
  shareProgress: boolean;
  publicProfile: boolean;
  analyticsOptIn: boolean;
}

export interface AccessibilitySettings {
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  highContrast: boolean;
  reduceMotion: boolean;
  screenReader: boolean;
}

export interface UserStats {
  totalSessions: number;
  totalTimeSpent: number; // in minutes
  questionsAnswered: number;
  correctAnswers: number;
  currentStreak: number;
  longestStreak: number;
  level: number;
  experience: number;
  achievementsUnlocked: number;
}

export type SubscriptionTier = 'free' | 'supporter' | 'patron';

// Chat and Conversation Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  metadata?: MessageMetadata;
  reactions?: MessageReaction[];
}

export interface MessageMetadata {
  agentType?: AgentType;
  confidence?: number;
  sources?: string[];
  location?: MiddleEarthLocation;
  quizGenerated?: boolean;
  imageUrl?: string;
  audioUrl?: string;
}

export interface MessageReaction {
  type: 'like' | 'dislike' | 'helpful' | 'funny' | 'wise';
  userId: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  userId: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
  location: MiddleEarthLocation;
  tags: string[];
  isArchived: boolean;
}

// Agent Types
export type AgentType = 
  | 'grey_tutor' 
  | 'knowledge' 
  | 'assessment' 
  | 'journey' 
  | 'analytics' 
  | 'learning';

export interface Agent {
  type: AgentType;
  name: string;
  description: string;
  personality: string;
  capabilities: string[];
  isActive: boolean;
  healthStatus: 'healthy' | 'degraded' | 'offline';
  lastResponse?: string;
}

// Middle Earth and Learning Types
export interface MiddleEarthLocation {
  id: string;
  name: string;
  region: string;
  description: string;
  coordinates: {
    x: number;
    y: number;
  };
  isUnlocked: boolean;
  requiredLevel: number;
  backgroundImage: string;
  ambientSound?: string;
  characters: Character[];
  landmarks: Landmark[];
  quests: Quest[];
}

export interface Character {
  id: string;
  name: string;
  race: string;
  description: string;
  avatar: string;
  quotes: string[];
  location: string;
  isAvailable: boolean;
}

export interface Landmark {
  id: string;
  name: string;
  description: string;
  image: string;
  significance: string;
  relatedTopics: string[];
}

export interface Quest {
  id: string;
  title: string;
  description: string;
  type: 'knowledge' | 'exploration' | 'quiz' | 'discussion';
  difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  estimatedTime: number; // in minutes
  rewards: QuestReward[];
  prerequisites: string[];
  isCompleted: boolean;
  progress: number; // 0-100
}

export interface QuestReward {
  type: 'experience' | 'badge' | 'location' | 'character' | 'item';
  value: number | string;
  name: string;
  description: string;
}

// Quiz and Assessment Types
export interface Quiz {
  id: string;
  title: string;
  description: string;
  questions: QuizQuestion[];
  timeLimit?: number; // in seconds
  difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  category: string;
  location: string;
  createdAt: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  type: 'multiple_choice' | 'true_false' | 'short_answer' | 'essay';
  options?: string[];
  correctAnswer: string | string[];
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  points: number;
  timeLimit?: number;
  hints?: string[];
}

export interface QuizAttempt {
  id: string;
  quizId: string;
  userId: string;
  answers: QuizAnswer[];
  score: number;
  maxScore: number;
  timeSpent: number;
  completedAt: string;
  feedback: string;
}

export interface QuizAnswer {
  questionId: string;
  userAnswer: string | string[];
  isCorrect: boolean;
  timeSpent: number;
  hintsUsed: number;
}

// Achievement and Progress Types
export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: 'learning' | 'exploration' | 'social' | 'time' | 'special';
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  requirements: AchievementRequirement[];
  rewards: QuestReward[];
  unlockedAt?: string;
  progress: number; // 0-100
}

export interface AchievementRequirement {
  type: 'sessions' | 'questions' | 'streak' | 'time' | 'location' | 'quiz_score';
  target: number;
  current: number;
}

export interface LearningProgress {
  userId: string;
  totalExperience: number;
  level: number;
  currentLevelProgress: number; // 0-100
  unlockedLocations: string[];
  completedQuests: string[];
  achievements: string[];
  weeklyGoal: number;
  weeklyProgress: number;
  lastUpdated: string;
}

// API and Service Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  location?: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  message: string;
  agentType: AgentType;
  sessionId: string;
  suggestions?: string[];
  quiz?: Quiz;
  location?: MiddleEarthLocation;
  metadata?: MessageMetadata;
}

// Navigation Types
export type RootStackParamList = {
  Auth: undefined;
  MainTabs: undefined;
  Login: undefined;
  Register: undefined;
  Chat: {
    sessionId?: string;
    location?: string;
    quizTheme?: string;
    autoStartQuiz?: boolean;
  };
  Learning: { location?: string };
  Profile: undefined;
  Quiz: {
    quizId?: string;
    theme?: string;
    location?: string;
  };
  Achievement: { achievementId: string };
  Location: { locationId: string };
  RegionDetail: { regionName: string };
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

export type TabParamList = {
  ChatTab: undefined;
  LearningTab: undefined;
  MapTab: undefined;
  ProfileTab: undefined;
};

export type MainTabParamList = {
  Chat: undefined;
  Learning: undefined;
  Profile: undefined;
  Map: undefined;
};

// Redux State Types
export interface RootState {
  auth: AuthState;
  chat: ChatState;
  learning: LearningState;
  ui: UIState;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token: string | null;
}

export interface ChatState {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  isLoading: boolean;
  error: string | null;
  agents: Agent[];
}

export interface LearningState {
  locations: MiddleEarthLocation[];
  currentLocation: MiddleEarthLocation | null;
  progress: LearningProgress | null;
  achievements: Achievement[];
  quizzes: Quiz[];
  isLoading: boolean;
  error: string | null;
}

export interface UIState {
  theme: 'light' | 'dark' | 'auto';
  isOnline: boolean;
  notifications: Notification[];
  modals: {
    achievement: boolean;
    quiz: boolean;
    location: boolean;
  };
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  isRead: boolean;
  action?: {
    label: string;
    onPress: () => void;
  };
}

// Utility Types
export type LoadingState = 'idle' | 'loading' | 'succeeded' | 'failed';

export interface AsyncState<T> {
  data: T | null;
  status: LoadingState;
  error: string | null;
}
