#!/usr/bin/env python3
"""
OpenRouter Integration Demo

Demonstrates how to configure and use OpenRouter API for enhanced AI-powered 
LinkedIn bio generation in the RepoReadme application.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from openrouter_service import OpenRouterAIService, OpenRouterConfig, EnhancementRequest
except ImportError:
    print("❌ Could not import OpenRouter service. Make sure you're running from the correct directory.")
    sys.exit(1)

def demo_openrouter_setup():
    """Demonstrate OpenRouter setup and configuration."""
    print("🤖 OpenRouter AI Integration Demo")
    print("=" * 60)
    print()
    
    print("📋 Setup Instructions:")
    print("1. Get your OpenRouter API key from: https://openrouter.ai/")
    print("2. Create an account and add credits to your balance")
    print("3. Copy your API key from the dashboard")
    print("4. In RepoReadme, navigate to '🤖 AI Bio' tab")
    print("5. Enable 'OpenRouter AI Enhancement'")
    print("6. Paste your API key and click 'Save'")
    print("7. Test the connection with the 'Test' button")
    print()
    
    print("🔧 Configuration Options:")
    print("• Model: Choose from GPT-3.5, GPT-4, Claude, Llama, etc.")
    print("• Temperature: Control creativity (0.0 = focused, 1.0 = creative)")
    print("• Enhancement Options: Creativity, readability, keywords")
    print()

def demo_openrouter_workflow():
    """Demonstrate the OpenRouter enhancement workflow."""
    print("🚀 OpenRouter Enhancement Workflow")
    print("=" * 60)
    print()
    
    print("Step 1: Generate Base Bio")
    print("   • Use the standard AI bio generator")
    print("   • Configure style, tone, and target role")
    print("   • Generate your initial bio version")
    print()
    
    print("Step 2: Configure OpenRouter")
    print("   • Enable OpenRouter AI Enhancement")
    print("   • Enter your API key and save")
    print("   • Select your preferred AI model")
    print("   • Test the connection")
    print()
    
    print("Step 3: Enhance with AI")
    print("   • Click '✨ Enhance with AI' button")
    print("   • AI analyzes and improves your bio")
    print("   • Get enhanced version + alternatives")
    print("   • Review improvement metrics")
    print()
    
    print("Step 4: Optimize and Export")
    print("   • Compare original vs enhanced versions")
    print("   • Choose your preferred bio")
    print("   • Export as text, guide, or copy to clipboard")
    print()

def demo_openrouter_models():
    """Demonstrate available OpenRouter models."""
    print("🧠 Available AI Models (Updated)")
    print("=" * 60)
    print()
    
    models = [
        # Budget-Friendly Models
        ("meta-llama/llama-3-8b-instruct", "~$0.0002", "Open source, very cost-effective, fast"),
        ("deepseek/deepseek-v3.2-exp", "~$0.0003", "Advanced reasoning, excellent value, 163K context"),
        ("anthropic/claude-3-haiku", "~$0.0004", "Fast Claude model, great balance of speed/quality"),
        
        # Balanced Models  
        ("openai/gpt-3.5-turbo", "~$0.002", "Most popular, reliable, good for most use cases"),
        ("google/gemini-2.5-flash", "~$0.003", "Ultra-fast (0.4s), massive 1M context window"),
        ("anthropic/claude-3-sonnet", "~$0.004", "High-quality writing, excellent for creative bios"),
        
        # Premium Models
        ("openai/gpt-4-turbo", "~$0.012", "Latest GPT-4, 128K context, improved performance"),
        ("anthropic/claude-sonnet-4.5", "~$0.013", "🆕 Latest Claude, 1M context, top reasoning"),
        ("openai/gpt-4", "~$0.027", "Original GPT-4, highest quality for complex tasks"),
        ("anthropic/claude-3-opus", "~$0.045", "Most capable Claude, best for complex writing"),
    ]
    
    print("💰 MODELS BY COST (Bio Enhancement):")
    print()
    
    for model, cost, description in models:
        provider = model.split('/')[0].title()
        if provider == "Meta-llama":
            provider = "Meta"
        elif provider == "Anthropic":
            provider = "Anthropic"
        elif provider == "Openai":
            provider = "OpenAI"
        elif provider == "Google":
            provider = "Google"
        elif provider == "Deepseek":
            provider = "DeepSeek"
            
        print(f"� {cost:<8} | {provider:<10} | {model}")
        print(f"          {description}")
        print()
    
    print("🚀 NEW ADDITIONS:")
    print("• Claude Sonnet 4.5: Latest Anthropic model with 1M context")
    print("• DeepSeek V3.2: Advanced reasoning at ultra-low cost")  
    print("• Gemini 2.5 Flash: Google's fastest model (0.4s latency)")
    print()
    
    print("💡 Updated Recommendations:")
    print("• Ultra Budget: Llama-3-8b ($0.0002 per bio)")
    print("• Best Value: DeepSeek V3.2 ($0.0003 per bio)")
    print("• Most Popular: GPT-3.5-turbo ($0.002 per bio)")
    print("• Fastest: Gemini 2.5 Flash (0.4s response time)")
    print("• Highest Quality: Claude Sonnet 4.5 ($0.013 per bio)")
    print("• Creative Writing: Claude-3-sonnet ($0.004 per bio)")
    print()

def demo_enhancement_features():
    """Demonstrate enhancement features."""
    print("✨ Enhancement Features")
    print("=" * 60)
    print()
    
    print("🎨 Creativity Enhancement:")
    print("   • Adds engaging personality")
    print("   • Improves storytelling flow")
    print("   • Makes bio more memorable")
    print()
    
    print("📖 Readability Improvement:")
    print("   • Optimizes sentence structure")
    print("   • Improves clarity and flow")
    print("   • Ensures professional tone")
    print()
    
    print("🎯 Keyword Optimization:")
    print("   • Naturally integrates target keywords")
    print("   • Improves LinkedIn searchability")
    print("   • Maintains authentic voice")
    print()
    
    print("📊 Quality Metrics:")
    print("   • Enhancement score (0-100)")
    print("   • Readability improvement percentage")
    print("   • Engagement potential rating")
    print("   • Keyword optimization score")
    print()

def demo_cost_information():
    """Demonstrate cost information for OpenRouter."""
    print("💰 Updated Cost Information")
    print("=" * 60)
    print()
    
    print("OpenRouter Pricing (per bio enhancement):")
    print("┌─────────────────────────────┬──────────┬─────────────────────────┐")
    print("│ Model                       │ Cost     │ Best For                │")
    print("├─────────────────────────────┼──────────┼─────────────────────────┤")
    print("│ Llama-3-8b                  │ $0.0002  │ Ultra budget            │")
    print("│ DeepSeek V3.2 🆕            │ $0.0003  │ Best value + reasoning  │")
    print("│ Claude-3-haiku              │ $0.0004  │ Fast + quality          │")
    print("│ GPT-3.5-turbo               │ $0.002   │ Most reliable           │")
    print("│ Gemini 2.5 Flash 🆕         │ $0.003   │ Ultra-fast (0.4s)       │")
    print("│ Claude-3-sonnet             │ $0.004   │ Creative writing        │")
    print("│ GPT-4-turbo                 │ $0.012   │ Large context (128K)    │")
    print("│ Claude Sonnet 4.5 🆕        │ $0.013   │ Latest + best reasoning │")
    print("│ GPT-4                       │ $0.027   │ Premium quality         │")
    print("│ Claude-3-opus               │ $0.045   │ Most capable            │")
    print("└─────────────────────────────┴──────────┴─────────────────────────┘")
    print()
    
    print("💡 Smart Cost Strategies:")
    print("• Start testing: DeepSeek V3.2 ($0.0003)")
    print("• Daily use: GPT-3.5-turbo ($0.002)")  
    print("• Important bios: Claude Sonnet 4.5 ($0.013)")
    print("• Speed critical: Gemini 2.5 Flash ($0.003)")
    print("• Creative content: Claude-3-sonnet ($0.004)")
    print()
    
    print("🆕 What's New:")
    print("• Claude Sonnet 4.5: 1M context, best reasoning")
    print("• DeepSeek V3.2: 163K context, amazing value")
    print("• Gemini 2.5 Flash: 1M context, 0.4s speed")
    print()
    
    print("📊 Performance Comparison:")
    print("• Fastest: Gemini 2.5 Flash (0.4s latency)")
    print("• Best Value: DeepSeek V3.2 (advanced + cheap)")
    print("• Largest Context: Claude Sonnet 4.5 (1M tokens)")
    print("• Most Popular: GPT-3.5-turbo (proven reliable)")
    print("• Premium: Claude Sonnet 4.5 (latest + greatest)")
    print()
    
    print("🔒 Benefits vs Local/Free AI:")
    print("• Access to latest models (GPT-4, Claude-4.5)")
    print("• Professional-grade output quality")
    print("• Massive context windows (up to 1M tokens)")
    print("• Sub-second response times")
    print("• No hardware requirements")
    print("• Always up-to-date models")
    print("• Pay-per-use (no subscriptions)")
    print()

def main():
    """Run the complete OpenRouter demo."""
    try:
        demo_openrouter_setup()
        demo_openrouter_workflow()
        demo_openrouter_models()
        demo_enhancement_features()
        demo_cost_information()
        
        print("🎉 OpenRouter Integration Complete!")
        print("=" * 60)
        print()
        print("🚀 Next Steps:")
        print("1. Get your OpenRouter API key: https://openrouter.ai/")
        print("2. Launch RepoReadme: python main_unified.py")
        print("3. Navigate to '🤖 AI Bio' tab")
        print("4. Configure OpenRouter settings")
        print("5. Generate and enhance your LinkedIn bio!")
        print()
        print("💡 Your GitHub repositories will be analyzed by AI to create")
        print("   authentic, compelling LinkedIn bios that showcase your")
        print("   real skills and achievements!")
        print()
        print("🔗 Useful Links:")
        print("• OpenRouter Dashboard: https://openrouter.ai/activity")
        print("• Model Pricing: https://openrouter.ai/docs#models")
        print("• API Documentation: https://openrouter.ai/docs")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    main()