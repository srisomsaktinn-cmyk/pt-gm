import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import { 
  Volume2, 
  VolumeX,
  Heart, 
  Flame, 
  Zap, 
  CheckCircle2, 
  XCircle, 
  Lock, 
  Unlock,
  Star, 
  ArrowRight, 
  RotateCcw, 
  Award,
  Sparkles,
  BookOpen,
  HelpCircle,
  ShieldCheck,
  Gamepad2,
  Layers,
  Briefcase,
  Sun,
  Moon,
  Repeat,
  Info,
  GraduationCap
} from 'lucide-react';

// Comprehensive Japanese Particle Guide
const PARTICLE_GUIDE = [
  {
    symbol: 'wa',
    name: 'Topic Marker ("As for...")',
    why: 'Sets the main topic of conversation. It tells the listener: "Regarding X..."',
    example: 'Watashi wa Tin desu.',
    meaning: 'As for me, I am Tin.',
    rule: 'Use "wa" after the subject/topic you are introducing.',
    comparison: '"wa" highlights what comes AFTER it.'
  },
  {
    symbol: 'wo',
    name: 'Direct Object Marker ("Action Receiver")',
    why: 'Attached to the noun that directly receives an action verb (eat, drink, play, watch).',
    example: 'Sushi wo tabemasu / LoL wo shimasu.',
    meaning: 'Eat sushi / Play LoL.',
    rule: 'Noun + wo + Action Verb.',
    comparison: 'Always pairs with verbs like tabemasu (eat), nomimasu (drink), shimasu (do/play).'
  },
  {
    symbol: 'ga',
    name: 'Subject Emphasis & Likes Marker',
    why: 'Used to mark likes (suki), desires (daisuki), or emphasize WHO specifically does something.',
    example: 'Gēmu ga daisuki desu!',
    meaning: 'I love games!',
    rule: 'Noun + ga + suki / daisuki / hoshii.',
    comparison: 'Use "ga" with feelings/likes (suki), NOT "wo".'
  },
  {
    symbol: 'ni',
    name: 'Destination, Location of Being & Specific Time ("to / at")',
    why: 'Marks movement TO a place (ikimasu), existence AT a place (imasu), or a specific clock time.',
    example: 'Tokyo ni ikimasu / 7-ji ni tabemasu.',
    meaning: 'Go TO Tokyo / Eat AT 7 o\'clock.',
    rule: 'Place + ni + ikimasu (go) OR Time + ni.',
    comparison: '"ni" = destination point. "de" = place where action happens.'
  },
  {
    symbol: 'de',
    name: 'Location of Action & Means ("at / by")',
    why: 'Marks the location WHERE an active event takes place, or the tool/means used (by car, with chopsticks).',
    example: 'Uchi de gēmu wo shimasu.',
    meaning: 'Play games AT home.',
    rule: 'Location + de + Action Verb.',
    comparison: '"Uchi de tabemasu" (Eat AT home) vs "Tokyo ni ikimasu" (Go TO Tokyo).'
  },
  {
    symbol: 'no',
    name: 'Possession & Belonging ("\'s / of")',
    why: 'Connects two nouns where Noun 1 owns or describes Noun 2.',
    example: 'Watashi no tomodachi.',
    meaning: 'My friend (Friend of mine).',
    rule: 'Owner + no + Item.',
    comparison: 'Watashi no = My, Anata no = Your.'
  },
  {
    symbol: 'ka',
    name: 'Question Marker ("?")',
    why: 'Japanese does not traditionally use "?". Adding "ka" at the end of a polite sentence turns it into a question.',
    example: 'Ima isogashii desu ka?',
    meaning: 'Are you busy right now?',
    rule: 'Sentence + ka = Question.',
    comparison: 'Works like a spoken question mark.'
  },
  {
    symbol: 'ne',
    name: 'Confirmation Tag ("right? / isn\'t it?")',
    why: 'Added to the end of a sentence to politely seek agreement from older group members.',
    example: 'Omoshiroi desu ne!',
    meaning: 'It\'s fun, isn\'t it!',
    rule: 'Sentence + ne.',
    comparison: 'Creates a warm, shared feeling in group chat.'
  },
  {
    symbol: 'yo',
    name: 'Emphasis & Info Sharing Tag ("you know!")',
    why: 'Used when sharing new information or emphasizing your polite statement to friends.',
    example: 'Sugoi desu yo!',
    meaning: 'That\'s awesome, you know!',
    rule: 'Sentence + yo.',
    comparison: 'Adds positive energy & friendly confidence.'
  },
  {
    symbol: 'kedo',
    name: 'Softener / But ("although...")',
    why: 'Connects contrasting ideas or softens your sentence so you sound humble as the youngest member.',
    example: 'Mada heta desu kedo, ganbarimasu!',
    meaning: 'I\'m still bad at it, but I\'ll do my best!',
    rule: 'Statement + kedo + Next Clause.',
    comparison: 'Essential polite humble softener.'
  }
];

// Curriculum Levels Data - Expanded to 10 Questions per Level with Teach Hints
const LEVELS = [
  {
    id: 1,
    title: 'Level 1: Polite Greetings & Self-Intro as Youngest',
    desc: 'Learn how to introduce yourself respectfully to older group members.',
    toneNote: 'Since you are the youngest member in the group, using polite forms (-desu / -masu) shows respect to older friends while keeping a warm, friendly vibe.',
    lesson: [
      { 
        romaji: 'Konnichiwa!', 
        english: 'Hello / Good afternoon', 
        tip: 'Standard polite greeting for the group.',
        breakdown: [{ jp: 'Konnichiwa', en: 'Hello / Good day', type: 'normal' }],
        structure: '[ Greeting Formula ]'
      },
      { 
        romaji: 'Arigatou gozaimasu!', 
        english: 'Thank you very much (Polite)', 
        tip: 'Always add "gozaimasu" when thanking older friends.',
        breakdown: [
          { jp: 'Arigatou', en: 'Thank you', type: 'normal' },
          { jp: 'gozaimasu', en: '[Polite Extender] very much', type: 'verb' }
        ],
        structure: '[ Base Thanks ] + [ Polite Honorific Extender ]'
      },
      { 
        romaji: 'Sumimasen', 
        english: 'Excuse me / Sorry (Polite)', 
        tip: 'Use when asking a question or apologizing.',
        breakdown: [{ jp: 'Sumimasen', en: 'Excuse me / Sorry', type: 'normal' }],
        structure: '[ Polite Apology / Attention Call ]'
      },
      { 
        romaji: 'Watashi wa Tin desu.', 
        english: 'I am Tin.', 
        tip: 'Simple polite self-introduction.',
        breakdown: [
          { jp: 'Watashi', en: 'I / Me', type: 'normal' },
          { jp: 'wa', en: '[Topic Marker] as for', type: 'particle' },
          { jp: 'Tin', en: 'Tin (Name)', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] am/is', type: 'verb' }
        ],
        structure: '[ Subject: Watashi ] + [ Particle: wa ] + [ Name: Tin ] + [ Copula: desu ]'
      },
      { 
        romaji: 'Tai kara kimashita.', 
        english: 'I came from Thailand.', 
        tip: 'Explaining your origin.',
        breakdown: [
          { jp: 'Tai', en: 'Thailand', type: 'normal' },
          { jp: 'kara', en: '[Particle] from', type: 'particle' },
          { jp: 'kimashita', en: '[Past Verb] came', type: 'verb' }
        ],
        structure: '[ Origin Location: Tai ] + [ Particle: kara (from) ] + [ Polite Past Verb: kimashita (came) ]'
      },
      { 
        romaji: 'Yoroshiku onegaishimasu!', 
        english: 'Please treat me well!', 
        tip: 'Essential polite phrase when joining a group.',
        breakdown: [
          { jp: 'Yoroshiku', en: 'Well / Favorably', type: 'normal' },
          { jp: 'onegaishimasu', en: '[Polite Request] I ask of you', type: 'verb' }
        ],
        structure: '[ Adverb: Yoroshiku ] + [ Polite Request: onegaishimasu ]'
      }
    ],
    quiz: [
      {
        type: 'audio_choice',
        question: 'Q1: Listen and select the correct English meaning:',
        targetAudio: 'Arigatou gozaimasu!',
        options: ['Thank you very much (Polite)', 'See you tomorrow', 'Excuse me'],
        correctIndex: 0,
        teachHint: '"Arigatou" = thank you. Adding "gozaimasu" makes it respectful for older group friends.'
      },
      {
        type: 'word_arrange',
        question: 'Q2: Assemble the polite self-introduction: "I am Tin."',
        words: ['Tin desu.', 'Watashi', 'wa'],
        correctOrder: ['Watashi', 'wa', 'Tin desu.'],
        teachHint: 'Formula: [Watashi (I)] + [wa (as for)] + [Name desu (am Name)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q3: As the youngest group member, what is the polite way to say "Please treat me well"?',
        options: ['Yoroshiku onegaishimasu!', 'Jaa ne!', 'Daijoubu'],
        correctIndex: 0,
        teachHint: '"Yoroshiku onegaishimasu" is the classic polite request when joining a group.'
      },
      {
        type: 'multiple_choice',
        question: 'Q4: Fill in the particle: "Watashi ___ Tin desu."',
        options: ['wa', 'wo', 'ni'],
        correctIndex: 0,
        teachHint: '"wa" marks the topic ("As for me...").'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: What does "Konnichiwa" mean?',
        options: ['Hello / Good afternoon', 'Good night', 'Good morning'],
        correctIndex: 0,
        teachHint: '"Konnichiwa" is the standard greeting used during the day.'
      },
      {
        type: 'audio_choice',
        question: 'Q6: Listen and select the correct meaning:',
        targetAudio: 'Sumimasen',
        options: ['Excuse me / Sorry (Polite)', 'Thank you', 'Goodbye'],
        correctIndex: 0,
        teachHint: '"Sumimasen" is used to get attention or politely apologize.'
      },
      {
        type: 'word_arrange',
        question: 'Q7: Assemble: "I came from Thailand."',
        words: ['kimashita.', 'Tai kara'],
        correctOrder: ['Tai kara', 'kimashita.'],
        teachHint: '"Tai kara" (from Thailand) + "kimashita" (came - polite past verb).'
      },
      {
        type: 'multiple_choice',
        question: 'Q8: As the youngest member, how should you thank older friends?',
        options: ['Arigatou gozaimasu!', 'Domo', 'Sankyuu'],
        correctIndex: 0,
        teachHint: 'Always add "gozaimasu" to show respectful kouhai tone.'
      },
      {
        type: 'multiple_choice',
        question: 'Q9: Fill in the particle: "Tai ___ kimashita." (from Thailand)',
        options: ['kara', 'wa', 'wo'],
        correctIndex: 0,
        teachHint: '"kara" is the particle for "from".'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: When introduced to your new Japanese gamer friends, say:',
        options: ['Yoroshiku onegaishimasu!', 'Otsukaresama', 'Sumimasen'],
        correctIndex: 0,
        teachHint: '"Yoroshiku onegaishimasu" expresses excitement and respect to the group.'
      }
    ]
  },
  {
    id: 2,
    title: 'Level 2: SOV Structure & Particles (wa / wo)',
    desc: 'Master the Subject-Object-Verb order used in Japanese.',
    toneNote: 'Verb goes at the very end! Use polite "-masu" verbs with the group.',
    lesson: [
      { 
        romaji: 'Watashi wa sushi wo tabemasu.', 
        english: 'I eat sushi.', 
        tip: 'Subject (Watashi wa) + Object (sushi wo) + Verb (tabemasu).',
        breakdown: [
          { jp: 'Watashi', en: 'I / Me', type: 'normal' },
          { jp: 'wa', en: '[Topic Marker]', type: 'particle' },
          { jp: 'sushi', en: 'sushi (Object)', type: 'normal' },
          { jp: 'wo', en: '[Object Marker]', type: 'particle' },
          { jp: 'tabemasu', en: '[Polite Verb] eat', type: 'verb' }
        ],
        structure: '[ Subject: Watashi ] + [ wa ] + [ Object: sushi ] + [ wo ] + [ Verb: tabemasu ] (SOV Pattern)'
      },
      { 
        romaji: 'Watashi wa LoL wo shimasu.', 
        english: 'I play League of Legends.', 
        tip: '"shimasu" = to do / play (polite).',
        breakdown: [
          { jp: 'Watashi', en: 'I', type: 'normal' },
          { jp: 'wa', en: '[Topic Marker]', type: 'particle' },
          { jp: 'LoL', en: 'LoL (Game)', type: 'normal' },
          { jp: 'wo', en: '[Object Marker]', type: 'particle' },
          { jp: 'shimasu', en: '[Polite Verb] play/do', type: 'verb' }
        ],
        structure: '[ Subject: Watashi ] + [ wa ] + [ Object: LoL ] + [ wo ] + [ Verb: shimasu ]'
      },
      { 
        romaji: 'Kouhee wo nomimashita.', 
        english: 'I drank coffee.', 
        tip: '"wo" marks what you drink.',
        breakdown: [
          { jp: 'Kouhee', en: 'coffee', type: 'normal' },
          { jp: 'wo', en: '[Object Marker]', type: 'particle' },
          { jp: 'nomimashita', en: '[Polite Past Verb] drank', type: 'verb' }
        ],
        structure: '[ Object: Kouhee ] + [ Particle: wo ] + [ Past Verb: nomimashita ]'
      }
    ],
    quiz: [
      {
        type: 'word_arrange',
        question: 'Q1: Assemble the sentence: "I play LoL."',
        words: ['shimasu.', 'LoL wo', 'Watashi wa'],
        correctOrder: ['Watashi wa', 'LoL wo', 'shimasu.'],
        teachHint: 'SOV Order: [Watashi wa] + [LoL wo] + [shimasu (play)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q2: Which particle marks the direct object (the thing receiving the action)?',
        options: ['wo', 'wa', 'ni'],
        correctIndex: 0,
        teachHint: '"wo" attaches to direct objects (sushi wo, LoL wo, kouhee wo).'
      },
      {
        type: 'audio_choice',
        question: 'Q3: Listen and select the correct meaning:',
        targetAudio: 'Watashi wa sushi wo tabemasu.',
        options: ['I eat sushi.', 'I drink water.', 'I go to Tokyo.'],
        correctIndex: 0,
        teachHint: '"sushi wo tabemasu" = eat sushi.'
      },
      {
        type: 'word_arrange',
        question: 'Q4: Assemble: "I eat sushi."',
        words: ['tabemasu.', 'sushi wo', 'Watashi wa'],
        correctOrder: ['Watashi wa', 'sushi wo', 'tabemasu.'],
        teachHint: 'SOV: [Subject wa] + [Object wo] + [Verb tabemasu].'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: Fill in the particle: "Kouhee ___ nomimashita." (drank coffee)',
        options: ['wo', 'wa', 'ga'],
        correctIndex: 0,
        teachHint: '"wo" marks coffee as the direct object of drinking.'
      },
      {
        type: 'multiple_choice',
        question: 'Q6: What does "tabemasu" mean?',
        options: ['eat (polite)', 'drink', 'sleep'],
        correctIndex: 0,
        teachHint: '"tabemasu" is the polite verb for eat.'
      },
      {
        type: 'audio_choice',
        question: 'Q7: Listen and select the correct meaning:',
        targetAudio: 'Kouhee wo nomimashita.',
        options: ['I drank coffee.', 'I ate rice.', 'I like coffee.'],
        correctIndex: 0,
        teachHint: '"nomimashita" is past tense of drink.'
      },
      {
        type: 'word_arrange',
        question: 'Q8: Assemble: "I drank coffee."',
        words: ['nomimashita.', 'Kouhee wo'],
        correctOrder: ['Kouhee wo', 'nomimashita.'],
        teachHint: '[Kouhee wo] + [nomimashita (drank)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q9: Fill in the particle: "LoL ___ shimasu."',
        options: ['wo', 'ni', 'de'],
        correctIndex: 0,
        teachHint: '"LoL wo shimasu" = play LoL.'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: In Japanese sentence structure (SOV), where does the main verb go?',
        options: ['At the very end of the sentence', 'At the very beginning', 'Right after the topic'],
        correctIndex: 0,
        teachHint: 'Japanese is SOV: Subject – Object – Verb (verb always comes last).'
      }
    ]
  },
  {
    id: 3,
    title: 'Level 3: Asking Questions to Older Group Members',
    desc: 'How to ask questions politely using particle "ka" and "ni".',
    toneNote: 'Adding "ka?" to -masu makes a polite question for your group members!',
    lesson: [
      { 
        romaji: 'Kyou nani wo shimasu ka?', 
        english: 'What are you doing today?', 
        tip: '"nani" = what, "ka" = question tag.',
        breakdown: [
          { jp: 'Kyou', en: 'Today', type: 'normal' },
          { jp: 'nani', en: 'what', type: 'normal' },
          { jp: 'wo', en: '[Object Marker]', type: 'particle' },
          { jp: 'shimasu', en: '[Polite Verb] do', type: 'verb' },
          { jp: 'ka', en: '[Question Tag] ?', type: 'particle' }
        ],
        structure: '[ Time: Kyou ] + [ Question Word: nani ] + [ wo ] + [ Verb: shimasu ] + [ Tag: ka ]'
      },
      { 
        romaji: 'Doko ni ikimasu ka?', 
        english: 'Where are you going?', 
        tip: '"doko" = where, "ni" = to (destination).',
        breakdown: [
          { jp: 'Doko', en: 'Where', type: 'normal' },
          { jp: 'ni', en: '[Target Particle] to/at', type: 'particle' },
          { jp: 'ikimasu', en: '[Polite Verb] go', type: 'verb' },
          { jp: 'ka', en: '[Question Tag] ?', type: 'particle' }
        ],
        structure: '[ Question Word: Doko ] + [ Particle: ni (to) ] + [ Verb: ikimasu ] + [ Tag: ka ]'
      },
      { 
        romaji: 'Ima isogashii desu ka?', 
        english: 'Are you busy right now?', 
        tip: '"isogashii" is the authentic native Japanese i-adjective for "busy".',
        breakdown: [
          { jp: 'Ima', en: 'Right now / Now', type: 'normal' },
          { jp: 'isogashii', en: 'busy (Japanese adj)', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] are', type: 'verb' },
          { jp: 'ka', en: '[Question Tag] ?', type: 'particle' }
        ],
        structure: '[ Time: Ima ] + [ Native Adjective: isogashii ] + [ Copula: desu ] + [ Tag: ka ]'
      }
    ],
    quiz: [
      {
        type: 'word_arrange',
        question: 'Q1: Assemble the question: "Where are you going?"',
        words: ['ikimasu ka?', 'ni', 'Doko'],
        correctOrder: ['Doko', 'ni', 'ikimasu ka?'],
        teachHint: '[Doko (where)] + [ni (to)] + [ikimasu ka? (are going?)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q2: What is the correct native Japanese word for "busy" in "Are you busy right now?"',
        options: ['isogashii (Ima isogashii desu ka?)', 'busy (Ima busy desu ka?)', 'tanoshii'],
        correctIndex: 0,
        teachHint: 'Native Japanese uses "isogashii" for busy, not English loanword.'
      },
      {
        type: 'audio_choice',
        question: 'Q3: Listen and select the English meaning:',
        targetAudio: 'Kyou nani wo shimasu ka?',
        options: ['What are you doing today?', 'Where do you live?', 'What is your name?'],
        correctIndex: 0,
        teachHint: '"Kyou" = today, "nani" = what, "shimasu ka" = do?'
      },
      {
        type: 'word_arrange',
        question: 'Q4: Assemble: "What are you doing today?"',
        words: ['shimasu ka?', 'Kyou', 'nani wo'],
        correctOrder: ['Kyou', 'nani wo', 'shimasu ka?'],
        teachHint: '[Time: Kyou] + [Object: nani wo] + [Verb: shimasu ka?].'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: Fill in the destination particle: "Doko ___ ikimasu ka?" (to)',
        options: ['ni', 'wa', 'wo'],
        correctIndex: 0,
        teachHint: '"ni" is the destination particle ("to").'
      },
      {
        type: 'multiple_choice',
        question: 'Q6: What particle is added to turn a sentence into a question?',
        options: ['ka', 'ne', 'yo'],
        correctIndex: 0,
        teachHint: '"ka" acts as the spoken question mark.'
      },
      {
        type: 'audio_choice',
        question: 'Q7: Listen and select the correct meaning:',
        targetAudio: 'Doko ni ikimasu ka?',
        options: ['Where are you going?', 'What are you eating?', 'Who are you with?'],
        correctIndex: 0,
        teachHint: '"Doko ni ikimasu ka?" = Where are you going?'
      },
      {
        type: 'word_arrange',
        question: 'Q8: Assemble: "Are you busy right now?"',
        words: ['desu ka?', 'isogashii', 'Ima'],
        correctOrder: ['Ima', 'isogashii', 'desu ka?'],
        teachHint: '[Ima (now)] + [isogashii (busy)] + [desu ka?].'
      },
      {
        type: 'multiple_choice',
        question: 'Q9: Fill in the particle: "Kyou nani ___ shimasu ka?"',
        options: ['wo', 'ni', 'de'],
        correctIndex: 0,
        teachHint: '"wo" marks "nani" (what) as object of doing.'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: What does "ikimasu" mean?',
        options: ['go (polite)', 'come', 'return'],
        correctIndex: 0,
        teachHint: '"ikimasu" = to go.'
      }
    ]
  },
  {
    id: 4,
    title: 'Level 4: Expressing Hobbies & Likes (Particle ga)',
    desc: 'Tell the group what games and activities you love.',
    toneNote: 'Use "ga daisuki desu" (love) or "ga suki desu" (like) politely.',
    lesson: [
      { 
        romaji: 'Gēmu ga daisuki desu!', 
        english: 'I love games!', 
        tip: '"ga" marks what you like/love.',
        breakdown: [
          { jp: 'Gēmu', en: 'Games', type: 'normal' },
          { jp: 'ga', en: '[Preference Particle]', type: 'particle' },
          { jp: 'daisuki', en: 'love / favorite', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] is/are', type: 'verb' }
        ],
        structure: '[ Target: Gēmu ] + [ Particle: ga ] + [ Noun/Adj: daisuki ] + [ Copula: desu ]'
      },
      { 
        romaji: 'Valorant ga suki desu.', 
        english: 'I like Valorant.', 
        tip: 'Great for Discord voice chats.',
        breakdown: [
          { jp: 'Valorant', en: 'Valorant', type: 'normal' },
          { jp: 'ga', en: '[Preference Particle]', type: 'particle' },
          { jp: 'suki', en: 'like', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] is', type: 'verb' }
        ],
        structure: '[ Target: Valorant ] + [ Particle: ga ] + [ Adjective: suki ] + [ Copula: desu ]'
      },
      { 
        romaji: 'Nihongo ga suki desu.', 
        english: 'I like Japanese.', 
        tip: 'Showing your enthusiasm to friends!',
        breakdown: [
          { jp: 'Nihongo', en: 'Japanese language', type: 'normal' },
          { jp: 'ga', en: '[Preference Particle]', type: 'particle' },
          { jp: 'suki', en: 'like', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] is', type: 'verb' }
        ],
        structure: '[ Target: Nihongo ] + [ Particle: ga ] + [ Adjective: suki ] + [ Copula: desu ]'
      }
    ],
    quiz: [
      {
        type: 'word_arrange',
        question: 'Q1: Assemble: "I love games!"',
        words: ['daisuki desu!', 'Gēmu ga'],
        correctOrder: ['Gēmu ga', 'daisuki desu!'],
        teachHint: '[Gēmu ga (games)] + [daisuki desu! (love)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q2: Fill in the blank: "Valorant ___ suki desu."',
        options: ['ga', 'wo', 'wa'],
        correctIndex: 0,
        teachHint: 'Feelings & likes (suki/daisuki) use particle "ga", NOT "wo".'
      },
      {
        type: 'audio_choice',
        question: 'Q3: Listen and select the correct meaning:',
        targetAudio: 'Gēmu ga daisuki desu!',
        options: ['I love games!', 'I play games.', 'I buy games.'],
        correctIndex: 0,
        teachHint: '"daisuki desu" = love / favorite.'
      },
      {
        type: 'word_arrange',
        question: 'Q4: Assemble: "I like Valorant."',
        words: ['suki desu.', 'Valorant ga'],
        correctOrder: ['Valorant ga', 'suki desu.'],
        teachHint: '[Valorant ga] + [suki desu].'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: Fill in the particle: "Nihongo ___ suki desu."',
        options: ['ga', 'wo', 'ni'],
        correctIndex: 0,
        teachHint: '"ga" marks what you like.'
      },
      {
        type: 'multiple_choice',
        question: 'Q6: What does "suki desu" mean?',
        options: ['like (polite)', 'dislike', 'want'],
        correctIndex: 0,
        teachHint: '"suki" = like.'
      },
      {
        type: 'audio_choice',
        question: 'Q7: Listen and select the correct meaning:',
        targetAudio: 'Valorant ga suki desu.',
        options: ['I like Valorant.', 'I hate Valorant.', 'I play Valorant.'],
        correctIndex: 0,
        teachHint: '"Valorant ga suki desu" = I like Valorant.'
      },
      {
        type: 'word_arrange',
        question: 'Q8: Assemble: "I like Japanese."',
        words: ['suki desu.', 'Nihongo ga'],
        correctOrder: ['Nihongo ga', 'suki desu.'],
        teachHint: '[Nihongo ga] + [suki desu].'
      },
      {
        type: 'multiple_choice',
        question: 'Q9: Why do we use particle "ga" instead of "wo" with "suki desu"?',
        options: ['"ga" marks preferences, feelings, and likes', '"ga" is only for past tense', '"ga" means to go'],
        correctIndex: 0,
        teachHint: '"suki" is an adjective in Japanese, so it takes "ga" instead of object marker "wo".'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: What does "daisuki" mean?',
        options: ['love / favorite', 'a little bit', 'difficult'],
        correctIndex: 0,
        teachHint: '"daisuki" = big like / love.'
      }
    ]
  },
  {
    id: 5,
    title: 'Level 5: Past Tense & Daily Routine (-mashita)',
    desc: 'Talk about what you did yesterday or earlier.',
    toneNote: 'Change "-masu" to "-mashita" for polite past tense.',
    lesson: [
      { 
        romaji: 'Kinou LoL wo shimashita.', 
        english: 'I played LoL yesterday.', 
        tip: '"kinou" = yesterday, "shimashita" = played.',
        breakdown: [
          { jp: 'Kinou', en: 'Yesterday', type: 'normal' },
          { jp: 'LoL', en: 'LoL', type: 'normal' },
          { jp: 'wo', en: '[Object Marker]', type: 'particle' },
          { jp: 'shimashita', en: '[Polite Past Verb] played', type: 'verb' }
        ],
        structure: '[ Time: Kinou ] + [ Object: LoL ] + [ Particle: wo ] + [ Past Verb: shimashita ]'
      },
      { 
        romaji: 'Oishii sushi wo tabemashita.', 
        english: 'I ate delicious sushi.', 
        tip: '"tabemashita" = ate.',
        breakdown: [
          { jp: 'Oishii', en: 'Delicious', type: 'normal' },
          { jp: 'sushi', en: 'sushi', type: 'normal' },
          { jp: 'wo', en: '[Object Marker]', type: 'particle' },
          { jp: 'tabemashita', en: '[Polite Past Verb] ate', type: 'verb' }
        ],
        structure: '[ Modifier: Oishii ] + [ Noun: sushi ] + [ Particle: wo ] + [ Past Verb: tabemashita ]'
      }
    ],
    quiz: [
      {
        type: 'word_arrange',
        question: 'Q1: Assemble: "I played LoL yesterday."',
        words: ['shimashita.', 'LoL wo', 'Kinou'],
        correctOrder: ['Kinou', 'LoL wo', 'shimashita.'],
        teachHint: '[Kinou (yesterday)] + [LoL wo] + [shimashita (played)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q2: What is the polite past tense ending for verbs (-masu)?',
        options: ['-mashita', '-masen', '-masou'],
        correctIndex: 0,
        teachHint: 'Change "-masu" to "-mashita" to express past tense.'
      },
      {
        type: 'audio_choice',
        question: 'Q3: Listen and select the correct meaning:',
        targetAudio: 'Kinou LoL wo shimashita.',
        options: ['I played LoL yesterday.', 'I play LoL tomorrow.', 'I don\'t play LoL.'],
        correctIndex: 0,
        teachHint: '"Kinou" = yesterday, "shimashita" = played.'
      },
      {
        type: 'word_arrange',
        question: 'Q4: Assemble: "I ate delicious sushi."',
        words: ['tabemashita.', 'sushi wo', 'Oishii'],
        correctOrder: ['Oishii', 'sushi wo', 'tabemashita.'],
        teachHint: '[Oishii sushi wo] + [tabemashita (ate)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: Fill in the particle: "Kinou LoL ___ shimashita."',
        options: ['wo', 'wa', 'ni'],
        correctIndex: 0,
        teachHint: '"wo" marks LoL as the object played.'
      },
      {
        type: 'multiple_choice',
        question: 'Q6: What does "kinou" mean?',
        options: ['yesterday', 'today', 'tomorrow'],
        correctIndex: 0,
        teachHint: '"kinou" = yesterday.'
      },
      {
        type: 'audio_choice',
        question: 'Q7: Listen and select the correct meaning:',
        targetAudio: 'Oishii sushi wo tabemashita.',
        options: ['I ate delicious sushi.', 'I eat sushi today.', 'Sushi is expensive.'],
        correctIndex: 0,
        teachHint: '"tabemashita" = ate.'
      },
      {
        type: 'multiple_choice',
        question: 'Q8: What is the polite past tense of "tabemasu" (eat)?',
        options: ['tabemashita', 'tabemasen', 'taberu'],
        correctIndex: 0,
        teachHint: 'tabemasu -> tabemashita.'
      },
      {
        type: 'word_arrange',
        question: 'Q9: Assemble: "I drank coffee yesterday."',
        words: ['nomimashita.', 'kouhee wo', 'Kinou'],
        correctOrder: ['Kinou', 'kouhee wo', 'nomimashita.'],
        teachHint: '[Kinou] + [kouhee wo] + [nomimashita].'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: What does "oishii" mean?',
        options: ['delicious', 'bad tasting', 'hot'],
        correctIndex: 0,
        teachHint: '"oishii" = delicious.'
      }
    ]
  },
  {
    id: 6,
    title: 'Level 6: Polite Softeners for Group Chat (ne, yo, kedo)',
    desc: 'Sound natural as the youngest member in group discussions.',
    toneNote: 'Use "desu ne" (right?), "desu yo" (you know), and "kedo" (but) to soften your speech.',
    lesson: [
      { 
        romaji: 'Omoshiroi desu ne!', 
        english: 'That\'s interesting / fun, isn\'t it!', 
        tip: '"ne" seeks agreement from older friends.',
        breakdown: [
          { jp: 'Omoshiroi', en: 'Fun / Interesting', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] is', type: 'verb' },
          { jp: 'ne', en: '[Tag] right?', type: 'particle' }
        ],
        structure: '[ Adjective: Omoshiroi ] + [ Copula: desu ] + [ Sentence Tag: ne (right?) ]'
      },
      { 
        romaji: 'Mada heta desu kedo, ganbarimasu!', 
        english: 'I\'m still bad at it, but I\'ll do my best!', 
        tip: 'Humble & polite kouhai attitude.',
        breakdown: [
          { jp: 'Mada', en: 'Still', type: 'normal' },
          { jp: 'heta', en: 'unskilled/bad', type: 'normal' },
          { jp: 'desu', en: 'am', type: 'verb' },
          { jp: 'kedo', en: '[Softener] but', type: 'particle' },
          { jp: 'ganbarimasu', en: '[Polite Verb] will do my best', type: 'verb' }
        ],
        structure: '[ Condition: Mada heta desu ] + [ Softener: kedo (but) ] + [ Verb: ganbarimasu ]'
      },
      { 
        romaji: 'Sugoi desu yo!', 
        english: 'That\'s awesome, you know!', 
        tip: 'Expressing genuine praise to group members.',
        breakdown: [
          { jp: 'Sugoi', en: 'Awesome / Amazing', type: 'normal' },
          { jp: 'desu', en: 'is', type: 'verb' },
          { jp: 'yo', en: '[Tag] you know!', type: 'particle' }
        ],
        structure: '[ Adjective: Sugoi ] + [ Copula: desu ] + [ Sentence Tag: yo (emphasis) ]'
      }
    ],
    quiz: [
      {
        type: 'word_arrange',
        question: 'Q1: Assemble: "I\'m still bad at it, but I\'ll do my best!"',
        words: ['ganbarimasu!', 'Mada heta desu kedo,'],
        correctOrder: ['Mada heta desu kedo,', 'ganbarimasu!'],
        teachHint: '[Mada heta desu kedo (still bad but)] + [ganbarimasu! (I\'ll do my best)].'
      },
      {
        type: 'multiple_choice',
        question: 'Q2: Which tag politely seeks agreement ("isn\'t it?")?',
        options: ['ne', 'yo', 'ka'],
        correctIndex: 0,
        teachHint: '"ne" asks for soft agreement from friends.'
      },
      {
        type: 'audio_choice',
        question: 'Q3: Listen and select the correct meaning:',
        targetAudio: 'Omoshiroi desu ne!',
        options: ['That\'s fun, isn\'t it!', 'It\'s boring.', 'Are you busy?'],
        correctIndex: 0,
        teachHint: '"Omoshiroi" = fun/interesting.'
      },
      {
        type: 'word_arrange',
        question: 'Q4: Assemble: "That\'s fun, isn\'t it!"',
        words: ['ne!', 'Omoshiroi desu'],
        correctOrder: ['Omoshiroi desu', 'ne!'],
        teachHint: '[Omoshiroi desu] + [ne!].'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: Fill in particle: "Sugoi desu ___!" (you know!)',
        options: ['yo', 'kedo', 'wa'],
        correctIndex: 0,
        teachHint: '"yo" adds polite emphasis when sharing praise.'
      },
      {
        type: 'multiple_choice',
        question: 'Q6: What does "kedo" mean in "Mada heta desu kedo"?',
        options: ['but / although (softener)', 'and', 'because'],
        correctIndex: 0,
        teachHint: '"kedo" softens a sentence meaning "but / although".'
      },
      {
        type: 'audio_choice',
        question: 'Q7: Listen and select the correct meaning:',
        targetAudio: 'Sugoi desu yo!',
        options: ['That\'s awesome, you know!', 'It\'s difficult.', 'No problem.'],
        correctIndex: 0,
        teachHint: '"Sugoi" = awesome/amazing.'
      },
      {
        type: 'word_arrange',
        question: 'Q8: Assemble: "That\'s awesome, you know!"',
        words: ['yo!', 'Sugoi desu'],
        correctOrder: ['Sugoi desu', 'yo!'],
        teachHint: '[Sugoi desu] + [yo!].'
      },
      {
        type: 'multiple_choice',
        question: 'Q9: Fill in particle: "Mada heta desu ___ ganbarimasu!"',
        options: ['kedo', 'yo', 'ne'],
        correctIndex: 0,
        teachHint: '"kedo" connects the contrast ("bad BUT will try").'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: What does "ganbarimasu" mean?',
        options: ['I will do my best!', 'I am going home.', 'Thank you.'],
        correctIndex: 0,
        teachHint: '"ganbarimasu" = do my best.'
      }
    ]
  },
  {
    id: 7,
    title: 'Level 7: Gamer & Discord Group Vocab (Polite Hype)',
    desc: 'Respectful and energetic phrases for gaming with older friends.',
    toneNote: 'High energy yet polite! Perfect for ending gaming sessions with "Otsukaresama desu!".',
    lesson: [
      { 
        romaji: 'Naisu desu!', 
        english: 'Nice play! (Polite)', 
        tip: 'Praising your older teammate.',
        breakdown: [
          { jp: 'Naisu', en: 'Nice play', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula] is', type: 'verb' }
        ],
        structure: '[ Gamer Word: Naisu ] + [ Kouhai Respect Copula: desu ]'
      },
      { 
        romaji: 'Maji desu ka?!', 
        english: 'Seriously?! / For real?!', 
        tip: 'Polite version of "Maji de?".',
        breakdown: [
          { jp: 'Maji', en: 'Seriously / For real', type: 'normal' },
          { jp: 'desu', en: 'is', type: 'verb' },
          { jp: 'ka', en: '[Question Tag] ?', type: 'particle' }
        ],
        structure: '[ Slang: Maji ] + [ Polite Copula: desu ] + [ Question Tag: ka ]'
      },
      { 
        romaji: 'Ikimashou!', 
        english: 'Let\'s go!', 
        tip: 'Polite invitation to start a match.',
        breakdown: [
          { jp: 'Ikimashou', en: '[Polite Volitional Verb] Let\'s go!', type: 'verb' }
        ],
        structure: '[ Verb Stem: Iki ] + [ Polite Volitional Ending: -mashou (let\'s...) ]'
      },
      { 
        romaji: 'Otsukaresama desu!', 
        english: 'Great work everyone / Good game!', 
        tip: 'Essential polite phrase when ending a session.',
        breakdown: [
          { jp: 'Otsukaresama', en: 'Good work / Thanks for your work', type: 'normal' },
          { jp: 'desu', en: '[Polite Copula]', type: 'verb' }
        ],
        structure: '[ Group Thanks Formula: Otsukaresama ] + [ Polite Copula: desu ]'
      }
    ],
    quiz: [
      {
        type: 'multiple_choice',
        question: 'Q1: What essential phrase should you say to the group after finishing a game session?',
        options: ['Otsukaresama desu!', 'Sayounara', 'Sumimasen'],
        correctIndex: 0,
        teachHint: '"Otsukaresama desu" is the universal polite phrase for ending work/gaming sessions.'
      },
      {
        type: 'word_arrange',
        question: 'Q2: Assemble: "Seriously?! Nice play!"',
        words: ['Naisu desu!', 'Maji desu ka?!'],
        correctOrder: ['Maji desu ka?!', 'Naisu desu!'],
        teachHint: '[Maji desu ka?!] + [Naisu desu!].'
      },
      {
        type: 'audio_choice',
        question: 'Q3: Listen and select the correct meaning:',
        targetAudio: 'Otsukaresama desu!',
        options: ['Great work everyone / Good game!', 'Welcome home', 'Nice to meet you'],
        correctIndex: 0,
        teachHint: '"Otsukaresama desu" = thanks for your hard work / good game.'
      },
      {
        type: 'word_arrange',
        question: 'Q4: Assemble: "Let\'s go!"',
        words: ['Ikimashou!'],
        correctOrder: ['Ikimashou!'],
        teachHint: '"Ikimashou" = let\'s go (polite volitional).'
      },
      {
        type: 'multiple_choice',
        question: 'Q5: What is the polite way to say "Let\'s go!" to older teammates?',
        options: ['Ikimashou!', 'Ikuzo', 'Ike'],
        correctIndex: 0,
        teachHint: '"Ikimashou!" is polite and hype.'
      },
      {
        type: 'audio_choice',
        question: 'Q6: Listen and select the correct meaning:',
        targetAudio: 'Maji desu ka?!',
        options: ['Seriously?! / For real?!', 'Are you ready?', 'Good evening'],
        correctIndex: 0,
        teachHint: '"Maji desu ka" = polite "Seriously?!"'
      },
      {
        type: 'word_arrange',
        question: 'Q7: Assemble: "Nice play!"',
        words: ['desu!', 'Naisu'],
        correctOrder: ['Naisu', 'desu!'],
        teachHint: '[Naisu] + [desu!].'
      },
      {
        type: 'multiple_choice',
        question: 'Q8: What does "Otsukaresama desu" mean in gamer Discord voice chats?',
        options: ['Good game / Thanks for the matches!', 'Sorry I died', 'I am hungry'],
        correctIndex: 0,
        teachHint: 'Standard polite sign-off after gaming together.'
      },
      {
        type: 'audio_choice',
        question: 'Q9: Listen and select the correct meaning:',
        targetAudio: 'Ikimashou!',
        options: ['Let\'s go!', 'Let\'s eat!', 'Let\'s sleep!'],
        correctIndex: 0,
        teachHint: '"Ikimashou!" = Let\'s go!'
      },
      {
        type: 'multiple_choice',
        question: 'Q10: When praising an older teammate\'s good play, say:',
        options: ['Naisu desu!', 'Baka', 'Mada mada'],
        correctIndex: 0,
        teachHint: '"Naisu desu!" is polite and encouraging.'
      }
    ]
  }
];

export default function App() {
  // Navigation & Persistent Game State (localStorage backed!)
  const [unlockedLevel, setUnlockedLevel] = useState(() => {
    const saved = localStorage.getItem('tin_unlocked_level');
    return saved ? parseInt(saved, 10) : LEVELS.length; // Default: ALL LEVELS UNLOCKED!
  });

  const [currentLevel, setCurrentLevel] = useState(null); // level object
  const [mode, setMode] = useState('map'); // 'map', 'learn', 'test'
  
  // Inline Teach Hint toggle state per question
  const [showTeachHint, setShowTeachHint] = useState(false);

  // Particle Master Guide Modal Toggle
  const [showParticleGuide, setShowParticleGuide] = useState(false);

  // Persistent Theme State
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('tin_theme') || 'dark';
  });

  // Persistent Workplace Silent Mode Toggle
  const [isMuted, setIsMuted] = useState(() => {
    return localStorage.getItem('tin_muted') === 'true';
  });

  // Persistent Gamification Stats
  const [xp, setXp] = useState(() => {
    const saved = localStorage.getItem('tin_xp');
    return saved ? parseInt(saved, 10) : 0;
  });

  const [streak, setStreak] = useState(() => {
    const saved = localStorage.getItem('tin_streak');
    return saved ? parseInt(saved, 10) : 1;
  });

  const [hearts, setHearts] = useState(3);
  
  // Test Mode & Dynamic Retry Queue State
  const [quizQueue, setQuizQueue] = useState([]);
  const [quizIndex, setQuizIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [arrangedWords, setArrangedWords] = useState([]);
  const [quizStatus, setQuizStatus] = useState(null); // 'correct', 'wrong', null
  const [showCelebration, setShowCelebration] = useState(false);

  // Sync state changes to localStorage so progress NEVER resets
  useEffect(() => {
    localStorage.setItem('tin_unlocked_level', unlockedLevel.toString());
  }, [unlockedLevel]);

  useEffect(() => {
    localStorage.setItem('tin_xp', xp.toString());
  }, [xp]);

  useEffect(() => {
    localStorage.setItem('tin_streak', streak.toString());
  }, [streak]);

  useEffect(() => {
    localStorage.setItem('tin_theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('tin_muted', isMuted.toString());
  }, [isMuted]);

  // Speech Helper with Mute Protection
  const speakJapanese = (text) => {
    if (isMuted) return; // Silent Workplace Mode!
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ja-JP';
    utterance.rate = 0.85;
    window.speechSynthesis.speak(utterance);
  };

  // Start Level (Teach Phase first)
  const startLevel = (lvl) => {
    setCurrentLevel(lvl);
    setMode('learn');
  };

  // Switch to Test Mode & Initialize Dynamic Quiz Queue
  const startTest = () => {
    setMode('test');
    setQuizQueue(currentLevel.quiz);
    setQuizIndex(0);
    setHearts(3);
    setSelectedOption(null);
    setArrangedWords([]);
    setQuizStatus(null);
    setShowTeachHint(false);
  };

  // Word Block Puzzle helpers
  const handleWordTap = (word) => {
    if (arrangedWords.includes(word)) {
      setArrangedWords(arrangedWords.filter(w => w !== word));
    } else {
      setArrangedWords([...arrangedWords, word]);
    }
  };

  // Check Answer with Retry Queue Addition
  const checkAnswer = () => {
    const currentQuestion = quizQueue[quizIndex];

    let isCorrect = false;
    if (currentQuestion.type === 'word_arrange') {
      isCorrect = JSON.stringify(arrangedWords) === JSON.stringify(currentQuestion.correctOrder);
    } else {
      isCorrect = selectedOption === currentQuestion.correctIndex;
    }

    if (isCorrect) {
      setQuizStatus('correct');
      setXp(prev => prev + 10);
      speakJapanese(currentQuestion.targetAudio || arrangedWords.join(' ') || 'Yatta!');
    } else {
      setQuizStatus('wrong');
      setHearts(prev => Math.max(0, prev - 1));

      // Auto-reveal teach hint on wrong answer so user learns before retry!
      setShowTeachHint(true);

      // 🔁 RETRY SYSTEM: Push incorrect question to the end of quiz queue!
      setQuizQueue(prev => [...prev, { ...currentQuestion, isReview: true }]);
    }
  };

  // Move to Next Question or Complete Test
  const nextQuestion = () => {
    if (quizIndex + 1 < quizQueue.length) {
      setQuizIndex(prev => prev + 1);
      setSelectedOption(null);
      setArrangedWords([]);
      setQuizStatus(null);
      setShowTeachHint(false);
    } else {
      // Passed Test!
      setShowCelebration(true);
      confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
      if (currentLevel.id >= unlockedLevel) {
        setUnlockedLevel(currentLevel.id + 1);
      }
    }
  };

  // Close celebration modal and return to map
  const finishLevel = () => {
    setShowCelebration(false);
    setMode('map');
  };

  // Toggle All Unlocked vs Progression Mode
  const toggleUnlockAll = () => {
    if (unlockedLevel >= LEVELS.length) {
      setUnlockedLevel(1);
    } else {
      setUnlockedLevel(LEVELS.length);
    }
  };

  return (
    <div className="app-container">
      {/* Top Gamified Header Bar */}
      <header className="top-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles color="var(--duo-green)" size={24} />
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: '800', fontSize: '18px' }}>
            Tin's Japanese Path
          </span>
        </div>

        <div className="nav-stats">
          {/* Particle Master Guide Button */}
          <button 
            className="duo-btn duo-btn-purple"
            style={{ padding: '6px 12px', fontSize: '12px' }}
            onClick={() => setShowParticleGuide(true)}
            title="Learn WHY we use wa, ga, wo, ni, de..."
          >
            <Info size={14} /> Particle Guide
          </button>

          {/* Unlock All Levels Button */}
          <button 
            className={`duo-btn ${unlockedLevel >= LEVELS.length ? 'duo-btn-green' : 'duo-btn-secondary'}`}
            style={{ padding: '6px 12px', fontSize: '12px' }}
            onClick={toggleUnlockAll}
            title="Jump to any level freely"
          >
            {unlockedLevel >= LEVELS.length ? <Unlock size={14} /> : <Lock size={14} />}
            {unlockedLevel >= LEVELS.length ? 'All Unlocked' : 'Lock Levels'}
          </button>

          {/* Theme Switcher Button (Light / Dark) */}
          <button 
            className="duo-btn duo-btn-secondary"
            style={{ padding: '6px 12px', fontSize: '12px' }}
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Toggle Light / Dark Mode"
          >
            {theme === 'dark' ? <Sun size={14} color="var(--duo-gold)" /> : <Moon size={14} color="var(--duo-purple)" />}
            {theme === 'dark' ? 'Light' : 'Dark'}
          </button>

          {/* Work Place Audio Mode Toggle Button */}
          <button 
            className={`duo-btn ${isMuted ? 'duo-btn-purple' : 'duo-btn-cyan'}`}
            style={{ padding: '6px 12px', fontSize: '12px' }}
            onClick={() => setIsMuted(!isMuted)}
          >
            {isMuted ? (
              <>
                <Briefcase size={14} /> Muted
              </>
            ) : (
              <>
                <Volume2 size={14} /> Sound ON
              </>
            )}
          </button>

          <div className="stat-badge streak">
            <Flame size={16} /> {streak}d
          </div>
          <div className="stat-badge xp">
            <Zap size={16} /> {xp} XP
          </div>
          <div className="stat-badge hearts">
            <Heart size={16} fill="var(--duo-rose)" /> {hearts}
          </div>
        </div>
      </header>

      {/* Workplace Mode Notice Toast if Muted */}
      {isMuted && (
        <div style={{ background: 'rgba(206, 130, 255, 0.15)', border: '1px solid var(--duo-purple)', padding: '10px 16px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', color: 'var(--text-main)' }}>
          <Briefcase size={18} color="var(--duo-purple)" />
          <span><strong>Workplace Silent Mode Active:</strong> Audio playback is muted so you can study discreetly without speakers at work. Text transcripts will guide your tests.</span>
        </div>
      )}

      {/* VIEW 1: LEVEL MAP (Duolingo Path) */}
      {mode === 'map' && (
        <div className="level-map-container">
          <div style={{ textAlign: 'center', maxWidth: '500px' }}>
            <h1 style={{ fontSize: '32px', fontWeight: '800' }}>Your Romaji Learning Trail</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '15px', marginTop: '6px' }}>
              Teach Me (Word Breakdown + Structure) $\rightarrow$ 10-Question Test $\rightarrow$ Next Level!
            </p>
          </div>

          <div className="level-path">
            {LEVELS.map((lvl, idx) => {
              const isUnlocked = lvl.id <= unlockedLevel;
              const isCurrent = lvl.id === unlockedLevel;

              return (
                <div key={lvl.id} className="level-node-wrapper">
                  <button 
                    className={`level-node ${isCurrent ? 'current' : isUnlocked ? 'unlocked' : 'locked'}`}
                    onClick={() => startLevel(lvl)}
                  >
                    {isUnlocked ? (
                      <CheckCircle2 size={36} color="#fff" />
                    ) : (
                      <Lock size={28} />
                    )}
                  </button>

                  <div className="level-label">
                    {lvl.title}
                  </div>

                  {idx < LEVELS.length - 1 && (
                    <div className={`node-connector ${lvl.id < unlockedLevel ? 'active' : ''}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* VIEW 2: TEACH ME PHASE (Lesson Cards with Word Breakdown & Structure) */}
      {mode === 'learn' && currentLevel && (
        <div className="lesson-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '13px', color: 'var(--duo-green)', fontWeight: '800', textTransform: 'uppercase' }}>
                📖 TEACH ME PHASE — WORD-BY-WORD & STRUCTURE
              </span>
              <h2 style={{ fontSize: '24px', fontWeight: '800', marginTop: '4px' }}>{currentLevel.title}</h2>
            </div>
            <button className="duo-btn duo-btn-secondary" onClick={() => setMode('map')}>
              Exit
            </button>
          </div>

          {/* Tone & Context Explanation Banner */}
          <div className="tone-banner">
            <ShieldCheck size={24} color="var(--duo-purple)" style={{ flexShrink: 0 }} />
            <div>
              <strong style={{ display: 'block', fontSize: '15px' }}>Youngest Group Member Tone Guide:</strong>
              {currentLevel.toneNote}
            </div>
          </div>

          {/* Vocabulary Cards with Word Breakdown Chips & Structure Box */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {currentLevel.lesson.map((item, idx) => (
              <div 
                key={idx} 
                style={{ background: 'rgba(0, 0, 0, 0.02)', border: '1px solid var(--border-color)', padding: '20px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '12px' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                  <div>
                    <div style={{ fontFamily: 'var(--font-heading)', fontSize: '22px', fontWeight: '800', color: 'var(--duo-cyan)' }}>
                      {item.romaji}
                    </div>
                    <div style={{ fontSize: '15px', color: 'var(--text-main)', marginTop: '2px', fontWeight: '600' }}>
                      {item.english}
                    </div>
                  </div>

                  <button 
                    className={`duo-btn ${isMuted ? 'duo-btn-secondary' : 'duo-btn-cyan'}`} 
                    style={{ padding: '8px 14px', fontSize: '13px', flexShrink: 0 }}
                    onClick={() => speakJapanese(item.romaji)}
                    disabled={isMuted}
                  >
                    {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />} 
                    {isMuted ? 'Muted' : 'Listen'}
                  </button>
                </div>

                {/* WORD BY WORD BREAKDOWN CHIPS */}
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    🔍 Word-by-Word Breakdown:
                  </div>
                  <div className="word-breakdown-row">
                    {item.breakdown.map((w, wIdx) => (
                      <div key={wIdx} className={`word-chip ${w.type}`}>
                        <span className="jp-word">{w.jp}</span>
                        <span className="en-word">{w.en}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* SENTENCE STRUCTURE MAP */}
                <div className="structure-box">
                  <Layers size={16} color="var(--duo-green)" style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Sentence Formula:</strong> {item.structure}
                  </div>
                </div>

                {/* Tip */}
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  💡 <em>{item.tip}</em>
                </div>
              </div>
            ))}
          </div>

          {/* Proceed to Test Button */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '12px' }}>
            <button className="duo-btn duo-btn-green" onClick={startTest}>
              Start 10-Question Test <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* VIEW 3: TEST PHASE (10 Questions Quiz with Inline Teach Me First Hint) */}
      {mode === 'test' && currentLevel && quizQueue.length > 0 && (
        <div className="lesson-card">
          {/* Progress Header */}
          <div className="test-header">
            <button className="duo-btn duo-btn-secondary" style={{ padding: '6px 12px' }} onClick={() => setMode('map')}>
              <XCircle size={20} />
            </button>
            
            <div className="progress-bar-bg">
              <div 
                className="progress-bar-fill"
                style={{ width: `${((quizIndex + 1) / quizQueue.length) * 100}%` }}
              />
            </div>

            <div style={{ fontSize: '13px', fontWeight: '800', color: 'var(--duo-cyan)' }}>
              {quizIndex + 1} / {quizQueue.length}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--duo-rose)', fontWeight: '800' }}>
              <Heart size={20} fill="var(--duo-rose)" /> {hearts}
            </div>
          </div>

          {/* Question Display */}
          {(() => {
            const q = quizQueue[quizIndex];
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <h3 className="question-title">{q.question}</h3>
                  
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {/* Teach Me First Hint Button */}
                    {q.teachHint && (
                      <button 
                        className={`duo-btn ${showTeachHint ? 'duo-btn-purple' : 'duo-btn-secondary'}`}
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                        onClick={() => setShowTeachHint(!showTeachHint)}
                      >
                        <GraduationCap size={14} /> {showTeachHint ? 'Hide Hint' : 'Teach Concept'}
                      </button>
                    )}

                    {/* Retry Review Badge if pushed to queue */}
                    {q.isReview && (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(255, 75, 75, 0.15)', color: 'var(--duo-rose)', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: '700', flexShrink: 0 }}>
                        <Repeat size={14} /> Review Retry
                      </span>
                    )}
                  </div>
                </div>

                {/* TEACH ME FIRST INLINE HINT BOX */}
                {showTeachHint && q.teachHint && (
                  <div style={{ background: 'rgba(206, 130, 255, 0.12)', border: '1px solid var(--duo-purple)', padding: '14px 18px', borderRadius: 'var(--radius-md)', fontSize: '14px', color: 'var(--text-main)', display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <GraduationCap size={20} color="var(--duo-purple)" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <strong style={{ color: 'var(--duo-purple)', display: 'block', fontSize: '14px' }}>📖 Quick Concept Breakdown:</strong>
                      {q.teachHint}
                    </div>
                  </div>
                )}

                {/* Audio Prompt or Silent Workplace Prompt */}
                {q.targetAudio && (
                  <div className="audio-prompt-box">
                    <button 
                      className={`duo-btn ${isMuted ? 'duo-btn-secondary' : 'duo-btn-cyan'}`} 
                      onClick={() => speakJapanese(q.targetAudio)}
                      disabled={isMuted}
                    >
                      {isMuted ? <VolumeX size={24} /> : <Volume2 size={24} />} 
                      {isMuted ? 'Muted (Work Mode)' : 'Play Sound'}
                    </button>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      {isMuted ? (
                        <span style={{ fontSize: '15px', color: 'var(--duo-purple)', fontWeight: '700' }}>
                          Target Phrase: "{q.targetAudio}"
                        </span>
                      ) : (
                        <span style={{ fontSize: '15px', color: 'var(--text-muted)' }}>
                          Tap to listen to the Japanese sentence out loud!
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Question Type 1: Word Block Sentence Assembly */}
                {q.type === 'word_arrange' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="word-blocks-slots">
                      {arrangedWords.length === 0 ? (
                        <span style={{ color: 'var(--text-subtle)', fontSize: '14px' }}>Tap blocks below to build the sentence...</span>
                      ) : (
                        arrangedWords.map((word, wIdx) => (
                          <span 
                            key={wIdx} className="word-block-chip"
                            onClick={() => handleWordTap(word)}
                            style={{ cursor: 'pointer', background: 'var(--duo-cyan)', borderColor: '#1899d6', color: '#fff' }}
                          >
                            {word}
                          </span>
                        ))
                      )}
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                      {q.words.map((word, wIdx) => {
                        const isUsed = arrangedWords.includes(word);
                        return (
                          <button
                            key={wIdx}
                            className={`word-block-chip ${isUsed ? 'used' : ''}`}
                            onClick={() => handleWordTap(word)}
                          >
                            {word}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Question Type 2: Multiple Choice */}
                {q.options && (
                  <div className="options-grid">
                    {q.options.map((opt, oIdx) => {
                      let statusClass = '';
                      if (selectedOption === oIdx) statusClass = 'selected';
                      if (quizStatus && oIdx === q.correctIndex) statusClass = 'correct';
                      if (quizStatus === 'wrong' && selectedOption === oIdx) statusClass = 'wrong';

                      return (
                        <button
                          key={oIdx}
                          className={`option-card ${statusClass}`}
                          onClick={() => quizStatus === null && setSelectedOption(oIdx)}
                        >
                          <span style={{ width: '24px', height: '24px', borderRadius: '50%', border: '2px solid rgba(0,0,0,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>
                            {oIdx + 1}
                          </span>
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Submit / Continue Button */}
                {quizStatus === null ? (
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                    <button 
                      className="duo-btn duo-btn-green"
                      disabled={q.type === 'word_arrange' ? arrangedWords.length === 0 : selectedOption === null}
                      style={{ opacity: (q.type === 'word_arrange' ? arrangedWords.length === 0 : selectedOption === null) ? 0.5 : 1 }}
                      onClick={checkAnswer}
                    >
                      Check Answer
                    </button>
                  </div>
                ) : (
                  <div className={`feedback-footer ${quizStatus}`}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      {quizStatus === 'correct' ? <CheckCircle2 size={32} /> : <XCircle size={32} />}
                      <div>
                        <div style={{ fontSize: '18px', fontWeight: '800' }}>
                          {quizStatus === 'correct' ? 'Excellent! Correct!' : 'Not quite right!'}
                        </div>
                        <div style={{ fontSize: '13px', opacity: 0.9 }}>
                          {quizStatus === 'correct' ? '+10 XP Gained!' : 'Review the hint above. Added to test end for retry!'}
                        </div>
                      </div>
                    </div>

                    <button className="duo-btn duo-btn-green" onClick={nextQuestion}>
                      Continue <ArrowRight size={18} />
                    </button>
                  </div>
                )}

              </div>
            );
          })()}
        </div>
      )}

      {/* PARTICLE MASTER GUIDE MODAL */}
      {showParticleGuide && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: '640px', textTransform: 'none', textAlign: 'left', alignItems: 'stretch' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Info color="var(--duo-purple)" size={28} />
                <h2 style={{ fontSize: '24px', fontWeight: '800' }}>Japanese Particle Master Guide</h2>
              </div>
              <button className="duo-btn duo-btn-secondary" style={{ padding: '6px 12px' }} onClick={() => setShowParticleGuide(false)}>
                <XCircle size={18} />
              </button>
            </div>

            <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
              Why do we use <strong>wa, ga, wo, ni, de</strong>? Particles connect words together to give them grammatical meaning!
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '420px', overflowY: 'auto', paddingRight: '6px' }}>
              {PARTICLE_GUIDE.map((p, pIdx) => (
                <div key={pIdx} style={{ background: 'rgba(0,0,0,0.04)', border: '1px solid var(--border-color)', padding: '16px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: '800', color: 'var(--duo-rose)', background: 'rgba(255, 75, 75, 0.15)', padding: '4px 10px', borderRadius: '8px' }}>
                      {p.symbol}
                    </span>
                    <strong style={{ fontSize: '16px', color: 'var(--duo-cyan)' }}>{p.name}</strong>
                  </div>

                  <div style={{ fontSize: '14px', fontWeight: '600' }}>
                    💡 <strong>WHY USE IT:</strong> {p.why}
                  </div>

                  <div style={{ fontSize: '13px', background: 'rgba(28, 176, 246, 0.08)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid var(--duo-cyan)' }}>
                    <strong>Example:</strong> <span style={{ fontFamily: 'var(--font-heading)', fontWeight: '700' }}>{p.example}</span> $\rightarrow$ <em>{p.meaning}</em>
                  </div>

                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    ⚡ <strong>Rule / Tip:</strong> {p.rule} ({p.comparison})
                  </div>
                </div>
              ))}
            </div>

            <button className="duo-btn duo-btn-purple" style={{ width: '100%', marginTop: '8px' }} onClick={() => setShowParticleGuide(false)}>
              Got it! Back to Learning
            </button>
          </div>
        </div>
      )}

      {/* CELEBRATION MODAL (Test Passed) */}
      {showCelebration && (
        <div className="modal-overlay">
          <div className="modal-card">
            <Award size={64} color="var(--duo-gold)" />
            <h2 style={{ fontSize: '28px', fontWeight: '800' }}>Level Passed!</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '15px' }}>
              Awesome job! You mastered all 10 questions including review retries.
            </p>

            <div className="star-rating">
              <Star size={32} fill="var(--duo-gold)" color="var(--duo-gold)" />
              <Star size={32} fill="var(--duo-gold)" color="var(--duo-gold)" />
              <Star size={32} fill="var(--duo-gold)" color="var(--duo-gold)" />
            </div>

            <div style={{ display: 'flex', gap: '16px', background: 'rgba(0,0,0,0.05)', padding: '12px 24px', borderRadius: 'var(--radius-md)' }}>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>XP GAINED</div>
                <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--duo-gold)' }}>+100 XP</div>
              </div>
              <div style={{ borderLeft: '1px solid var(--border-color)' }} />
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>QUESTIONS</div>
                <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--duo-green)' }}>10 / 10</div>
              </div>
            </div>

            <button className="duo-btn duo-btn-green" style={{ width: '100%' }} onClick={finishLevel}>
              Continue Trail
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
