import express from 'express';
import cors from 'cors';
import { OpenAI } from 'openai';
import dotenv from 'dotenv';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

// Get __dirname equivalent in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env file in project root
dotenv.config({ path: path.resolve(__dirname, '..', '.env') });

const app = express();
const port = 5000;

// Simplified retry configuration for better reliability
const MAX_RETRIES = 3;
const INITIAL_BACKOFF_MS = 1000; // Start with 1 second
const MAX_BACKOFF_MS = 10000; // Maximum 10 seconds
const REQUEST_TIMEOUT_MS = 30000; // 30 second timeout

app.use(cors());
app.use(express.json());

// Validate API key on startup
if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'your_openai_api_key_here') {
  console.error('❌ OPENAI_API_KEY not found or still contains placeholder value');
  console.error('Please update your .env file with a valid OpenAI API key');
  console.error('Get your API key from: https://platform.openai.com/api-keys');
  process.exit(1);
}

console.log('✅ OpenAI API key loaded successfully');

// Simplified OpenAI client configuration
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  timeout: REQUEST_TIMEOUT_MS,
  maxRetries: 0, // We'll handle retries manually
});

// Helper function to sleep for a given number of milliseconds
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Simplified retry mechanism with better error reporting
const callOpenAIWithRetry = async (messages, temperature = 0.7) => {
  let lastError;
  
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    try {
      console.log(`🤖 Attempt ${attempt + 1}/${MAX_RETRIES} - Sending request to OpenAI...`);
      
      const completion = await openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: messages,
        temperature: temperature,
      });
      
      console.log(`✅ OpenAI request successful on attempt ${attempt + 1}`);
      return completion;
      
    } catch (error) {
      lastError = error;
      console.error(`❌ Attempt ${attempt + 1} failed:`, error.message);
      
      // Check for specific error types
      if (error.status === 401 || error.code === 'invalid_api_key') {
        console.error('❌ Invalid API key detected');
        throw new Error('Invalid OpenAI API key. Please check your .env file.');
      }
      
      if (error.status === 429 || error.code === 'rate_limit_exceeded') {
        console.error('❌ Rate limit exceeded');
        throw new Error('OpenAI API rate limit exceeded. Please try again later.');
      }
      
      if (error.status === 402 || error.code === 'insufficient_quota') {
        console.error('❌ Insufficient quota');
        throw new Error('OpenAI API quota exceeded. Please check your billing.');
      }
      
      // Check if this is a retryable error (network/connection issues)
      const isRetryable = (
        error.code === 'ECONNRESET' ||
        error.code === 'ENOTFOUND' ||
        error.code === 'ECONNREFUSED' ||
        error.code === 'ETIMEDOUT' ||
        error.code === 'ENETUNREACH' ||
        error.code === 'EHOSTUNREACH' ||
        error.message?.includes('fetch failed') ||
        error.message?.includes('network') ||
        error.message?.includes('timeout') ||
        error.status >= 500 // Server errors
      );
      
      // Don't retry on non-retryable errors
      if (!isRetryable) {
        console.error(`❌ Non-retryable error: ${error.message}`);
        throw error;
      }
      
      // If this was the last attempt, throw a descriptive error
      if (attempt === MAX_RETRIES - 1) {
        console.error(`❌ All ${MAX_RETRIES} attempts failed`);
        throw new Error(`Connection to OpenAI failed after ${MAX_RETRIES} attempts. This may be due to network issues or OpenAI service unavailability. Please check your internet connection and try again.`);
      }
      
      // Calculate backoff time
      const backoffTime = Math.min(INITIAL_BACKOFF_MS * Math.pow(2, attempt), MAX_BACKOFF_MS);
      console.log(`⏳ Waiting ${backoffTime}ms before retry...`);
      
      await sleep(backoffTime);
    }
  }
  
  throw lastError;
};

// Helper function to get base directory for data files (project root)
const getBaseDir = () => path.resolve(__dirname, '..');

// Helper for capitalizing first letter
const capitalizeFirstLetter = (string) => {
  return string.charAt(0).toUpperCase() + string.slice(1);
};

// Load prompt template
const loadPromptTemplate = () => {
  const promptPath = path.join(getBaseDir(), 'src', 'data', 'prompts', 'interrogation_prompt.txt');
  if (!fs.existsSync(promptPath)) {
    console.error(`❌ Prompt template not found at: ${promptPath}`);
    throw new Error('Prompt template file not found');
  }
  return fs.readFileSync(promptPath, 'utf-8');
};

// Load suspect data
const loadSuspectData = (name) => {
  const suspectPath = path.join(getBaseDir(), 'src', 'data', 'suspects', `${name.toLowerCase()}.json`);
  if (fs.existsSync(suspectPath)) {
    try {
      return JSON.parse(fs.readFileSync(suspectPath, 'utf-8'));
    } catch (error) {
      console.error(`❌ Error parsing suspect data for ${name}:`, error);
      return {};
    }
  }
  console.warn(`⚠️ Suspect data not found for: ${name}`);
  return {};
};

// Load clue data - FIXED VERSION
const loadClueData = (day, suspect) => {
  const baseDir = getBaseDir();
  
  // Try both day 1 and day1 format
  const dayFormats = [`day${day}`, `day ${day}`];
  
  for (const dayFormat of dayFormats) {
    const clueDir = path.join(baseDir, 'src', 'data', 'clues', dayFormat);
    
    // Check if the directory exists
    if (!fs.existsSync(clueDir)) {
      console.log(`📁 Directory not found: ${clueDir}`);
      continue;
    }
    
    try {
      // Read all files in the directory
      const files = fs.readdirSync(clueDir);
      console.log(`📂 Found files in ${dayFormat}:`, files);
      
      // Look for files that start with the suspect name (case-insensitive)
      const suspectLower = suspect.toLowerCase();
      const matchingFiles = files.filter(file => {
        const fileLower = file.toLowerCase();
        return fileLower.startsWith(suspectLower) && (fileLower.endsWith('.json') || fileLower.endsWith('.txt'));
      });
      
      console.log(`🔍 Matching files for ${suspect}:`, matchingFiles);
      
      if (matchingFiles.length > 0) {
        // Use the first matching file
        const fileName = matchingFiles[0];
        const filePath = path.join(clueDir, fileName);
        
        try {
          if (fileName.toLowerCase().endsWith('.json')) {
            const fileContent = fs.readFileSync(filePath, 'utf-8');
            const data = JSON.parse(fileContent);
            const clueText = data.clue || data.text || data.content || 'No clue text found in JSON';
            console.log(`✅ Loaded JSON clue for ${suspect}: ${clueText}`);
            return `🧩 Clue about ${capitalizeFirstLetter(suspect)}: ${clueText}`;
          } else { // .txt file
            const clue = fs.readFileSync(filePath, 'utf-8').trim();
            console.log(`✅ Loaded TXT clue for ${suspect}: ${clue}`);
            return `🧩 Clue about ${capitalizeFirstLetter(suspect)}: ${clue}`;
          }
        } catch (error) {
          console.error(`❌ Error reading clue file ${filePath}:`, error);
        }
      }
    } catch (error) {
      console.error(`❌ Error reading directory ${clueDir}:`, error);
    }
  }
  
  console.log(`⚠️ No clue files found for ${suspect} on day ${day}`);
  return `No new clues for ${capitalizeFirstLetter(suspect)} today.`;
};

// API endpoint for asking questions with improved error handling
app.post('/api/ask', async (req, res) => {
  const { suspect, question } = req.body;

  console.log(`📝 Received question for ${suspect}: ${question}`);

  if (!suspect || !question) {
    return res.status(400).json({ error: 'Missing suspect or question' });
  }

  try {
    const promptTemplate = loadPromptTemplate();
    const data = loadSuspectData(suspect);

    const backstory = data.backstory || '';
    const timeline = data.timeline || {};
    const relationship = data.relationship_to_victim || 'Unknown relationship';
    const tone = data.tone || 'neutral';

    const filledPrompt = promptTemplate.replace(/{name}/g, capitalizeFirstLetter(suspect))
                                     .replace(/{question}/g, question)
                                     .replace(/{tone}/g, tone)
                                     .replace(/{backstory}/g, backstory)
                                     .replace(/{time_range}/g, timeline.time_range || '')
                                     .replace(/{location}/g, timeline.claimed_location || timeline.location || '')
                                     .replace(/{relationship_to_victim}/g, relationship);

    const systemMessage = {
      role: 'system',
      content: 'You are a detective AI assistant. Your task is to help generate responses for a character in a murder mystery interrogation.',
    };
    const userMessage = {
      role: 'user',
      content: filledPrompt,
    };

    // Use the retry mechanism for the OpenAI API call
    const completion = await callOpenAIWithRetry([systemMessage, userMessage], 0.7);

    const response = completion.choices[0].message.content.trim();
    console.log(`✅ Generated response for ${suspect}`);

    res.json({ response });
  } catch (error) {
    console.error('❌ Error generating response:', error);
    
    // Return the actual error message from our retry mechanism
    res.status(500).json({ 
      error: `Error generating response: ${error.message}` 
    });
  }
});

// API endpoint for loading clues
app.get('/api/clue', (req, res) => {
  const day = parseInt(req.query.day);
  const suspect = req.query.suspect;

  console.log(`🔍 Loading clue for day ${day}, suspect: ${suspect}`);

  if (isNaN(day) || !suspect) {
    return res.status(400).json({ error: 'Missing or invalid day or suspect parameter' });
  }

  try {
    const clue = loadClueData(day, suspect);
    console.log(`✅ Loaded clue for ${suspect}: ${clue}`);
    res.json({ clue });
  } catch (error) {
    console.error('❌ Error loading clue:', error);
    res.status(500).json({ error: `Error loading clue: ${error.message}` });
  }
});

// Health check endpoint
app.get('/health', async (req, res) => {
  const healthData = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    openai_configured: !!(process.env.OPENAI_API_KEY && process.env.OPENAI_API_KEY !== 'your_openai_api_key_here'),
    server_version: '1.2.0',
    retry_config: {
      max_retries: MAX_RETRIES,
      initial_backoff_ms: INITIAL_BACKOFF_MS,
      max_backoff_ms: MAX_BACKOFF_MS,
      request_timeout_ms: REQUEST_TIMEOUT_MS
    }
  };

  // Optional: Test OpenAI connection if requested
  if (req.query.test_openai === 'true' && healthData.openai_configured) {
    try {
      console.log('🔍 Testing OpenAI connection...');
      const testCompletion = await callOpenAIWithRetry([
        { role: 'user', content: 'Say "OK" if you can hear me.' }
      ], 0);
      healthData.openai_test = 'success';
      healthData.openai_response = testCompletion.choices[0].message.content.trim();
      console.log('✅ OpenAI connection test successful');
    } catch (error) {
      console.error('❌ OpenAI connection test failed:', error.message);
      healthData.openai_test = 'failed';
      healthData.openai_error = error.message;
    }
  }

  res.json(healthData);
});

app.listen(port, () => {
  console.log(`🚀 Node.js API server listening at http://localhost:${port}`);
  console.log(`📡 Health check available at http://localhost:${port}/health`);
  console.log(`🔑 OpenAI API key: ${process.env.OPENAI_API_KEY && process.env.OPENAI_API_KEY !== 'your_openai_api_key_here' ? 'Configured' : 'Missing or Invalid'}`);
  console.log(`🔄 Retry mechanism: ${MAX_RETRIES} attempts with exponential backoff`);
  console.log(`⏱️  Request timeout: ${REQUEST_TIMEOUT_MS}ms`);
  
  if (!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'your_openai_api_key_here') {
    console.log(`\n⚠️  WARNING: OpenAI API key is not properly configured!`);
    console.log(`   Please update your .env file with a valid API key from:`);
    console.log(`   https://platform.openai.com/api-keys\n`);
  } else {
    console.log(`\n💡 Tip: Test OpenAI connection with: curl "http://localhost:${port}/health?test_openai=true"\n`);
  }
});