# Chatbot Conversation Modes

The enhanced chatbot now supports multiple conversation modes for different types of interactions. Each mode provides a distinct personality and approach to conversations.

## Available Modes

### 1. Critique Mode
**Command:** `critique text`
- Provides detailed critiques and constructive feedback
- Follows a structured approach with thinking, critique, and output sections
- Professional and analytical tone
- Best for reviewing content and getting improvement suggestions

### 2. Reflecting Mode
**Command:** `reflect on text`
- Offers detailed, step-by-step responses
- Uses a thinking process with reflection sections
- Analytical and formal tone
- Best for complex problem-solving and logical reasoning

### 3. Casual Mode
**Command:** `casual chat`
- Friendly and easygoing conversation style
- Uses informal language and contractions
- Shows personality and is relatable
- Can use emojis when appropriate
- Best for relaxed, informal conversations

### 4. Professional Mode
**Command:** `professional chat`
- Formal and respectful communication
- Clear and concise responses
- Well-structured with proper formatting
- Business-appropriate language
- Best for formal discussions and professional contexts

### 5. Creative Mode
**Command:** `creative brainstorm`
- Innovative and original responses
- Uses vivid descriptions and figurative language
- Encourages brainstorming and out-of-the-box thinking
- Inspiring and playful
- Best for creative projects and idea generation

### 6. Analytical Mode
**Command:** `analytical analysis`
- Logical and methodical approach
- Data-driven and evidence-based
- Structured with clear reasoning steps
- Objective and impartial
- Best for data analysis and logical evaluation

## How to Use

### Setting a Mode
You can set a conversation mode using specific commands:

```
> casual chat
> professional chat
> creative brainstorm
> analytical analysis
> critique text
> reflect on text
```

### Starting a Conversation
You can also start a conversation with a specific mode:

```
> chat with casual mode
> chat with professional mode
```

### Exiting Conversation Mode
To exit conversation mode and return to normal command processing:

```
> exit chat
```

### Using Conversation Mode
Once a mode is set, all subsequent input (that isn't a recognized command) will be processed as conversation with the chatbot in that mode.

Example:
```
> casual chat
[Success] Casual mode enabled.

> Hi there! How's your day going?
[Chatbot responds in casual mode]

> exit chat
[Success] Conversation mode disabled.
```

## Mode Switching
You can switch between modes at any time by using a different mode command. This allows you to change the conversation style as needed for different topics or purposes.