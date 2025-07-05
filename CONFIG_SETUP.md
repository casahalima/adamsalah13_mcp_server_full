# Configuration Setup

## Files

- `config.py` - Main configuration class (safe for git)
- `config_template.py` - Template without sensitive data (safe for git)
- `.env` - Environment variables with secrets (ignored by git)

## Setup Instructions

1. **Copy the template** (if you need a local config):
   ```bash
   cp config_template.py config_local.py
   ```

2. **Create .env file** with your secrets:
   ```env
   # OpenAI Agent (optional)
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Neo4j Database (optional)
   NEO4J_PASSWORD=your_neo4j_password
   
   # Ollama Agent (optional, uses local server)
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2
   ```

3. **Use environment variables** - The main `config.py` will automatically load from `.env`

## Security Notes

- Never commit `.env` files or config files with hardcoded passwords
- Use environment variables for all sensitive data
- The `config.py` file should only contain safe defaults and field definitions
