import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getMockAnswer } from '../../services/mockChatDatabase';
import {
  startQuizSession,
  getNextQuestion,
  submitQuizAnswer,
  getQuizSessionState,
  QuestionResponse,
  SubmitAnswerResponse
} from '../../services/quizApi';
import { BASE_URL } from '../../services/quizApi';

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  question?: any; // allow quiz question object for assistant messages
}

function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [quizMessages, setQuizMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [quizMode, setQuizMode] = useState(false);
  const [quizSessionId, setQuizSessionId] = useState<string | null>(null);
  const [quizScore, setQuizScore] = useState(0);
  const [quizFinished, setQuizFinished] = useState(false);
  const [currentQuizQuestion, setCurrentQuizQuestion] = useState<any | null>(null);
  const [quizQuestionNumber, setQuizQuestionNumber] = useState(0);
  const flatListRef = useRef<FlatList>(null);

  // Utility: Normalize question text (handles string, array, object)
  function normalizeQuestionText(text: any): string {
    if (!text) return '';
    if (typeof text === 'string') return text;
    if (Array.isArray(text)) return text.join('');
    if (typeof text === 'object') {
      // If it's a character map like {0: 'W', 1: 'h', ...}
      return Object.values(text).join('');
    }
    return String(text);
  }

  const startQuiz = async () => {
    // If already in quiz mode or an active quiz session exists, just switch mode and do not reset messages/state
    if (quizMode || quizSessionId) {
      setQuizMode(true);
      return;
    }
    setQuizMode(true);
    setQuizScore(0);
    setQuizFinished(false);
    setQuizMessages([
      {
        id: Date.now().toString(),
        content: 'Quiz mode activated! Gandalf will test your knowledge of Middle-earth. Answer the following questions:',
        role: 'assistant',
        timestamp: new Date().toISOString(),
      }
    ]);
    setInputText('');
    setIsLoading(true);
    try {
      // For now, use anonymous user
      const student_id = 'demo_user';
      const student_name = 'Adventurer';
      const session = await startQuizSession(student_id, student_name);
      setQuizSessionId(session.session_id);
      const q = await getNextQuestion(session.session_id);
      console.log('[QUIZ DEBUG] Raw API response:', JSON.stringify(q, null, 2));
      // API returns { question: {...}, session_id, question_number }
      // question contains: question_text, answer, options
      let rawQuestion = q.question || q;
      console.log('[QUIZ DEBUG] Extracted rawQuestion:', JSON.stringify(rawQuestion, null, 2));
      
      // Extract options - they come directly as an array from the LLM
      let options: string[] = [];
      if (rawQuestion.options) {
        if (Array.isArray(rawQuestion.options)) {
          options = rawQuestion.options;
        } else if (typeof rawQuestion.options === 'string') {
          try {
            const parsed = JSON.parse(rawQuestion.options);
            options = Array.isArray(parsed) ? parsed : [rawQuestion.options];
          } catch {
            options = rawQuestion.options.includes(',') 
              ? rawQuestion.options.split(',').map((x: string) => x.trim())
              : [rawQuestion.options];
          }
        }
      }
      console.log('[QUIZ DEBUG] Extracted options:', options);
      
      const normQuestion = {
        ...rawQuestion,
        text: rawQuestion.question_text || rawQuestion.text || rawQuestion.question || '',
        options: options,
      };
      console.log('[QUIZ DEBUG] Normalized question:', JSON.stringify(normQuestion, null, 2));
      setCurrentQuizQuestion(normQuestion);
      setQuizQuestionNumber(q.question_number || 1);
      setQuizMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          content: formatQuizQuestion(normQuestion, q.question_number || 1),
          role: 'assistant',
          timestamp: new Date().toISOString(),
          question: normQuestion // Attach normalized question object for option rendering
        } as any // type patch
      ]);
    } catch (err) {
      setQuizMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          content: 'Sorry, there was a problem starting the quiz. Please try again later.',
          role: 'assistant',
          timestamp: new Date().toISOString(),
        }
      ]);
      setQuizMode(false);
    } finally {
      setIsLoading(false);
    }
  };

  function cleanQuizQuestionText(text?: string): string {
    if (!text) return '';
    // Remove MC options like 'Is it: A) ...' or numbered lists
    let cleaned = text.replace(/Is it:.*?(A\)).*?(B\)).*?(C\)).*?(D\)).*?(\?|$)/i, '').trim();
    // Remove lines like '1. Option', '2. Option', etc.
    cleaned = cleaned.replace(/^[0-9]+\.\s.*$/gm, '').trim();
    // Remove lines like 'A) Option', etc.
    cleaned = cleaned.replace(/^[A-D]\)\s.*$/gm, '').trim();
    // Remove extra whitespace
    cleaned = cleaned.replace(/\n{2,}/g, '\n').trim();
    return cleaned;
  }

  function formatQuizQuestion(q: any, number?: number) {
    // Only show question text - options are rendered as buttons separately
    return `Q${number ? number : ''}: ${cleanQuizQuestionText(q.text || q.question)}`;
  }

  const stopQuiz = () => {
    setQuizMode(false);
    setQuizSessionId(null);
    setQuizFinished(false);
    setCurrentQuizQuestion(null);
    setQuizQuestionNumber(0);
    setInputText('');
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    if (quizMode) {
      // Quiz mode: send answer to quiz API
      setIsLoading(true);
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        content: inputText.trim(),
        role: 'user',
        timestamp: new Date().toISOString(),
      };
      setQuizMessages(prev => [...prev, userMessage]);
      setInputText('');
      try {
        // Accept answer by number or text
        let answerToSend = inputText.trim();
        if (currentQuizQuestion.options && Array.isArray(currentQuizQuestion.options)) {
          const idx = parseInt(answerToSend, 10);
          if (!isNaN(idx) && currentQuizQuestion.options[idx - 1]) {
            answerToSend = currentQuizQuestion.options[idx - 1];
          }
        }
        if (!quizSessionId) {
          setQuizMessages(prev => [
            ...prev,
            {
              id: (Date.now() + 10).toString(),
              content: 'Quiz session missing. Please restart the quiz.',
              role: 'assistant',
              timestamp: new Date().toISOString(),
            }
          ]);
          setIsLoading(false);
          return;
        }
        setAnsweredQuizMessageId(
          quizMessages.filter(m => m.role === 'assistant' && m.question && Array.isArray(m.question.options)).slice(-1)[0]?.id || null
        );
        const resp: SubmitAnswerResponse = await submitQuizAnswer(quizSessionId as string, answerToSend);
        let feedbackMsg = resp.feedback?.explanation || (resp.correct ? 'Correct!' : 'Incorrect.');
        setQuizMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 2).toString(),
            content: feedbackMsg,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          }
        ]);
        if (resp.session_complete) {
          setQuizMessages(prev => [
            ...prev,
            {
              id: (Date.now() + 3).toString(),
              content: `Quiz complete! Your score: ${quizScore + (resp.correct ? 1 : 0)}`,
              role: 'assistant',
              timestamp: new Date().toISOString(),
            }
          ]);
          setQuizFinished(true);
        } else if (resp.next_question) {
          // next_question contains: question_text, answer, options directly
          console.log('[QUIZ DEBUG] next_question response:', JSON.stringify(resp.next_question, null, 2));
          let rawQuestion = resp.next_question;
          
          // Extract options
          let options: string[] = [];
          if (rawQuestion.options) {
            if (Array.isArray(rawQuestion.options)) {
              options = rawQuestion.options;
            } else if (typeof rawQuestion.options === 'string') {
              try {
                const parsed = JSON.parse(rawQuestion.options);
                options = Array.isArray(parsed) ? parsed : [rawQuestion.options];
              } catch {
                options = rawQuestion.options.includes(',') 
                  ? rawQuestion.options.split(',').map((x: string) => x.trim())
                  : [rawQuestion.options];
              }
            }
          }
          console.log('[QUIZ DEBUG] next options:', options);
          
          const normQuestion = {
            ...rawQuestion,
            text: rawQuestion.question_text || rawQuestion.text || rawQuestion.question || '',
            options: options,
          };
          console.log('[QUIZ DEBUG] next normalized:', JSON.stringify(normQuestion, null, 2));
          setCurrentQuizQuestion(normQuestion);
          setQuizQuestionNumber(q => q + 1);
          setQuizMessages(prev => [
            ...prev,
            {
              id: (Date.now() + 4).toString(),
              content: formatQuizQuestion(normQuestion, quizQuestionNumber + 1),
              role: 'assistant',
              timestamp: new Date().toISOString(),
              question: normQuestion
            } as any
          ]);
          setAnsweredQuizMessageId(null);
          if (resp.correct) setQuizScore(s => s + 1);
        }
      } catch (err) {
        setQuizMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 5).toString(),
            content: 'Sorry, there was a problem submitting your answer. Please try again.',
            role: 'assistant',
            timestamp: new Date().toISOString(),
          }
        ]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // Chat mode: send message to backend
      setIsLoading(true);
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        content: inputText,
        role: 'user',
        timestamp: new Date().toISOString(),
      };
      setChatMessages(prev => [...prev, userMessage]);
      const messageText = inputText.trim();
      setInputText('');
      setIsLoading(true);

      try {
        const response = await fetch(`${BASE_URL}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: messageText,
            verbose: false,
            use_cache: true
          }),
        });
        const data = await response.json();
        const aiResponse: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: data.answer || "Gandalf is silent... (no answer received)",
          role: 'assistant',
          timestamp: new Date().toISOString(),
        };
        setChatMessages(prev => [...prev, aiResponse]);
      } catch (err) {
        setChatMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            content: "Sorry, there was a problem contacting Gandalf.",
            role: 'assistant',
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const scrollToBottom = () => {
    flatListRef.current?.scrollToEnd({ animated: true });
  };

  // Track which assistant message (by id) is the latest unanswered quiz question
  const [answeredQuizMessageId, setAnsweredQuizMessageId] = useState<string | null>(null);

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    // Get options array from question if it exists
    const questionOptions = item.question?.options;
    const hasOptions = Array.isArray(questionOptions) && questionOptions.length > 0;
    
    return (
      <View style={styles.messageWrapper}>
        {item.role === 'assistant' && (
          <View style={styles.avatarContainer}>
            <Text style={styles.avatar}>🧙‍♂️</Text>
          </View>
        )}
        <View style={[
          styles.messageContainer,
          item.role === 'user' ? styles.userMessage : styles.assistantMessage
        ]}>
          <Text style={[
            styles.messageText,
            item.role === 'user' ? styles.userMessageText : styles.assistantMessageText
          ]}>
            {/* Always show normalized question text if present for quiz messages */}
            {item.question
              ? normalizeQuestionText(item.question.text || item.question.question || item.question)
              : item.content}
          </Text>
          {/* Debug overlays removed for production. Uncomment for debugging only. */}
          {/*
          <View style={{ backgroundColor: 'rgba(255,255,0,0.15)', padding: 4, marginBottom: 4 }}>
            <Text style={{ fontSize: 11, color: '#444' }}>
              showQuizOptions: {showQuizOptions ? 'true' : 'false'} | quizMode: {quizMode ? 'true' : 'false'} | role: {item.role}
            </Text>
            <Text style={{ fontSize: 11, color: '#444' }}>
              question: {item.question ? 'yes' : 'no'} | options: {item.question && Array.isArray(item.question.options) ? item.question.options.length : 'none'}
            </Text>
            <Text style={{ fontSize: 11, color: '#444' }}>
              quizFinished: {quizFinished ? 'true' : 'false'} | answeredQuizMessageId: {answeredQuizMessageId} | item.id: {item.id}
            </Text>
          </View>
          {item.role === 'assistant' && item.question && (
            <View style={{ backgroundColor: 'rgba(0,0,0,0.04)', padding: 4, marginBottom: 4 }}>
              <Text style={{ fontSize: 10, color: '#333' }}>
                question: {JSON.stringify(item.question, null, 2)}
              </Text>
              {!Array.isArray(item.question.options) && (
                <Text style={{ fontSize: 10, color: 'red' }}>
                  WARNING: options is not an array. Actual type: {typeof item.question.options} Value: {JSON.stringify(item.question.options)}
                </Text>
              )}
            </View>
          )}
          */}
          {quizMode && hasOptions && !quizFinished ? (
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 }}>
              {questionOptions.map((opt: string, idx: number) => (
                <TouchableOpacity
                  key={idx}
                  style={{
                    backgroundColor: '#e0e7ef',
                    borderRadius: 14,
                    paddingHorizontal: 12,
                    paddingVertical: 6,
                    marginRight: 6,
                    marginBottom: 6,
                    borderWidth: 1,
                    borderColor: '#b5c1d8',
                  }}
                  onPress={async () => {
                    if (isLoading || answeredQuizMessageId === item.id) return;
                    setAnsweredQuizMessageId(item.id);
                    if (!quizSessionId) return;
                    setIsLoading(true);
                    const userMessage = {
                      id: Date.now().toString(),
                      content: opt,
                      role: 'user' as const,
                      timestamp: new Date().toISOString(),
                    };
                    setQuizMessages(prev => [...prev, userMessage]);
                    try {
                      console.log('[QUIZ DEBUG] Submitting answer:', opt, 'to session:', quizSessionId);
                      const resp: SubmitAnswerResponse = await submitQuizAnswer(quizSessionId as string, opt);
                      console.log('[QUIZ DEBUG] Submit response:', JSON.stringify(resp, null, 2));
                      let feedbackMsg = resp.feedback?.explanation || (resp.correct ? 'Correct!' : 'Incorrect.');
                      setQuizMessages(prev => [
                        ...prev,
                        {
                          id: (Date.now() + 2).toString(),
                          content: feedbackMsg,
                          role: 'assistant' as const,
                          timestamp: new Date().toISOString(),
                        }
                      ]);
                      if (resp.session_complete) {
                        setQuizMessages(prev => [
                          ...prev,
                          {
                            id: (Date.now() + 3).toString(),
                            content: `Quiz complete! Your score: ${quizScore + (resp.correct ? 1 : 0)}`,
                            role: 'assistant' as const,
                            timestamp: new Date().toISOString(),
                          }
                        ]);
                        setQuizFinished(true);
                      } else if (resp.next_question) {
                        // Normalize the next question
                        const rawQ = resp.next_question;
                        let opts: string[] = [];
                        if (rawQ.options) {
                          if (Array.isArray(rawQ.options)) {
                            opts = rawQ.options;
                          } else if (typeof rawQ.options === 'string') {
                            try {
                              const parsed = JSON.parse(rawQ.options);
                              opts = Array.isArray(parsed) ? parsed : [rawQ.options];
                            } catch {
                              opts = [rawQ.options];
                            }
                          }
                        }
                        const normQ = {
                          ...rawQ,
                          text: rawQ.question_text || rawQ.text || rawQ.question || '',
                          options: opts,
                        };
                        setCurrentQuizQuestion(normQ);
                        setQuizQuestionNumber(q => q + 1);
                        setQuizMessages(prev => [
                          ...prev,
                          {
                            id: (Date.now() + 4).toString(),
                            content: formatQuizQuestion(normQ, quizQuestionNumber + 1),
                            role: 'assistant' as const,
                            timestamp: new Date().toISOString(),
                            question: normQ
                          } as any
                        ]);
                        setAnsweredQuizMessageId(null);
                        if (resp.correct) setQuizScore(s => s + 1);
                      }
                    } catch (err) {
                      console.log('[QUIZ DEBUG] Submit error:', err);
                      setQuizMessages(prev => [
                        ...prev,
                        {
                          id: (Date.now() + 5).toString(),
                          content: 'Sorry, there was a problem submitting your answer. Please try again.',
                          role: 'assistant' as const,
                          timestamp: new Date().toISOString(),
                        }
                      ]);
                    } finally {
                      setIsLoading(false);
                    }
                  }}
                  disabled={isLoading || answeredQuizMessageId === item.id}
                >
                  <Text style={{ color: '#2a3a5e', fontWeight: '600', fontSize: 15 }}>{opt}</Text>
                </TouchableOpacity>
              ))}
            </View>
          ) : null}
          <Text style={styles.timestamp}>
            {item.timestamp && !isNaN(new Date(item.timestamp).getTime())
              ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              : '--:--'}
          </Text>
        </View>
        {item.role === 'user' && <View style={styles.spacer} />}
      </View>
    );
  };

  const currentMessages = quizMode ? quizMessages : chatMessages;

  return (
    <SafeAreaView style={styles.container}>
      {/* Toggle Chat/Quiz mode */}
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: 8 }}>
        <TouchableOpacity
          style={{
            backgroundColor: quizMode ? '#888' : '#007AFF',
            paddingHorizontal: 16,
            paddingVertical: 8,
            borderRadius: 20,
            marginRight: 8,
          }}
          onPress={stopQuiz}
          disabled={!quizMode}
        >
          <Text style={{ color: '#fff', fontWeight: 'bold' }}>Chat Mode</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={{
            backgroundColor: quizMode ? '#007AFF' : '#888',
            paddingHorizontal: 16,
            paddingVertical: 8,
            borderRadius: 20,
          }}
          onPress={startQuiz}
          disabled={quizMode}
        >
          <Text style={{ color: '#fff', fontWeight: 'bold' }}>Quiz Mode</Text>
        </TouchableOpacity>
      </View>
      <KeyboardAvoidingView 
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <View style={styles.messagesContainer}>
          {currentMessages.length === 0 ? (
            <View style={styles.welcomeContainer}>
              <Text style={styles.welcomeAvatar}>🧙‍♂️</Text>
              <Text style={styles.welcomeTitle}>Welcome to The Grey Tutor</Text>
              <Text style={styles.welcomeText}>
                I'm here to guide you through the vast lore of Middle Earth. Ask me anything about characters, places, events, or themes!
              </Text>
            </View>
          ) : (
            <>
              <FlatList
                ref={flatListRef}
                data={currentMessages}
                renderItem={renderMessage}
                keyExtractor={(item) => item.id}
                style={styles.messagesList}
                contentContainerStyle={styles.messagesContent}
                showsVerticalScrollIndicator={false}
                onContentSizeChange={() => {
                  setTimeout(() => {
                    flatListRef.current?.scrollToEnd({ animated: true });
                  }, 100);
                }}
              />
            </>
          )}

        </View>


<View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Ask me about Middle Earth..."
            placeholderTextColor="#8E8E93"
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
            onPress={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            <Text style={styles.sendButtonText}>
              {isLoading ? '...' : 'Send'}
            </Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  keyboardContainer: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
    position: 'relative',
  },
  welcomeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingBottom: 100,
  },
  welcomeAvatar: {
    fontSize: 80,
    marginBottom: 20,
  },
  welcomeTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1C1C1E',
    marginBottom: 16,
    textAlign: 'center',
  },
  welcomeText: {
    fontSize: 16,
    color: '#6D6D70',
    textAlign: 'center',
    lineHeight: 24,
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 20,
  },
  messageWrapper: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  avatarContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FF9500',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  avatar: {
    fontSize: 20,
  },
  spacer: {
    width: 48,
  },
  messageContainer: {
    flex: 1,
    maxWidth: '80%',
    padding: 12,
    borderRadius: 18,
  },
  userMessage: {
    backgroundColor: '#6C7B7F',
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  assistantMessage: {
    backgroundColor: '#E9E9EB',
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userMessageText: {
    color: '#FFFFFF',
  },
  assistantMessageText: {
    color: '#1C1C1E',
  },
  timestamp: {
    fontSize: 11,
    color: '#8E8E93',
    marginTop: 4,
    textAlign: 'right',
  },
  scrollButton: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: '#007AFF',
    borderRadius: 25,
    width: 50,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#F2F2F7',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginRight: 12,
    color: '#1C1C1E',
    fontSize: 16,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  sendButton: {
    backgroundColor: '#007AFF',
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 16,
  },
});

export default ChatScreen;
