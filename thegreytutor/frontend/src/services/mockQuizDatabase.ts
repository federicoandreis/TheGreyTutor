// src/services/mockQuizDatabase.ts
// Simple Middle Earth quiz questions for demo

export interface QuizQuestion {
  question: string;
  answer: string;
  choices?: string[]; // Optional for multiple choice
}

export const mockQuizQuestions: QuizQuestion[] = [
  {
    question: 'Who is the author of The Lord of the Rings?',
    answer: 'J.R.R. Tolkien',
    choices: ['J.K. Rowling', 'J.R.R. Tolkien', 'George R.R. Martin', 'C.S. Lewis']
  },
  {
    question: 'What is the name of Frodo’s loyal friend who travels with him to Mordor?',
    answer: 'Samwise Gamgee',
    choices: ['Peregrin Took', 'Samwise Gamgee', 'Meriadoc Brandybuck', 'Boromir']
  },
  {
    question: 'Which creature says "My precious" about the One Ring?',
    answer: 'Gollum',
    choices: ['Gollum', 'Saruman', 'Sauron', 'Legolas']
  },
  {
    question: 'What is the Elvish name for Rivendell?',
    answer: 'Imladris',
    choices: ['Lothlórien', 'Imladris', 'Valinor', 'Erebor']
  },
  {
    question: 'Who is the Lady of Lothlórien?',
    answer: 'Galadriel',
    choices: ['Arwen', 'Galadriel', 'Éowyn', 'Goldberry']
  },
  {
    question: 'What is the name of the volcano where the One Ring must be destroyed?',
    answer: 'Mount Doom',
    choices: ['Mount Doom', 'Mount Erebor', 'Mount Gundabad', 'Mount Mindolluin']
  },
  {
    question: 'Which city is known as the White City?',
    answer: 'Minas Tirith',
    choices: ['Edoras', 'Minas Tirith', 'Osgiliath', 'Dale']
  },
  {
    question: 'Who is the king of Rohan during the War of the Ring?',
    answer: 'Théoden',
    choices: ['Théoden', 'Denethor', 'Aragorn', 'Elrond']
  },
  {
    question: 'What is the name of the sword reforged for Aragorn?',
    answer: 'Andúril',
    choices: ['Glamdring', 'Sting', 'Andúril', 'Orcrist']
  },
  {
    question: 'Which river runs through the Shire?',
    answer: 'Brandywine',
    choices: ['Anduin', 'Brandywine', 'Isen', 'Baranduin']
  }
];
