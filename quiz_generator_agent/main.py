# |---------------------------------------------------------|
# |                                                         |
# |                 Give Feedback / Get Help                |
# | https://github.com/getbindu/Bindu/issues/new/choose    |
# |                                                         |
# |---------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""Quiz Generator Agent - AI quiz creation agent."""

import argparse
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from bindu.penguin.bindufy import bindufy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global agent instance
agent: Agent | None = None
_initialized = False
_init_lock = asyncio.Lock()


def load_config() -> dict[str, Any]:
    """Load agent configuration from project root."""
    # Try multiple possible locations for agent_config.json
    possible_paths = [
        Path(__file__).parent.parent / "agent_config.json",  # Project root
        Path(__file__).parent / "agent_config.json",  # Same directory as main.py
        Path.cwd() / "agent_config.json",  # Current working directory
    ]

    for config_path in possible_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return cast(dict[str, Any], json.load(f))
            except (PermissionError, json.JSONDecodeError) as e:
                print(f"⚠️  Error reading {config_path}: {type(e).__name__}")
                continue
            except Exception as e:
                print(f"⚠️  Unexpected error reading {config_path}: {type(e).__name__}")
                continue

    # If no config found or readable, create a minimal default
    print("⚠️  No agent_config.json found, using default configuration")
    return {
        "name": "quiz-generator-agent",
        "description": "AI quiz generator for educational content",
        "version": "1.0.0",
        "deployment": {
            "url": "http://127.0.0.1:3773",
            "expose": True,
            "protocol_version": "1.0.0",
            "proxy_urls": ["127.0.0.1"],
            "cors_origins": ["*"],
        },
        "environment_variables": [
            {"key": "OPENAI_API_KEY", "description": "OpenAI API key for LLM calls", "required": False},
            {"key": "OPENROUTER_API_KEY", "description": "OpenRouter API key for LLM calls", "required": False},
        ],
    }


async def initialize_agent() -> None:
    """Initialize the quiz generator agent with proper model."""
    global agent

    # Get API keys from environment
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("MODEL_NAME", "openai/gpt-4o")

    # Only support OpenRouter
    if openrouter_api_key:
        model = OpenRouter(
            id=model_name,
            api_key=openrouter_api_key,
            cache_response=True,
            supports_native_structured_outputs=True,
        )
        print(f"✅ Using OpenRouter model: {model_name}")
    else:
        # Define error message separately to avoid TRY003
        error_msg = (
            "OpenRouter API key required. Set OPENROUTER_API_KEY environment variable.\n"
            "Get your API key from: https://openrouter.ai/keys"
        )
        raise ValueError(error_msg)

    # Create the quiz generator agent
    agent = Agent(
        name="Quiz Generator Agent",
        model=model,
        instructions=dedent("""\
            You are an expert educational quiz creator with extensive experience in curriculum development.
            Your expertise encompasses: 📚

            - Educational assessment design
            - Question difficulty calibration
            - Cognitive learning theory
            - Subject matter expertise across disciplines
            - Bloom's taxonomy application
            - Inclusive question writing
            - Cultural sensitivity in content
            - Adaptive learning principles
            - Gamification of education
            - Assessment analytics and validation

            2. Question Design Phase ✏️
               - Create questions that test different cognitive levels
               - Balance multiple choice, true/false, and short answer questions
               - Write clear, unambiguous questions with correct answers
               - Include plausible distractors for multiple choice questions

            3. Quality Control Phase ✓
               - Verify all questions have correct answers and explanations
               - Ensure appropriate difficulty distribution
               - Check for cultural bias and accessibility
               - Validate question clarity and relevance

            4. Quiz Structure Phase 📋
               - Organize questions logically by topic or difficulty
               - Include time estimates and scoring guidelines
               - Add educational metadata and learning objectives

            Always:
            - Create questions that promote critical thinking
            - Provide detailed answer explanations
            - Include source attribution where applicable
            - Structure output professionally for educational use\
        """),
        expected_output=dedent("""\
            # {Quiz Title} 📝

            ## Quiz Overview
            {Brief description of quiz topic and objectives}

            **Difficulty Level:** {easy|medium|hard|mixed}
            **Number of Questions:** {count}
            **Estimated Time:** {minutes} minutes
            **Total Points:** {points}

            ## Questions

            ### Question 1: {Question Text}
            **Type:** {multiple_choice|true_false|short_answer}
            **Difficulty:** {easy|medium|hard}
            **Points:** {points}

            **Options:**
            a) {Option A}
            b) {Option B}
            c) {Option C}
            d) {Option D}

            **Correct Answer:** {a|b|c|d}
            **Explanation:** {detailed explanation}

            {Repeat for each question}

            ## Quiz Statistics
            - **Easy Questions:** {count}
            - **Medium Questions:** {count}
            - **Hard Questions:** {count}
            - **Multiple Choice:** {count}
            - **True/False:** {count}
            - **Short Answer:** {count}

            ## Answer Key
            {Complete answer key with explanations}

            ## Learning Objectives Met
            {List of educational goals achieved by this quiz}

            ---
            Quiz generated by AI Educational Assistant
            Designed for optimal learning outcomes
            Created: {current_date}
            Last Updated: {current_time}\
        """),
        add_datetime_to_context=True,
        markdown=True,
    )
    print("✅ Quiz Generator Agent initialized")


async def run_agent(messages: list[dict[str, str]]) -> Any:
    """Run the agent with the given messages."""
    global agent
    if not agent:
        # Define error message separately to avoid TRY003
        error_msg = "Agent not initialized"
        raise RuntimeError(error_msg)

    # Run the agent and get response
    return await agent.arun(messages)  # type: ignore[invalid-await]


async def handler(messages: list[dict[str, str]]) -> Any:
    """Handle incoming agent messages with lazy initialization."""
    global _initialized

    # Lazy initialization on first call
    async with _init_lock:
        if not _initialized:
            print("🔧 Initializing Quiz Generator Agent...")
            await initialize_agent()
            _initialized = True

    # Run the async agent
    result = await run_agent(messages)
    return result


async def cleanup() -> None:
    """Clean up any resources."""
    print("🧹 Cleaning up Quiz Generator Agent resources...")


def main() -> None:
    """Run the main entry point for the Quiz Generator Agent."""
    parser = argparse.ArgumentParser(description="Bindu Quiz Generator Agent")
    parser.add_argument(
        "--openai-api-key",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (env: OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--openrouter-api-key",
        type=str,
        default=os.getenv("OPENROUTER_API_KEY"),
        help="OpenRouter API key (env: OPENROUTER_API_KEY)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("MODEL_NAME", "openai/gpt-4o"),
        help="Model ID for OpenRouter (env: MODEL_NAME)",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to agent_config.json (optional)",
    )
    args = parser.parse_args()

    # Set environment variables if provided via CLI
    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
    if args.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = args.openrouter_api_key
    if args.model:
        os.environ["MODEL_NAME"] = args.model

    print("🤖 Quiz Generator Agent - AI Educational Content Creator")
    print("📚 Capabilities: Quiz generation, educational assessment design")

    # Load configuration
    config = load_config()

    try:
        # Bindufy and start the agent server
        print("🚀 Starting Bindu Quiz Generator Agent server...")
        print(f"🌐 Server will run on: {config.get('deployment', {}).get('url', 'http://127.0.0.1:3773')}")
        bindufy(config, handler)
    except KeyboardInterrupt:
        print("\n🛑 Quiz Generator Agent stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup on exit
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
