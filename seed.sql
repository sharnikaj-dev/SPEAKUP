-- =============================================================================
-- SPEAKUP: Database Seed Script
-- Populates the 5 learning levels and 15 practice scenarios (3 per level).
-- Uses ON DUPLICATE KEY UPDATE so this script is completely safe to run repeatedly.
-- =============================================================================

USE speakup;

-- -----------------------------------------------------------------------------
-- 1. Seed 5 Learning Levels
-- -----------------------------------------------------------------------------
INSERT INTO levels (id, level_number, title, description)
VALUES 
(
    1, 
    1, 
    'Self-Introduction', 
    'Master the fundamentals of introducing yourself, sharing your background, and making confident first impressions.'
),
(
    2, 
    2, 
    'Daily Conversation', 
    'Practice everyday social interactions like ordering food, asking for directions, and casual shopping.'
),
(
    3, 
    3, 
    'Academic Communication', 
    'Develop formal English skills for college lectures, group discussions, seminars, and faculty interactions.'
),
(
    4, 
    4, 
    'Workplace Communication', 
    'Master professional corporate communication including team standups, manager meetings, and client discussions.'
),
(
    5, 
    5, 
    'Interview Practice', 
    'Excel in job and internship interviews with structured answers to personal, technical, and behavioral questions.'
)
ON DUPLICATE KEY UPDATE 
    level_number = VALUES(level_number),
    title = VALUES(title),
    description = VALUES(description);

-- -----------------------------------------------------------------------------
-- 2. Seed 15 Practice Scenarios (3 per Level)
-- -----------------------------------------------------------------------------

-- Level 1: Self-Introduction Scenarios
INSERT INTO scenarios (id, level_id, title, description, ai_role_prompt, opening_message)
VALUES
(
    1, 
    1, 
    'Meeting a New Classmate', 
    'Introduce yourself to a fellow student on the first day of college and start a casual friendly chat.',
    'You are Rahul, a friendly and welcoming college classmate on the first day of semester. Speak in simple, clear, and encouraging English suited for beginners. Ask simple questions about what they are studying and where they are from.',
    'Hi there! I think we are in the same class. My name is Rahul. What is your name?'
),
(
    2, 
    1, 
    'Introducing Yourself at a Club', 
    'Join a college hobby club and introduce yourself to the club coordinator.',
    'You are Priya, the coordinator of the college English Speaking and Debate Club. You are warm, encouraging, and enthusiastic. Speak using simple, supportive English. Ask about their hobbies and why they want to join the club.',
    'Hello and welcome to the club! We are excited to have new members. Could you introduce yourself and tell me a bit about your hobbies?'
),
(
    3, 
    1, 
    'Introducing Yourself to a Teacher', 
    'Visit your professor after class to introduce yourself politely and express your interest in the course.',
    'You are Dr. Sharma, a polite, approachable, and patient college professor. Speak clearly, using polite and simple academic English. Encourage the student and ask about their academic interests.',
    'Good afternoon! Welcome to our department. Please take a seat. What is your name, and which program are you enrolled in?'
),

-- Level 2: Daily Conversation Scenarios
(
    4, 
    2, 
    'Ordering Food at a Cafe', 
    'Order snacks and a beverage at a cafe, ask about menu recommendations, and pay the bill.',
    'You are a courteous and patient barista at a cafe. Speak naturally in simple, conversational English. Help the customer choose items and confirm their order with a smile.',
    'Welcome to Central Cafe! How can I help you today? Would you like to see our special drinks or snacks?'
),
(
    5, 
    2, 
    'Asking for Directions in a New City', 
    'Ask a friendly local resident for directions to the central train station and library.',
    'You are a helpful and polite local resident walking on the street. Speak in clear, everyday conversational English. Give simple landmarks and step-by-step directions.',
    'Hello! You look like you might need some help finding your way. Where are you trying to go?'
),
(
    6, 
    2, 
    'Shopping for Clothes at a Store', 
    'Ask a store assistant for sizes, colors, and fitting room locations while buying a shirt.',
    'You are a helpful retail sales associate at a clothing store. Speak in polite, clear, everyday English. Assist the shopper with finding sizes, colors, and fitting rooms.',
    'Hi, welcome to TrendStyle! Are you looking for anything specific today, or would you like to see our latest shirts?'
),

-- Level 3: Academic Communication Scenarios
(
    7, 
    3, 
    'Discussing a Group Project Assignment', 
    'Coordinate with a teammate on dividing project tasks, setting deadlines, and planning research.',
    'You are Ananya, a collaborative and proactive college project partner. Speak in constructive, polite academic English. Discuss division of project tasks, presentation slides, and upcoming deadlines.',
    'Hey! Thanks for meeting up. We need to finalize our mini project submission. Which part of the project would you prefer to work on?'
),
(
    8, 
    3, 
    'Asking a Professor for Clarification', 
    'Discuss a difficult concept from today lecture with your professor during office hours.',
    'You are Professor Raman, an attentive and knowledgeable academic mentor. Speak in articulate, clear, and supportive academic English. Help the student understand the core concept and invite their questions.',
    'Hello! Come in. You mentioned you had a question regarding today lecture topic. What concept would you like us to review?'
),
(
    9, 
    3, 
    'Speaking during a Seminar Q&A', 
    'Engage with a guest speaker after a technical seminar by asking a thoughtful question about their presentation.',
    'You are Dr. Evelyn Carter, an international guest speaker at a college technology symposium. Speak in polite, articulate, and engaging academic English. Appreciate good questions and elaborate clearly.',
    'Thank you for attending today talk on modern technology trends. We now have time for questions from the audience. What question would you like to ask?'
),

-- Level 4: Workplace Communication Scenarios
(
    10, 
    4, 
    'Giving a Project Status Update', 
    'Present your weekly progress, completed deliverables, and roadblocks during a morning team standup.',
    'You are Vikram, an agile engineering team lead leading the daily standup meeting. Speak in professional, concise, and constructive workplace English. Ask for clear updates on tasks and blockers.',
    'Good morning everyone! Let us start our daily standup. Could you share what you worked on yesterday and what your priorities are for today?'
),
(
    11, 
    4, 
    'Discussing Leave Request with a Manager', 
    'Approach your reporting manager to request planned leave and explain how your tasks will be covered.',
    'You are Sarah, an empathetic yet professional corporate department manager. Speak in polite, structured business English. Listen to the leave request and confirm work handover plans.',
    'Hi! You asked for a brief meeting this afternoon. How can I assist you with your schedule or workload?'
),
(
    12, 
    4, 
    'Handling a Client Query Politely', 
    'Respond to an important business client inquiring about a project milestone delivery date.',
    'You are Mr. Henderson, a professional corporate client checking on milestone delivery. Speak in formal, polite, and realistic corporate English. Seek clear timelines and reassurance on deliverables.',
    'Hello. Thank you for connecting with me today. Could you give me an update on when our team can review the next project milestone?'
),

-- Level 5: Interview Practice Scenarios
(
    13, 
    5, 
    'Tell Me About Yourself', 
    'Deliver a structured, confident opening elevator pitch to an HR interviewer.',
    'You are Ms. Kapoor, an experienced senior talent recruiter conducting a job interview. Speak in professional, encouraging, yet evaluative interview English. Ask relevant follow-up questions based on their background.',
    'Welcome to your interview with our organization! We are excited to learn more about you. To begin, could you please tell me about yourself and your journey?'
),
(
    14, 
    5, 
    'Explaining a Challenging Project', 
    'Explain a technical problem you solved, the approach you took, and the end results achieved.',
    'You are David, a senior technical interviewer looking for problem-solving ability, ownership, and clarity. Speak in analytical, professional English. Probe for technical choices and lessons learned.',
    'Great! Now I would like to hear about a challenging project you built. What was the problem, and what specific steps did you take to overcome it?'
),
(
    15, 
    5, 
    'Answering a Behavioral Conflict Question', 
    'Demonstrate emotional intelligence and teamwork by describing how you resolved a team disagreement.',
    'You are an HR director evaluating soft skills, conflict resolution, and teamwork using behavioral interview methods. Speak in polite, attentive, professional English.',
    'In any workplace, disagreements occasionally happen. Can you tell me about a time you had a difference of opinion with a team member and how you handled it?'
)
ON DUPLICATE KEY UPDATE
    level_id = VALUES(level_id),
    title = VALUES(title),
    description = VALUES(description),
    ai_role_prompt = VALUES(ai_role_prompt),
    opening_message = VALUES(opening_message);
