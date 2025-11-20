<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/18iqaeoWplJMVmc_vr6npD0SxOYx3jvKx

## Run Locally

**Prerequisites:**  Node.js

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure API keys in `.env.local`:
   
   **Option 1: Google Gemini** (Recommended for free tier)
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   Get your key from: https://makersuite.google.com/app/apikey
   
   **Option 2: Anthropic Claude**
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```
   Get your key from: https://console.anthropic.com/
   
   **Option 3: Azure OpenAI**
   ```bash
   AZURE_OPENAI_API_KEY=your_azure_api_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   ```
   Get your credentials from: https://portal.azure.com/

3. Run the app:
   ```bash
   npm run dev
   ```

## Supported AI Providers

This app supports multiple AI providers:
- **Google Gemini** - Free tier available, fast responses
- **Anthropic Claude** - High-quality reasoning, great for complex topics
- **Azure OpenAI** - Enterprise-grade, supports GPT-4 and other models

You can switch between providers using the provider selector in the sidebar. The app will automatically use the first available provider if no specific one is selected.
