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
import { mockQuizQuestions, QuizQuestion } from '../../services/mockQuizDatabase';

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

const ChatScreen: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [quizMode, setQuizMode] = useState(false);
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizScore, setQuizScore] = useState(0);
  const [quizFinished, setQuizFinished] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const startQuiz = () => {
    setQuizMode(true);
    setQuizIndex(0);
    setQuizScore(0);
    setQuizFinished(false);
    setMessages([
      {
        id: Date.now().toString(),
        content: 'Quiz mode activated! Answer the following questions:',
        role: 'assistant' as 'assistant',
        timestamp: new Date().toISOString(),
      },
      {
        id: (Date.now() + 1).toString(),
        content: mockQuizQuestions[0].question + (mockQuizQuestions[0].choices ? '\n' + mockQuizQuestions[0].choices.map((c, i) => `${i+1}. ${c}`).join('\n') : ''),
        role: 'assistant' as 'assistant',
        timestamp: new Date().toISOString(),
      },
    ]);
    setInputText('');
  };

  const stopQuiz = () => {
    setQuizMode(false);
    setQuizIndex(0);
    setQuizScore(0);
    setQuizFinished(false);
    setMessages([]);
    setInputText('');
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputText.trim(),
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = inputText.trim();
    setInputText('');
    setIsLoading(true);

    if (!quizMode) {
      try {
        const response = await fetch('http://localhost:8000/chat', {
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
        setMessages(prev => [...prev, aiResponse]);
      } catch (err) {
        setMessages(prev => [
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
    } else {
      // Quiz mode logic
      setTimeout(() => {
        if (quizFinished) {
          setIsLoading(false);
          return;
        }
        const currentQ = mockQuizQuestions[quizIndex];
        let correct = false;
        // Accept answer by number or text
        if (currentQ.choices) {
          const idx = parseInt(messageText.trim(), 10);
          if (!isNaN(idx) && currentQ.choices[idx-1]) {
            correct = currentQ.choices[idx-1].toLowerCase() === currentQ.answer.toLowerCase();
          } else {
            correct = messageText.trim().toLowerCase() === currentQ.answer.toLowerCase();
          }
        } else {
          correct = messageText.trim().toLowerCase() === currentQ.answer.toLowerCase();
        }
        let feedback = correct ? 'Correct!' : `Incorrect. The answer is: ${currentQ.answer}`;
        if (correct) setQuizScore(s => s + 1);
        let nextIndex = quizIndex + 1;
        let newMessages = [
          ...messages,
          {
            id: (Date.now() + 2).toString(),
            content: feedback,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          }
        ];
        if (nextIndex < mockQuizQuestions.length) {
          newMessages.push({
            id: (Date.now() + 3).toString(),
            content: mockQuizQuestions[nextIndex].question + (mockQuizQuestions[nextIndex].choices ? '\n' + mockQuizQuestions[nextIndex].choices.map((c, i) => `${i+1}. ${c}`).join('\n') : ''),
            role: 'assistant',
            timestamp: new Date().toISOString(),
          });
          setQuizIndex(nextIndex);
        } else {
          newMessages.push({
            id: (Date.now() + 4).toString(),
            content: `Quiz complete! Your score: ${quizScore + (correct ? 1 : 0)} / ${mockQuizQuestions.length}`,
            role: 'assistant',
            timestamp: new Date().toISOString(),
          });
          setQuizFinished(true);
        }
        setMessages(newMessages);
        setIsLoading(false);
      }, 800);
    }
  };

  const scrollToBottom = () => {
    flatListRef.current?.scrollToEnd({ animated: true });
  };

  const renderMessage = ({ item }: { item: ChatMessage }) => (
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
          {item.content}
        </Text>
        <Text style={styles.timestamp}>
          {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </View>
      {item.role === 'user' && <View style={styles.spacer} />}
    </View>
  );

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
          {messages.length === 0 ? (
            <View style={styles.welcomeContainer}>
              <Text style={styles.welcomeAvatar}>🧙‍♂️</Text>
              <Text style={styles.welcomeTitle}>Welcome to The Grey Tutor</Text>
              <Text style={styles.welcomeText}>
                I'm here to guide you through the vast lore of Middle Earth. Ask me anything about characters, places, events, or themes!
              </Text>
            </View>
          ) : (
            <FlatList
              ref={flatListRef}
              data={messages}
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
          )}

          {messages.length > 3 && (
            <TouchableOpacity style={styles.scrollButton} onPress={scrollToBottom}>
              <Ionicons name="chevron-down" size={20} color="#FFFFFF" />
            </TouchableOpacity>
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
