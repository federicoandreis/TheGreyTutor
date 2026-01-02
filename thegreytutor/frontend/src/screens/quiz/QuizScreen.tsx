/**
 * QuizScreen - Dedicated screen for taking quizzes
 *
 * Features:
 * - Clean quiz-focused UI without chat distractions
 * - Support for multiple question types (multiple choice, true/false, open-ended)
 * - Progress indicators and score tracking
 * - Smooth animations for feedback
 * - Integration with backend quiz API
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  ActivityIndicator,
  Alert,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRoute, useNavigation, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import {
  startQuizSession,
  getNextQuestion,
  submitQuizAnswer,
  QuestionResponse,
  SubmitAnswerResponse,
} from '../../services/quizApi';
import { RootStackParamList } from '../../types';

type QuizScreenRouteProp = RouteProp<RootStackParamList, 'Quiz'>;
type QuizScreenNavigationProp = StackNavigationProp<RootStackParamList>;

interface NormalizedQuestion {
  text: string;
  options?: string[];
  question_type?: string;
}

const QuizScreen: React.FC = () => {
  const route = useRoute<QuizScreenRouteProp>();
  const navigation = useNavigation<QuizScreenNavigationProp>();

  // Quiz state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<NormalizedQuestion | null>(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(10); // Default, can be dynamic
  const [score, setScore] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [isCorrect, setIsCorrect] = useState(false);
  const [quizComplete, setQuizComplete] = useState(false);

  // Animation
  const feedbackOpacity = useState(new Animated.Value(0))[0];

  // Utility: Normalize question text
  const normalizeQuestionText = (text: any): string => {
    if (!text) return '';
    if (typeof text === 'string') return text;
    if (Array.isArray(text)) return text.join(' ');
    if (typeof text === 'object') {
      // This was causing duplication - if it's an object, stringify it
      return JSON.stringify(text);
    }
    return String(text);
  };

  // Utility: Normalize options
  const normalizeOptions = (options: any): string[] => {
    if (Array.isArray(options)) {
      return options as string[];
    }
    if (typeof options === 'string') {
      try {
        const parsed = JSON.parse(options);
        if (Array.isArray(parsed)) return parsed;
        if (typeof parsed === 'string') return [parsed];
      } catch {
        if (options.includes(',')) {
          return options.split(',').map((x: string) => x.trim());
        }
        return [options];
      }
    }
    return [];
  };

  // Initialize quiz session
  useEffect(() => {
    initializeQuiz();
  }, []);

  const initializeQuiz = async () => {
    setIsInitializing(true);
    try {
      // TODO: Get actual user ID from auth context
      const student_id = 'demo_user';
      const student_name = 'Adventurer';

      const session = await startQuizSession(student_id, student_name);
      setSessionId(session.session_id);

      const question = await getNextQuestion(session.session_id);
      loadQuestion(question, 1);
    } catch (error) {
      console.error('Failed to initialize quiz:', error);
      Alert.alert(
        'Quiz Error',
        'Failed to start quiz. Please try again.',
        [{ text: 'Go Back', onPress: () => navigation.goBack() }]
      );
    } finally {
      setIsInitializing(false);
    }
  };

  const loadQuestion = (questionData: QuestionResponse, number: number) => {
    console.log('[QuizScreen] Raw questionData received:', JSON.stringify(questionData, null, 2));

    // Backend returns { question: {...}, session_id, question_number }
    const rawQuestion = questionData.question || questionData;

    console.log('[QuizScreen] Extracted rawQuestion:', JSON.stringify(rawQuestion, null, 2));

    // Match ChatScreen's extraction logic - check question_text FIRST
    const questionText = rawQuestion.question_text || rawQuestion.text || rawQuestion.question || '';
    const questionOptions = rawQuestion.options || [];
    const questionType = rawQuestion.type || rawQuestion.question_type || 'open_ended';

    console.log('[QuizScreen] Extracted fields:', {
      questionText,
      questionOptions,
      questionType
    });

    const normalizedQuestion: NormalizedQuestion = {
      text: typeof questionText === 'string' ? questionText : String(questionText),
      options: Array.isArray(questionOptions) ? questionOptions : [],
      question_type: questionType,
    };

    setCurrentQuestion(normalizedQuestion);
    setQuestionNumber(number);
    setUserAnswer('');
    setSelectedOption(null);
    setShowFeedback(false);
  };

  const handleSubmitAnswer = async () => {
    if (!sessionId || !currentQuestion) return;

    // Validate answer
    if (currentQuestion.options && currentQuestion.options.length > 0) {
      if (selectedOption === null) {
        Alert.alert('Select an Answer', 'Please select an option before submitting.');
        return;
      }
    } else {
      if (!userAnswer.trim()) {
        Alert.alert('Enter an Answer', 'Please enter your answer before submitting.');
        return;
      }
    }

    setIsLoading(true);

    try {
      // Prepare answer to send
      let answerToSend = userAnswer.trim();
      if (currentQuestion.options && selectedOption !== null) {
        answerToSend = currentQuestion.options[selectedOption];
      }

      const response: SubmitAnswerResponse = await submitQuizAnswer(sessionId, answerToSend);

      // Show feedback
      setIsCorrect(response.correct || false);
      setFeedback(response.feedback?.explanation || (response.correct ? 'Correct!' : 'Incorrect.'));
      setShowFeedback(true);

      // Animate feedback
      Animated.sequence([
        Animated.timing(feedbackOpacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.delay(2000),
        Animated.timing(feedbackOpacity, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start(() => {
        setShowFeedback(false);
        proceedToNext(response);
      });

      if (response.correct) {
        setScore((s) => s + 1);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
      Alert.alert('Submission Error', 'Failed to submit answer. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const proceedToNext = (response: SubmitAnswerResponse) => {
    if (response.session_complete) {
      setQuizComplete(true);
    } else if (response.next_question) {
      // Wrap the raw question in a QuestionResponse structure
      const questionResponse: QuestionResponse = {
        question: response.next_question,
        session_id: sessionId || '',
        question_number: questionNumber + 1,
      };
      loadQuestion(questionResponse, questionNumber + 1);
    } else {
      // No next question but not complete - likely an error
      Alert.alert('Quiz Error', 'Something went wrong. Please restart the quiz.');
    }
  };

  const handleFinishQuiz = () => {
    navigation.goBack();
  };

  // Render loading state
  if (isInitializing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Preparing your quiz...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Render quiz complete state
  if (quizComplete) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.completeContainer}>
          <Ionicons name="trophy" size={80} color="#F59E0B" />
          <Text style={styles.completeTitle}>Quiz Complete!</Text>
          <Text style={styles.scoreText}>
            Your Score: {score} / {questionNumber}
          </Text>
          <Text style={styles.percentageText}>
            {((score / questionNumber) * 100).toFixed(0)}%
          </Text>
          <TouchableOpacity style={styles.finishButton} onPress={handleFinishQuiz}>
            <Text style={styles.finishButtonText}>Finish</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="close" size={28} color="#1C1C1E" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Quiz</Text>
        <View style={styles.scoreContainer}>
          <Ionicons name="star" size={20} color="#F59E0B" />
          <Text style={styles.scoreLabel}>{score}</Text>
        </View>
      </View>

      {/* Progress bar */}
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View
            style={[styles.progressFill, { width: `${(questionNumber / totalQuestions) * 100}%` }]}
          />
        </View>
        <Text style={styles.progressText}>
          Question {questionNumber} of {totalQuestions}
        </Text>
      </View>

      {/* Question */}
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.questionCard}>
          <Text style={styles.questionText}>{currentQuestion?.text}</Text>
        </View>

        {/* Answer options */}
        {currentQuestion?.options && currentQuestion.options.length > 0 ? (
          <View style={styles.optionsContainer}>
            {currentQuestion.options.map((option, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.optionButton,
                  selectedOption === index && styles.optionButtonSelected,
                ]}
                onPress={() => setSelectedOption(index)}
                disabled={isLoading}
              >
                <View style={styles.optionContent}>
                  <View
                    style={[
                      styles.radioButton,
                      selectedOption === index && styles.radioButtonSelected,
                    ]}
                  >
                    {selectedOption === index && (
                      <View style={styles.radioButtonInner} />
                    )}
                  </View>
                  <Text
                    style={[
                      styles.optionText,
                      selectedOption === index && styles.optionTextSelected,
                    ]}
                  >
                    {option}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        ) : (
          <View style={styles.textInputContainer}>
            <TextInput
              style={styles.textInput}
              value={userAnswer}
              onChangeText={setUserAnswer}
              placeholder="Type your answer here..."
              placeholderTextColor="#8E8E93"
              multiline
              editable={!isLoading}
            />
          </View>
        )}

        {/* Feedback overlay */}
        {showFeedback && (
          <Animated.View
            style={[
              styles.feedbackContainer,
              {
                opacity: feedbackOpacity,
                backgroundColor: isCorrect ? '#34C75944' : '#FF3B3044',
              },
            ]}
          >
            <Ionicons
              name={isCorrect ? 'checkmark-circle' : 'close-circle'}
              size={48}
              color={isCorrect ? '#34C759' : '#FF3B30'}
            />
            <Text style={styles.feedbackText}>{feedback}</Text>
          </Animated.View>
        )}
      </ScrollView>

      {/* Submit button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.submitButton, isLoading && styles.submitButtonDisabled]}
          onPress={handleSubmitAnswer}
          disabled={isLoading || showFeedback}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.submitButtonText}>Submit Answer</Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6D6D70',
  },
  completeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  completeTitle: {
    marginTop: 24,
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  scoreText: {
    marginTop: 16,
    fontSize: 20,
    color: '#3C3C43',
  },
  percentageText: {
    marginTop: 8,
    fontSize: 48,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  finishButton: {
    marginTop: 32,
    paddingHorizontal: 48,
    paddingVertical: 16,
    backgroundColor: '#007AFF',
    borderRadius: 12,
  },
  finishButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1C1C1E',
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  scoreLabel: {
    marginLeft: 4,
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  progressContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  progressText: {
    marginTop: 8,
    fontSize: 14,
    color: '#6D6D70',
    textAlign: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  questionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  questionText: {
    fontSize: 18,
    lineHeight: 28,
    color: '#1C1C1E',
    fontWeight: '500',
  },
  optionsContainer: {
    marginBottom: 24,
  },
  optionButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  optionButtonSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#007AFF08',
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  radioButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#C7C7CC',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  radioButtonSelected: {
    borderColor: '#007AFF',
  },
  radioButtonInner: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#007AFF',
  },
  optionText: {
    flex: 1,
    fontSize: 16,
    color: '#3C3C43',
  },
  optionTextSelected: {
    color: '#007AFF',
    fontWeight: '500',
  },
  textInputContainer: {
    marginBottom: 24,
  },
  textInput: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#1C1C1E',
    minHeight: 120,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  feedbackContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 16,
    padding: 24,
  },
  feedbackText: {
    marginTop: 16,
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  submitButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  submitButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

export default QuizScreen;
