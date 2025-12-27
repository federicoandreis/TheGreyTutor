import { User, ChatSession, ChatMessage, MiddleEarthLocation, Achievement, Quiz, LearningProgress } from '../types';

// Mock Users Database - Test Credentials Below
const mockUsers: User[] = [
  {
    id: '1',
    email: 'gandalf@middleearth.com',
    username: 'gandalf_grey',
    displayName: 'Gandalf the Grey',
    avatar: 'https://example.com/gandalf.jpg',
    createdAt: '2024-01-01T00:00:00Z',
    lastLoginAt: new Date().toISOString(),
    preferences: {
      theme: 'dark',
      language: 'en',
      notifications: {
        pushEnabled: true,
        emailEnabled: true,
        dailyReminders: true,
        achievementAlerts: true,
        weeklyProgress: true,
      },
      privacy: {
        dataCollection: 'full',
        shareProgress: true,
        publicProfile: false,
        analyticsOptIn: true,
      },
      accessibility: {
        fontSize: 'medium',
        highContrast: false,
        reduceMotion: false,
        screenReader: false,
      },
    },
    subscription: 'patron',
    stats: {
      totalSessions: 42,
      totalTimeSpent: 1260, // 21 hours
      questionsAnswered: 156,
      correctAnswers: 134,
      currentStreak: 7,
      longestStreak: 15,
      level: 8,
      experience: 2340,
      achievementsUnlocked: 12,
    },
  },
  // TEST USER - Use these credentials to login:
  // Email: test@example.com
  // Password: password123 (any password works in mock)
  {
    id: '2',
    email: 'test@example.com',
    username: 'test_user',
    displayName: 'Test User',
    avatar: 'https://example.com/test-avatar.jpg',
    createdAt: '2024-01-15T00:00:00Z',
    lastLoginAt: new Date().toISOString(),
    preferences: {
      theme: 'dark',
      language: 'en',
      notifications: {
        pushEnabled: true,
        emailEnabled: true,
        dailyReminders: true,
        achievementAlerts: true,
        weeklyProgress: true,
      },
      privacy: {
        dataCollection: 'full',
        shareProgress: true,
        publicProfile: false,
        analyticsOptIn: true,
      },
      accessibility: {
        fontSize: 'medium',
        highContrast: false,
        reduceMotion: false,
        screenReader: false,
      },
    },
    subscription: 'free',
    stats: {
      totalSessions: 5,
      totalTimeSpent: 120, // 2 hours
      questionsAnswered: 25,
      correctAnswers: 20,
      currentStreak: 3,
      longestStreak: 5,
      level: 2,
      experience: 450,
      achievementsUnlocked: 2,
    },
  },
];

// Mock Chat Messages
const mockMessages: ChatMessage[] = [
  {
    id: '1',
    content: 'Welcome to Middle Earth! I am Gandalf the Grey, and I shall be your guide on this learning journey.',
    role: 'assistant',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    metadata: {
      agentType: 'grey_tutor',
      confidence: 0.95,
      location: {
        id: 'shire',
        name: 'The Shire',
        region: 'Eriador',
        description: 'A peaceful land of rolling green hills',
        coordinates: { x: 100, y: 200 },
        isUnlocked: true,
        requiredLevel: 1,
        backgroundImage: 'shire.jpg',
        characters: [],
        landmarks: [],
        quests: [],
      },
    },
  },
  {
    id: '2',
    content: 'Hello Gandalf! I\'m excited to learn about Middle Earth.',
    role: 'user',
    timestamp: new Date(Date.now() - 3500000).toISOString(),
  },
  {
    id: '3',
    content: 'Excellent! Let us begin with the history of the Shire. What would you like to know about this peaceful land?',
    role: 'assistant',
    timestamp: new Date(Date.now() - 3400000).toISOString(),
    metadata: {
      agentType: 'knowledge',
      confidence: 0.92,
    },
  },
];

// Mock Chat Sessions
const mockChatSessions: ChatSession[] = [
  {
    id: 'session-1',
    userId: '1',
    title: 'Journey Through the Shire',
    messages: mockMessages,
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 3400000).toISOString(),
    location: {
      id: 'shire',
      name: 'The Shire',
      region: 'Eriador',
      description: 'A peaceful land of rolling green hills',
      coordinates: { x: 100, y: 200 },
      isUnlocked: true,
      requiredLevel: 1,
      backgroundImage: 'shire.jpg',
      characters: [],
      landmarks: [],
      quests: [],
    },
    tags: ['beginner', 'shire', 'history'],
    isArchived: false,
  },
];

// Mock Locations
const mockLocations: MiddleEarthLocation[] = [
  {
    id: 'shire',
    name: 'The Shire',
    region: 'Eriador',
    description: 'A peaceful land of rolling green hills where hobbits dwell',
    coordinates: { x: 100, y: 200 },
    isUnlocked: true,
    requiredLevel: 1,
    backgroundImage: 'shire.jpg',
    ambientSound: 'peaceful_countryside.mp3',
    characters: [
      {
        id: 'bilbo',
        name: 'Bilbo Baggins',
        race: 'Hobbit',
        description: 'A well-respected hobbit of Bag End',
        avatar: 'bilbo.jpg',
        quotes: ['I\'m going on an adventure!'],
        location: 'shire',
        isAvailable: true,
      },
    ],
    landmarks: [
      {
        id: 'bag_end',
        name: 'Bag End',
        description: 'The famous hobbit-hole of the Baggins family',
        image: 'bag_end.jpg',
        significance: 'Home of Bilbo and Frodo Baggins',
        relatedTopics: ['hobbits', 'baggins_family'],
      },
    ],
    quests: [
      {
        id: 'shire_history',
        title: 'Learn About Shire History',
        description: 'Discover the peaceful history of the Shire',
        type: 'knowledge',
        difficulty: 'easy',
        estimatedTime: 15,
        rewards: [
          {
            type: 'experience',
            value: 100,
            name: 'Shire Scholar',
            description: 'Gained knowledge about the Shire',
          },
        ],
        prerequisites: [],
        isCompleted: false,
        progress: 0,
      },
    ],
  },
  {
    id: 'rivendell',
    name: 'Rivendell',
    region: 'Eriador',
    description: 'The Last Homely House, refuge of the Elves',
    coordinates: { x: 200, y: 150 },
    isUnlocked: false,
    requiredLevel: 5,
    backgroundImage: 'rivendell.jpg',
    characters: [],
    landmarks: [],
    quests: [],
  },
];

// Mock Achievements
const mockAchievements: Achievement[] = [
  {
    id: 'first_steps',
    name: 'First Steps in Middle Earth',
    description: 'Complete your first conversation with Gandalf',
    icon: 'first_steps.png',
    category: 'learning',
    rarity: 'common',
    requirements: [
      {
        type: 'sessions',
        target: 1,
        current: 1,
      },
    ],
    rewards: [
      {
        type: 'experience',
        value: 50,
        name: 'Welcome Bonus',
        description: 'Experience for starting your journey',
      },
    ],
    unlockedAt: new Date(Date.now() - 86400000).toISOString(),
    progress: 100,
  },
];

// Mock Learning Progress
const mockLearningProgress: LearningProgress = {
  userId: '1',
  totalExperience: 2340,
  level: 8,
  currentLevelProgress: 34, // 34% to next level
  unlockedLocations: ['shire'],
  completedQuests: ['shire_history'],
  achievements: ['first_steps'],
  weeklyGoal: 300, // minutes
  weeklyProgress: 180, // minutes completed this week
  lastUpdated: new Date().toISOString(),
};

// Mock Database Service
export class MockDatabase {
  private static instance: MockDatabase;
  private users = mockUsers;
  private chatSessions = mockChatSessions;
  private locations = mockLocations;
  private achievements = mockAchievements;
  private learningProgress = mockLearningProgress;

  static getInstance(): MockDatabase {
    if (!MockDatabase.instance) {
      MockDatabase.instance = new MockDatabase();
    }
    return MockDatabase.instance;
  }

  // Auth Methods
  async login(email: string, password: string): Promise<{ user: User; token: string }> {
    await this.delay(1000); // Simulate network delay
    
    const user = this.users.find(u => u.email === email);
    if (!user) {
      throw new Error('Invalid credentials');
    }

    return {
      user: {
        ...user,
        lastLoginAt: new Date().toISOString(),
      },
      token: 'mock-jwt-token-' + Date.now(),
    };
  }

  async register(userData: { email: string; password: string; username: string; displayName: string }): Promise<{ user: User; token: string }> {
    await this.delay(1000);

    const newUser: User = {
      id: (this.users.length + 1).toString(),
      email: userData.email,
      username: userData.username,
      displayName: userData.displayName,
      createdAt: new Date().toISOString(),
      lastLoginAt: new Date().toISOString(),
      preferences: {
        theme: 'dark',
        language: 'en',
        notifications: {
          pushEnabled: true,
          emailEnabled: true,
          dailyReminders: true,
          achievementAlerts: true,
          weeklyProgress: true,
        },
        privacy: {
          dataCollection: 'full',
          shareProgress: true,
          publicProfile: false,
          analyticsOptIn: true,
        },
        accessibility: {
          fontSize: 'medium',
          highContrast: false,
          reduceMotion: false,
          screenReader: false,
        },
      },
      subscription: 'free',
      stats: {
        totalSessions: 0,
        totalTimeSpent: 0,
        questionsAnswered: 0,
        correctAnswers: 0,
        currentStreak: 0,
        longestStreak: 0,
        level: 1,
        experience: 0,
        achievementsUnlocked: 0,
      },
    };

    this.users.push(newUser);

    return {
      user: newUser,
      token: 'mock-jwt-token-' + Date.now(),
    };
  }

  // Chat Methods
  async sendMessage(messageData: { message: string; sessionId?: string; location?: string }): Promise<any> {
    await this.delay(800);

    // Generate mock response
    const responses = [
      "That's a fascinating question! Let me share some wisdom about Middle Earth...",
      "Indeed, the history of that place is rich with tales of courage and adventure.",
      "Ah, you show great curiosity! This reminds me of a story...",
      "Your understanding grows, young scholar. Let us delve deeper into this topic.",
      "Well spoken! The knowledge you seek is important for your journey.",
    ];

    const randomResponse = responses[Math.floor(Math.random() * responses.length)];

    return {
      response: {
        id: Date.now().toString(),
        message: randomResponse,
        metadata: {
          agentType: 'grey_tutor',
          confidence: 0.9 + Math.random() * 0.1,
        },
      },
    };
  }

  async getChatSessions(): Promise<ChatSession[]> {
    await this.delay(500);
    return [...this.chatSessions];
  }

  async createChatSession(sessionData: { title?: string; location?: string }): Promise<ChatSession> {
    await this.delay(600);

    const newSession: ChatSession = {
      id: 'session-' + Date.now(),
      userId: '1',
      title: sessionData.title || 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      location: this.locations.find(l => l.id === sessionData.location) || this.locations[0],
      tags: [],
      isArchived: false,
    };

    this.chatSessions.unshift(newSession);
    return newSession;
  }

  // Learning Methods
  async getLocations(): Promise<MiddleEarthLocation[]> {
    await this.delay(400);
    return [...this.locations];
  }

  async getLearningProgress(): Promise<LearningProgress> {
    await this.delay(300);
    return { ...this.learningProgress };
  }

  async getAchievements(): Promise<Achievement[]> {
    await this.delay(350);
    return [...this.achievements];
  }

  // Utility method to simulate network delay
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export const mockDB = MockDatabase.getInstance();
