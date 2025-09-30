#!/usr/bin/env python3
"""
OpenRouter AI Service

Integration with OpenRouter API for enhanced AI-powered content generation
in the RepoReadme application. Provides sophisticated bio enhancement,
content optimization, and natural language generation.
"""

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
import ssl
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

try:
    from .utils.logger import get_logger
    from .config.settings import SettingsManager
except ImportError:
    from utils.logger import get_logger
    from config.settings import SettingsManager


@dataclass
class ModelPricing:
    """Pricing information for OpenRouter models."""
    
    model_name: str
    input_price_per_1k: float  # Price per 1K input tokens
    output_price_per_1k: float  # Price per 1K output tokens
    context_length: int
    max_output: int
    description: str
    provider: str
    latency: float = 0.0  # Average latency in seconds
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for given token usage."""
        input_cost = (input_tokens / 1000) * self.input_price_per_1k
        output_cost = (output_tokens / 1000) * self.output_price_per_1k
        return input_cost + output_cost
    
    def estimate_bio_cost(self) -> float:
        """Estimate cost for typical bio enhancement (500 input, 300 output tokens)."""
        return self.estimate_cost(500, 300)


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API."""
    
    api_key: str = ""
    model: str = "openai/gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7
    base_url: str = "https://openrouter.ai/api/v1"
    
    # Bio enhancement settings
    enhance_creativity: bool = True
    improve_readability: bool = True
    optimize_keywords: bool = True
    add_personality: bool = True


@dataclass
class EnhancementRequest:
    """Request for bio enhancement."""
    
    original_bio: str
    target_style: str = "professional"
    target_role: str = "Software Engineer"
    target_industry: str = "technology"
    enhancement_type: str = "improve"  # improve, rewrite, optimize, personalize
    include_metrics: bool = True
    
    # Context information
    github_username: str = ""
    primary_languages: List[str] = None
    project_highlights: List[str] = None
    technical_achievements: List[str] = None
    
    def __post_init__(self):
        if self.primary_languages is None:
            self.primary_languages = []
        if self.project_highlights is None:
            self.project_highlights = []
        if self.technical_achievements is None:
            self.technical_achievements = []


@dataclass
class EnhancementResult:
    """Result of bio enhancement."""
    
    enhanced_bio: str
    enhancement_score: float = 0.0
    improvements_made: List[str] = None
    suggestions: List[str] = None
    
    # Quality metrics
    readability_improvement: float = 0.0
    engagement_improvement: float = 0.0
    keyword_optimization: float = 0.0
    
    # API metadata
    model_used: str = ""
    tokens_used: int = 0
    processing_time: float = 0.0
    
    # Accurate cost tracking
    actual_cost: float = 0.0
    estimated_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generation_id: str = ""
    cost_breakdown: Dict[str, float] = None
    
    def __post_init__(self):
        if self.improvements_made is None:
            self.improvements_made = []
        if self.suggestions is None:
            self.suggestions = []
        if self.cost_breakdown is None:
            self.cost_breakdown = {}


class OpenRouterAIService:
    """OpenRouter AI service for enhanced content generation."""
    
    def __init__(self, config: OpenRouterConfig = None):
        self.config = config or OpenRouterConfig()
        self.logger = get_logger()
        self.settings_manager = SettingsManager()
        
        # Model pricing database
        self._init_model_pricing()
        
        # Load settings if available
        self._load_settings()
        
        # Initialize robust HTTP session
        self._init_http_session()
        
        # Validate configuration
        if not self.config.api_key:
            # Don't warn during initialization, only when service is used
            pass
    
    def _init_http_session(self):
        """Initialize HTTP session with robust SSL and retry configuration."""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        # Create adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Configure SSL context to handle various SSL issues
        try:
            # Disable SSL warnings for problematic connections
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Set session timeout
            self.session.timeout = 60
            
            # Configure headers for better compatibility
            self.session.headers.update({
                'User-Agent': 'RepoReadme-AI-Bio-Generator/1.0',
                'Connection': 'keep-alive'
            })
            
        except Exception as e:
            self.logger.warning(f"SSL configuration warning: {e}")
    
    def _init_model_pricing(self):
        """Initialize model pricing information."""
        self.model_pricing = {
            # OpenAI Models
            "openai/gpt-3.5-turbo": ModelPricing(
                model_name="GPT-3.5 Turbo",
                input_price_per_1k=0.0015,
                output_price_per_1k=0.002,
                context_length=16385,
                max_output=4096,
                description="Fast, cost-effective, great for most use cases",
                provider="OpenAI",
                latency=1.2
            ),
            "openai/gpt-4": ModelPricing(
                model_name="GPT-4",
                input_price_per_1k=0.03,
                output_price_per_1k=0.06,
                context_length=8192,
                max_output=4096,
                description="High quality, better reasoning, more expensive",
                provider="OpenAI",
                latency=2.8
            ),
            "openai/gpt-4-turbo": ModelPricing(
                model_name="GPT-4 Turbo",
                input_price_per_1k=0.01,
                output_price_per_1k=0.03,
                context_length=128000,
                max_output=4096,
                description="Latest GPT-4 with improved performance and larger context",
                provider="OpenAI",
                latency=2.1
            ),
            
            # Anthropic Claude Models
            "anthropic/claude-3-haiku": ModelPricing(
                model_name="Claude 3 Haiku",
                input_price_per_1k=0.00025,
                output_price_per_1k=0.00125,
                context_length=200000,
                max_output=4096,
                description="Fast Claude model, excellent value",
                provider="Anthropic",
                latency=0.8
            ),
            "anthropic/claude-3-sonnet": ModelPricing(
                model_name="Claude 3 Sonnet",
                input_price_per_1k=0.003,
                output_price_per_1k=0.015,
                context_length=200000,
                max_output=4096,
                description="High-quality Claude, excellent writing",
                provider="Anthropic",
                latency=1.5
            ),
            "anthropic/claude-3-opus": ModelPricing(
                model_name="Claude 3 Opus",
                input_price_per_1k=0.015,
                output_price_per_1k=0.075,
                context_length=200000,
                max_output=4096,
                description="Most capable Claude model",
                provider="Anthropic",
                latency=2.3
            ),
            "anthropic/claude-sonnet-4.5": ModelPricing(
                model_name="Claude Sonnet 4.5",
                input_price_per_1k=0.003,  # ≤200K tokens
                output_price_per_1k=0.015,  # ≤200K tokens
                context_length=1000000,
                max_output=64000,
                description="Latest Claude with 1M context, exceptional reasoning",
                provider="Anthropic",
                latency=2.5
            ),
            
            # Meta Llama Models
            "meta-llama/llama-3-8b-instruct": ModelPricing(
                model_name="Llama 3 8B Instruct",
                input_price_per_1k=0.0001,
                output_price_per_1k=0.0001,
                context_length=8192,
                max_output=2048,
                description="Open source, fast, very cost-effective",
                provider="Meta",
                latency=0.6
            ),
            "meta-llama/llama-3-70b-instruct": ModelPricing(
                model_name="Llama 3 70B Instruct",
                input_price_per_1k=0.0009,
                output_price_per_1k=0.0009,
                context_length=8192,
                max_output=2048,
                description="Larger Llama model, better quality",
                provider="Meta",
                latency=1.8
            ),
            
            # DeepSeek Models
            "deepseek/deepseek-v3.2-exp": ModelPricing(
                model_name="DeepSeek V3.2 Exp",
                input_price_per_1k=0.00027,
                output_price_per_1k=0.00041,
                context_length=163800,
                max_output=65500,
                description="Advanced reasoning model, excellent value",
                provider="DeepSeek",
                latency=0.9
            ),
            
            # Google Gemini Models
            "google/gemini-2.5-flash": ModelPricing(
                model_name="Gemini 2.5 Flash",
                input_price_per_1k=0.0003,
                output_price_per_1k=0.0025,
                context_length=1050000,
                max_output=65500,
                description="Ultra-fast Google model with massive context",
                provider="Google",
                latency=0.4
            ),
        }
    
    def get_model_pricing(self, model_id: str) -> Optional[ModelPricing]:
        """Get pricing information for a model."""
        return self.model_pricing.get(model_id)
    
    def get_all_models_with_pricing(self) -> List[tuple]:
        """Get all models with their pricing information for display."""
        models = []
        for model_id, pricing in self.model_pricing.items():
            cost_estimate = pricing.estimate_bio_cost()
            models.append((
                model_id,
                pricing.model_name,
                pricing.description,
                f"${cost_estimate:.4f}",
                pricing.provider,
                f"{pricing.latency:.1f}s"
            ))
        return sorted(models, key=lambda x: float(x[3][1:]))  # Sort by cost
    
    def calculate_actual_cost(self, usage_data: Dict[str, int], model_id: str = None) -> Dict[str, Any]:
        """Calculate actual cost from API usage data."""
        model_id = model_id or self.config.model
        pricing = self.get_model_pricing(model_id)
        
        if not pricing or not usage_data:
            return {"error": "Missing pricing or usage data"}
        
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        total_tokens = usage_data.get("total_tokens", 0)
        
        # Calculate costs using actual token counts
        input_cost = pricing.estimate_cost(prompt_tokens, 0)
        output_cost = pricing.estimate_cost(0, completion_tokens)
        total_cost = input_cost + output_cost
        
        return {
            "model": pricing.model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "cost_formatted": f"${total_cost:.6f}",
            "cost_breakdown": {
                "input": f"${input_cost:.6f} ({prompt_tokens} tokens)",
                "output": f"${output_cost:.6f} ({completion_tokens} tokens)"
            }
        }
    
    def estimate_enhancement_cost(self, bio_text: str, model_id: str) -> Dict[str, Any]:
        """Estimate the cost of enhancing a bio with the specified model."""
        try:
            model_info = self.get_model_pricing(model_id)
            if not model_info:
                return {"error": f"Model {model_id} not found in pricing database"}
            
            # Estimate token counts for the bio enhancement
            prompt_text = f"Please enhance this LinkedIn bio: {bio_text}"
            estimated_input_tokens = len(prompt_text.split()) * 1.3  # Rough estimation
            estimated_output_tokens = len(bio_text.split()) * 2  # Expect roughly 2x output
            
            # Calculate estimated cost
            estimated_cost = model_info.estimate_cost(
                int(estimated_input_tokens), 
                int(estimated_output_tokens)
            )
            
            return {
                "model": model_id,
                "provider": model_info.provider,
                "cost_formatted": f"${estimated_cost:.6f}",
                "estimated_cost": estimated_cost,
                "estimated_input_tokens": int(estimated_input_tokens),
                "estimated_output_tokens": int(estimated_output_tokens),
                "input_cost_per_1k": model_info.input_price_per_1k,
                "output_cost_per_1k": model_info.output_price_per_1k
            }
            
        except Exception as e:
            return {"error": f"Cost estimation failed: {str(e)}"}
    
    def query_generation_stats(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Query generation stats for precise cost accounting."""
        if not self.is_configured() or not generation_id:
            return None
        
        try:
            url = f"{self.config.base_url}/generation?id={generation_id}"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Failed to query generation stats: {e}")
            return None
        """Estimate cost for enhancing a specific bio."""
        model_id = model_id or self.config.model
        pricing = self.get_model_pricing(model_id)
        
        if not pricing:
            return {"error": "Pricing information not available for this model"}
        
        # Estimate tokens (rough approximation: 1 token ≈ 0.75 words)
        words = len(bio_text.split())
        input_tokens = int(words / 0.75) + 200  # Add system prompt tokens
        output_tokens = 300  # Typical enhanced bio length
        
        cost = pricing.estimate_cost(input_tokens, output_tokens)
        
        return {
            "model": pricing.model_name,
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_cost": cost,
            "cost_formatted": f"${cost:.4f}",
            "provider": pricing.provider,
            "context_length": pricing.context_length,
            "max_output": pricing.max_output
        }
    
    def _load_settings(self):
        """Load OpenRouter settings from application settings."""
        try:
            settings = self.settings_manager.get_settings()
            
            if hasattr(settings, 'openrouter_api_key') and settings.openrouter_api_key:
                self.config.api_key = settings.openrouter_api_key
            
            if hasattr(settings, 'openrouter_model') and settings.openrouter_model:
                self.config.model = settings.openrouter_model
            
            if hasattr(settings, 'openrouter_max_tokens'):
                self.config.max_tokens = settings.openrouter_max_tokens
            
            if hasattr(settings, 'openrouter_temperature'):
                self.config.temperature = settings.openrouter_temperature
                
        except Exception as e:
            self.logger.debug(f"Could not load OpenRouter settings: {e}")
    
    def is_configured(self) -> bool:
        """Check if OpenRouter is properly configured."""
        return bool(self.config.api_key and self.config.api_key.strip())
    
    def test_connection(self) -> Dict[str, Any]:
        """Test OpenRouter API connection."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "OpenRouter API key not configured",
                "details": "Please add your OpenRouter API key in settings"
            }
        
        try:
            # Simple test request
            response = self._make_api_request(
                "Tell me you're working in 5 words.",
                max_tokens=20,
                temperature=0.1
            )
            
            if response and "choices" in response:
                return {
                    "success": True,
                    "model": self.config.model,
                    "response": response["choices"][0]["message"]["content"],
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0)
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid API response",
                    "details": "Check your API key and model configuration"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Failed to connect to OpenRouter API"
            }
    
    def enhance_linkedin_bio(self, request: EnhancementRequest) -> EnhancementResult:
        """Enhance LinkedIn bio using OpenRouter AI with fallback strategies."""
        if not self.is_configured():
            return self._create_fallback_enhancement(request)
        
        start_time = time.time()
        self.logger.info(f"🤖 Enhancing LinkedIn bio with OpenRouter AI ({self.config.model})")
        
        try:
            # Build enhancement prompt
            prompt = self._build_enhancement_prompt(request)
            
            # Make API request
            response = self._make_api_request(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            if not response or "choices" not in response:
                self.logger.warning("Invalid response from OpenRouter API, using fallback")
                return self._create_fallback_enhancement(request)
            
            # Parse enhanced bio
            enhanced_content = response["choices"][0]["message"]["content"]
            enhanced_bio = self._extract_bio_from_response(enhanced_content)
            
            # Get actual usage data
            usage_data = response.get("usage", {})
            generation_id = response.get("id", "")
            
            # Calculate metrics
            processing_time = time.time() - start_time
            total_tokens = usage_data.get("total_tokens", 0)
            
            # Calculate actual costs
            cost_info = self.calculate_actual_cost(usage_data, self.config.model)
            actual_cost = cost_info.get("total_cost", 0.0) if "error" not in cost_info else 0.0
            
            # Analyze improvements
            improvements = self._analyze_improvements(request.original_bio, enhanced_bio)
            
            result = EnhancementResult(
                enhanced_bio=enhanced_bio,
                enhancement_score=self._calculate_enhancement_score(request.original_bio, enhanced_bio),
                improvements_made=improvements["improvements"],
                suggestions=improvements["suggestions"],
                readability_improvement=improvements["readability_improvement"],
                engagement_improvement=improvements["engagement_improvement"],
                keyword_optimization=improvements["keyword_optimization"],
                model_used=self.config.model,
                tokens_used=total_tokens,
                processing_time=processing_time,
                actual_cost=actual_cost,
                estimated_cost=self._estimate_cost_for_request(request),
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                generation_id=generation_id,
                cost_breakdown=cost_info.get("cost_breakdown", {}) if "error" not in cost_info else {}
            )
            
            self.logger.info(f"✅ Bio enhancement complete ({processing_time:.2f}s, {total_tokens} tokens)")
            return result
            
        except Exception as e:
            self.logger.error(f"Bio enhancement failed: {e}")
            self.logger.info("🔄 Falling back to local enhancement")
            return self._create_fallback_enhancement(request)
    
    def generate_bio_alternatives(self, original_bio: str, count: int = 3) -> List[str]:
        """Generate alternative bio versions using OpenRouter AI."""
        if not self.is_configured():
            return []
        
        self.logger.info(f"🎭 Generating {count} bio alternatives with OpenRouter AI")
        
        alternatives = []
        
        for i in range(count):
            try:
                style_variations = ["professional", "creative", "technical", "conversational", "executive"]
                style = style_variations[i % len(style_variations)]
                
                prompt = f"""
Create a LinkedIn bio alternative based on this original bio. Make it {style} in style while maintaining the core message and achievements.

Original bio:
{original_bio}

Create a {style} alternative that:
1. Maintains the same key accomplishments
2. Uses a {style} tone and language
3. Optimizes for LinkedIn engagement
4. Stays authentic to the person's background

Alternative bio:
"""
                
                response = self._make_api_request(
                    prompt,
                    max_tokens=500,
                    temperature=0.8
                )
                
                if response and "choices" in response:
                    alternative = response["choices"][0]["message"]["content"].strip()
                    alternative = self._extract_bio_from_response(alternative)
                    alternatives.append(alternative)
                    
            except Exception as e:
                self.logger.warning(f"Failed to generate alternative {i+1}: {e}")
                continue
        
        self.logger.info(f"✅ Generated {len(alternatives)} bio alternatives")
        return alternatives
    
    def optimize_for_keywords(self, bio: str, target_keywords: List[str]) -> str:
        """Optimize bio for specific keywords using OpenRouter AI."""
        if not self.is_configured() or not target_keywords:
            return bio
        
        self.logger.info(f"🎯 Optimizing bio for keywords: {', '.join(target_keywords)}")
        
        try:
            prompt = f"""
Optimize this LinkedIn bio to naturally include these target keywords while maintaining readability and authenticity:

Target keywords: {', '.join(target_keywords)}

Original bio:
{bio}

Instructions:
1. Integrate keywords naturally into the existing content
2. Maintain the professional tone and message
3. Don't force keywords - only include where they fit naturally
4. Ensure the bio remains readable and engaging
5. Prioritize the most important keywords

Optimized bio:
"""
            
            response = self._make_api_request(
                prompt,
                max_tokens=600,
                temperature=0.5
            )
            
            if response and "choices" in response:
                optimized = response["choices"][0]["message"]["content"].strip()
                optimized = self._extract_bio_from_response(optimized)
                
                self.logger.info("✅ Bio keyword optimization complete")
                return optimized
            
        except Exception as e:
            self.logger.error(f"Keyword optimization failed: {e}")
        
        return bio
    
    def _build_enhancement_prompt(self, request: EnhancementRequest) -> str:
        """Build sophisticated enhancement prompt for OpenRouter API."""
        
        # Build rich context information
        context_info = self._build_context_section(request)
        
        # Get style-specific instructions
        style_instructions = self._get_style_specific_instructions(request.target_style)
        
        # Get enhancement type specific approach
        enhancement_approach = self._get_enhancement_approach(request.enhancement_type)
        
        # Build the main prompt with sophisticated instructions
        prompt = f"""
You are an elite LinkedIn profile strategist with 15+ years of experience crafting compelling professional narratives. You've helped thousands of {request.target_role}s in {request.target_industry} land their dream roles.

=== CONTEXT & BACKGROUND ===
{context_info}

=== ORIGINAL BIO TO ENHANCE ===
{request.original_bio}

=== ENHANCEMENT MISSION ===
{enhancement_approach}

=== STYLE REQUIREMENTS ===
{style_instructions}

=== CRITICAL SUCCESS FACTORS ===
{'📊 MUST include specific numbers, percentages, and quantifiable achievements' if request.include_metrics else '🎯 Focus on impact and qualitative achievements'}
🔍 Optimize for LinkedIn algorithm: use industry keywords naturally
🎭 Target audience: {self._get_target_audience(request.target_role, request.target_industry)}
📱 Platform optimization: LinkedIn's 220-character preview + full bio
🎪 Engagement hooks: Start strong, end with clear value proposition

=== FORMATTING GUIDELINES ===
• Length: 180-280 words (LinkedIn sweet spot)
• Structure: Hook → Expertise → Achievements → Value → CTA
• Readability: Varied sentence lengths, active voice
• Keywords: Naturally integrate {self._get_industry_keywords(request.target_industry)}

=== OUTPUT REQUIREMENTS ===
Provide ONLY the enhanced bio text. No explanations, no prefixes, no commentary.
Make it so compelling that hiring managers can't help but click "Connect".

ENHANCED BIO:
"""
        
        return prompt
    
    def _build_context_section(self, request: EnhancementRequest) -> str:
        """Build rich context section for AI prompt."""
        context_parts = []
        
        if request.github_username:
            context_parts.append(f"👤 GitHub Profile: @{request.github_username}")
        
        if request.primary_languages:
            # Group and prioritize languages
            langs = request.primary_languages[:5]  # Top 5
            
            # Add language experience insights
            if len(langs) >= 4:
                lang_insight = "Polyglot developer with expertise across multiple languages"
            elif len(langs) >= 2:
                lang_insight = f"Strong in {langs[0]} and {langs[1]} with multi-language capabilities"
            else:
                lang_insight = f"Specialized in {langs[0]} development"
            
            context_parts.append(f"💻 Technical Stack: {', '.join(langs)} ({lang_insight})")
        
        if request.project_highlights:
            # Analyze project types for context
            projects = request.project_highlights[:3]
            project_types = self._infer_project_types(projects)
            context_parts.append(f"🚀 Notable Projects: {', '.join(projects)}")
            if project_types:
                context_parts.append(f"📂 Project Categories: {', '.join(project_types)}")
        
        if request.technical_achievements:
            # Parse achievements for insights
            achievements = request.technical_achievements[:3]
            context_parts.append(f"🏆 Key Achievements: {', '.join(achievements)}")
            
            # Add achievement context
            achievement_insights = self._analyze_achievement_patterns(achievements)
            if achievement_insights:
                context_parts.append(f"🎯 Achievement Focus: {achievement_insights}")
        
        # Add inferred context
        context_parts.append(f"🎯 Target Role: {request.target_role}")
        context_parts.append(f"🏢 Industry Focus: {request.target_industry}")
        
        # Add developer profile insights
        profile_insights = self._generate_developer_profile_insights(request)
        if profile_insights:
            context_parts.append(f"🧠 Developer Profile: {profile_insights}")
        
        return "\n".join(context_parts) if context_parts else "No specific context provided"
    
    def _infer_project_types(self, projects: List[str]) -> List[str]:
        """Infer project types from project names and descriptions."""
        types = []
        
        # Common project type indicators
        type_keywords = {
            "Web Applications": ["web", "app", "site", "dashboard", "portal", "frontend", "react", "vue"],
            "APIs & Backend": ["api", "backend", "server", "service", "rest", "graphql", "microservice"],
            "Data & Analytics": ["data", "analytics", "dashboard", "visualization", "ml", "ai", "analysis"],
            "Mobile Development": ["mobile", "ios", "android", "flutter", "react-native", "app"],
            "DevOps & Tools": ["cli", "tool", "automation", "deploy", "docker", "kubernetes", "ci"],
            "Libraries & Frameworks": ["library", "framework", "package", "sdk", "component"],
            "Games & Entertainment": ["game", "bot", "entertainment", "fun", "interactive"],
            "Blockchain & Crypto": ["blockchain", "crypto", "defi", "nft", "ethereum", "bitcoin"]
        }
        
        project_text = " ".join(projects).lower()
        
        for project_type, keywords in type_keywords.items():
            if any(keyword in project_text for keyword in keywords):
                types.append(project_type)
        
        return types[:3]  # Return top 3 categories
    
    def _analyze_achievement_patterns(self, achievements: List[str]) -> str:
        """Analyze patterns in achievements to understand focus areas."""
        
        achievement_text = " ".join(achievements).lower()
        
        focus_areas = []
        
        if any(word in achievement_text for word in ["star", "fork", "community", "open source"]):
            focus_areas.append("Community Impact")
        
        if any(word in achievement_text for word in ["performance", "optimization", "speed", "efficiency"]):
            focus_areas.append("Performance Optimization")
        
        if any(word in achievement_text for word in ["scale", "growth", "user", "traffic"]):
            focus_areas.append("Scalability & Growth")
        
        if any(word in achievement_text for word in ["innovation", "new", "first", "pioneering"]):
            focus_areas.append("Innovation Leadership")
        
        if any(word in achievement_text for word in ["team", "lead", "mentor", "manage"]):
            focus_areas.append("Technical Leadership")
        
        return ", ".join(focus_areas) if focus_areas else "Technical Excellence"
    
    def _generate_developer_profile_insights(self, request: EnhancementRequest) -> str:
        """Generate insights about the developer's profile and specialization."""
        
        insights = []
        
        # Analyze language combination for specialization
        if request.primary_languages:
            langs = [lang.lower() for lang in request.primary_languages[:4]]
            
            # Full-stack indicators
            frontend_langs = {"javascript", "typescript", "html", "css", "react", "vue", "angular"}
            backend_langs = {"python", "java", "go", "c#", "rust", "php", "ruby", "node.js"}
            mobile_langs = {"swift", "kotlin", "dart", "java", "objective-c"}
            
            has_frontend = any(lang in frontend_langs for lang in langs)
            has_backend = any(lang in backend_langs for lang in langs)
            has_mobile = any(lang in mobile_langs for lang in langs)
            
            if has_frontend and has_backend:
                insights.append("Full-stack developer")
            elif has_backend and not has_frontend:
                insights.append("Backend specialist")
            elif has_frontend and not has_backend:
                insights.append("Frontend specialist")
            
            if has_mobile:
                insights.append("Mobile developer")
            
            # Technology modernity
            modern_langs = {"typescript", "go", "rust", "kotlin", "swift", "python"}
            modern_count = sum(1 for lang in langs if lang in modern_langs)
            if modern_count >= 2:
                insights.append("Modern technology adopter")
            
            # Versatility
            if len(langs) >= 4:
                insights.append("Technology polyglot")
            elif len(langs) >= 2:
                insights.append("Multi-technology professional")
        
        # Analyze project focus
        if request.project_highlights:
            project_text = " ".join(request.project_highlights).lower()
            
            if any(word in project_text for word in ["open", "source", "community"]):
                insights.append("Open source contributor")
            
            if any(word in project_text for word in ["startup", "business", "product"]):
                insights.append("Product-focused engineer")
            
            if any(word in project_text for word in ["enterprise", "large", "scale"]):
                insights.append("Enterprise-scale developer")
        
    def evaluate_bio_by_style(self, bio: str, target_style: str) -> Dict[str, Any]:
        """Evaluate bio quality based on specific style requirements."""
        
        # Get base analysis
        analysis = self._analyze_bio_text(bio)
        
        # Style-specific evaluation
        if target_style == "professional":
            return self._evaluate_professional_style(bio, analysis)
        elif target_style == "creative":
            return self._evaluate_creative_style(bio, analysis)
        elif target_style == "technical":
            return self._evaluate_technical_style(bio, analysis)
        elif target_style == "executive":
            return self._evaluate_executive_style(bio, analysis)
        elif target_style == "startup":
            return self._evaluate_startup_style(bio, analysis)
        else:
            return self._evaluate_professional_style(bio, analysis)  # Default
    
    def _evaluate_professional_style(self, bio: str, analysis: Dict) -> Dict[str, Any]:
        """Evaluate bio for professional style standards."""
        
        scores = {}
        feedback = []
        
        # Authority & Credibility (30%)
        authority_score = 0
        if analysis['professional_count'] >= 2:
            authority_score += 40
        if analysis['number_count'] >= 2:
            authority_score += 30
        if analysis['action_verbs'] >= 3:
            authority_score += 30
        
        scores['authority'] = min(100, authority_score)
        
        # Clarity & Structure (25%)
        clarity_score = 0
        if 15 <= analysis['avg_words_per_sentence'] <= 20:
            clarity_score += 40
        else:
            clarity_score += max(0, 40 - abs(analysis['avg_words_per_sentence'] - 17.5) * 2)
        
        if 180 <= analysis['word_count'] <= 280:
            clarity_score += 35
        if analysis['sentence_variety'] > 3:
            clarity_score += 25
        
        scores['clarity'] = min(100, clarity_score)
        
        # Industry Relevance (20%)
        industry_keywords = ['experience', 'expertise', 'professional', 'results', 'successful', 'proven']
        relevance_score = sum(20 for keyword in industry_keywords if keyword in bio.lower())
        scores['relevance'] = min(100, relevance_score)
        
        # Engagement Factor (15%)
        engagement_indicators = ['passionate', 'driven', 'committed', 'focused', 'dedicated']
        engagement_score = sum(25 for indicator in engagement_indicators if indicator in bio.lower())
        scores['engagement'] = min(100, engagement_score)
        
        # Optimization (10%)
        optimization_score = 0
        if analysis['keyword_density'] > 5:
            optimization_score += 50
        if analysis['technical_terms'] >= 2:
            optimization_score += 50
        scores['optimization'] = optimization_score
        
        # Overall score
        weights = {'authority': 0.3, 'clarity': 0.25, 'relevance': 0.2, 'engagement': 0.15, 'optimization': 0.1}
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate feedback
        if scores['authority'] < 70:
            feedback.append("Add more quantifiable achievements and strong action verbs")
        if scores['clarity'] < 70:
            feedback.append("Improve sentence structure and overall clarity")
        if scores['engagement'] < 50:
            feedback.append("Include more personality and passion indicators")
        
        return {
            'overall_score': overall_score,
            'category_scores': scores,
            'feedback': feedback,
            'style_compliance': 'Professional' if overall_score >= 75 else 'Needs improvement'
        }
    
    def _evaluate_creative_style(self, bio: str, analysis: Dict) -> Dict[str, Any]:
        """Evaluate bio for creative style standards."""
        
        scores = {}
        feedback = []
        
        # Creativity & Personality (35%)
        creativity_indicators = ['innovative', 'creative', 'passionate', 'vision', 'imagination', 'artistic']
        metaphors = ['journey', 'craft', 'build', 'create', 'design', 'architect']
        
        creativity_score = 0
        creativity_score += sum(20 for indicator in creativity_indicators if indicator in bio.lower())
        creativity_score += sum(15 for metaphor in metaphors if metaphor in bio.lower())
        scores['creativity'] = min(100, creativity_score)
        
        # Storytelling & Flow (25%)
        storytelling_score = 0
        if analysis['sentence_variety'] > 4:
            storytelling_score += 40
        if analysis['engagement_count'] >= 2:
            storytelling_score += 35
        if 'I' in bio:  # First person narrative
            storytelling_score += 25
        scores['storytelling'] = min(100, storytelling_score)
        
        # Authenticity (20%)
        authenticity_indicators = ['love', 'enjoy', 'excited', 'believe', 'dream', 'inspire']
        authenticity_score = sum(25 for indicator in authenticity_indicators if indicator in bio.lower())
        scores['authenticity'] = min(100, authenticity_score)
        
        # Visual Appeal (10%)
        visual_score = 0
        if '✨' in bio or '🚀' in bio or '💡' in bio:  # Emojis
            visual_score += 50
        if analysis['sentence_variety'] > 3:
            visual_score += 50
        scores['visual_appeal'] = visual_score
        
        # Professional Balance (10%)
        balance_score = 0
        if analysis['professional_count'] >= 1:
            balance_score += 50
        if analysis['action_verbs'] >= 2:
            balance_score += 50
        scores['professional_balance'] = balance_score
        
        # Overall score
        weights = {'creativity': 0.35, 'storytelling': 0.25, 'authenticity': 0.2, 'visual_appeal': 0.1, 'professional_balance': 0.1}
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate feedback
        if scores['creativity'] < 70:
            feedback.append("Add more creative language and unique expressions")
        if scores['storytelling'] < 70:
            feedback.append("Improve narrative flow and personal story elements")
        if scores['authenticity'] < 50:
            feedback.append("Include more personal passion and authentic voice")
        
        return {
            'overall_score': overall_score,
            'category_scores': scores,
            'feedback': feedback,
            'style_compliance': 'Creative' if overall_score >= 75 else 'Needs more creativity'
        }
    
    def _evaluate_technical_style(self, bio: str, analysis: Dict) -> Dict[str, Any]:
        """Evaluate bio for technical style standards."""
        
        scores = {}
        feedback = []
        
        # Technical Expertise (40%)
        technical_score = 0
        if analysis['technical_terms'] >= 3:
            technical_score += 40
        if analysis['technical_terms'] >= 5:
            technical_score += 20
        
        technical_keywords = ['architecture', 'scalability', 'optimization', 'performance', 'systems', 'algorithms']
        tech_keyword_count = sum(1 for keyword in technical_keywords if keyword in bio.lower())
        technical_score += tech_keyword_count * 10
        
        scores['technical_expertise'] = min(100, technical_score)
        
        # Problem-Solving Focus (25%)
        problem_solving_indicators = ['solved', 'optimized', 'improved', 'designed', 'architected', 'built', 'implemented']
        problem_score = sum(15 for indicator in problem_solving_indicators if indicator in bio.lower())
        scores['problem_solving'] = min(100, problem_score)
        
        # Quantified Results (20%)
        if analysis['number_count'] >= 3:
            results_score = 100
        elif analysis['number_count'] >= 2:
            results_score = 70
        elif analysis['number_count'] >= 1:
            results_score = 40
        else:
            results_score = 0
        scores['quantified_results'] = results_score
        
        # Precision & Clarity (10%)
        precision_score = 0
        if 12 <= analysis['avg_words_per_sentence'] <= 18:
            precision_score += 60
        if analysis['technical_terms'] / max(analysis['word_count'], 1) * 100 > 3:  # Technical density
            precision_score += 40
        scores['precision'] = min(100, precision_score)
        
        # Industry Standards (5%)
        standards_keywords = ['best practices', 'standards', 'methodologies', 'frameworks', 'protocols']
        standards_score = sum(20 for keyword in standards_keywords if keyword in bio.lower())
        scores['industry_standards'] = min(100, standards_score)
        
        # Overall score
        weights = {'technical_expertise': 0.4, 'problem_solving': 0.25, 'quantified_results': 0.2, 'precision': 0.1, 'industry_standards': 0.05}
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate feedback
        if scores['technical_expertise'] < 70:
            feedback.append("Include more specific technical terminology and concepts")
        if scores['quantified_results'] < 70:
            feedback.append("Add more specific metrics and performance indicators")
        if scores['problem_solving'] < 60:
            feedback.append("Emphasize problem-solving achievements and solutions")
        
        return {
            'overall_score': overall_score,
            'category_scores': scores,
            'feedback': feedback,
            'style_compliance': 'Technical' if overall_score >= 75 else 'Needs more technical depth'
        }
    
    def _evaluate_executive_style(self, bio: str, analysis: Dict) -> Dict[str, Any]:
        """Evaluate bio for executive style standards."""
        
        scores = {}
        feedback = []
        
        # Strategic Vision (30%)
        vision_keywords = ['strategy', 'vision', 'transformation', 'growth', 'innovation', 'leadership']
        vision_score = sum(20 for keyword in vision_keywords if keyword in bio.lower())
        scores['strategic_vision'] = min(100, vision_score)
        
        # Leadership Evidence (25%)
        leadership_indicators = ['led', 'managed', 'directed', 'guided', 'mentored', 'built teams']
        leadership_score = sum(20 for indicator in leadership_indicators if indicator in bio.lower())
        scores['leadership'] = min(100, leadership_score)
        
        # Business Impact (25%)
        impact_score = 0
        if analysis['number_count'] >= 2:
            impact_score += 60
        business_terms = ['revenue', 'growth', 'roi', 'efficiency', 'scale', 'market']
        impact_score += sum(10 for term in business_terms if term in bio.lower())
        scores['business_impact'] = min(100, impact_score)
        
        # Communication Excellence (20%)
        comm_score = 0
        if 20 <= analysis['avg_words_per_sentence'] <= 25:
            comm_score += 70
        if analysis['professional_count'] >= 3:
            comm_score += 30
        scores['communication'] = min(100, comm_score)
        
        # Overall score
        weights = {'strategic_vision': 0.3, 'leadership': 0.25, 'business_impact': 0.25, 'communication': 0.2}
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate feedback
        if scores['strategic_vision'] < 70:
            feedback.append("Emphasize strategic thinking and visionary leadership")
        if scores['leadership'] < 70:
            feedback.append("Include more evidence of team leadership and mentorship")
        if scores['business_impact'] < 70:
            feedback.append("Add specific business outcomes and measurable impact")
        
        return {
            'overall_score': overall_score,
            'category_scores': scores,
            'feedback': feedback,
            'style_compliance': 'Executive' if overall_score >= 80 else 'Needs executive presence'
        }
    
    def _evaluate_startup_style(self, bio: str, analysis: Dict) -> Dict[str, Any]:
        """Evaluate bio for startup style standards."""
        
        scores = {}
        feedback = []
        
        # Innovation & Agility (35%)
        innovation_keywords = ['innovative', 'disruption', 'startup', 'entrepreneur', 'agile', 'rapid']
        innovation_score = sum(20 for keyword in innovation_keywords if keyword in bio.lower())
        scores['innovation'] = min(100, innovation_score)
        
        # Growth & Scale (25%)
        growth_indicators = ['scale', 'growth', 'launch', 'built', 'shipped', '0 to']
        growth_score = sum(25 for indicator in growth_indicators if indicator in bio.lower())
        scores['growth_focus'] = min(100, growth_score)
        
        # Versatility (20%)
        versatility_score = 0
        if len(analysis.get('technical_terms', 0)) >= 2:
            versatility_score += 40
        if analysis['action_verbs'] >= 4:
            versatility_score += 40
        multi_role_indicators = ['full-stack', 'end-to-end', 'product', 'business']
        versatility_score += sum(5 for indicator in multi_role_indicators if indicator in bio.lower())
        scores['versatility'] = min(100, versatility_score)
        
        # Energy & Passion (20%)
        energy_score = analysis['engagement_count'] * 30
        scores['energy'] = min(100, energy_score)
        
        # Overall score
        weights = {'innovation': 0.35, 'growth_focus': 0.25, 'versatility': 0.2, 'energy': 0.2}
        overall_score = sum(scores[key] * weights[key] for key in scores)
        
        # Generate feedback
        if scores['innovation'] < 70:
            feedback.append("Emphasize innovation and disruptive thinking")
        if scores['growth_focus'] < 70:
            feedback.append("Include more growth and scaling achievements")
        if scores['energy'] < 60:
            feedback.append("Add more energy and entrepreneurial passion")
        
        return {
            'overall_score': overall_score,
            'category_scores': scores,
            'feedback': feedback,
            'style_compliance': 'Startup-ready' if overall_score >= 75 else 'Needs startup energy'
        }
    
    def iterative_bio_improvement(self, request: EnhancementRequest, previous_attempts: List[str] = None, user_feedback: str = None) -> EnhancementResult:
        """Iteratively improve bio based on previous attempts and user feedback."""
        
        if not self.is_configured():
            raise ValueError("OpenRouter API not configured")
        
        self.logger.info("🔄 Starting iterative bio improvement process")
        
        # Build context-aware improvement prompt
        prompt = self._build_iterative_improvement_prompt(request, previous_attempts, user_feedback)
        
        # Use a model optimized for iterative tasks
        original_model = self.config.model
        self.config.model = self._select_iterative_model(request.target_style)
        
        try:
            # Make API request with higher temperature for creativity
            response = self._make_api_request(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=min(0.9, self.config.temperature + 0.2)  # Increase creativity
            )
            
            if not response or "choices" not in response:
                raise ValueError("Invalid response from OpenRouter API")
            
            # Parse enhanced bio
            enhanced_content = response["choices"][0]["message"]["content"]
            enhanced_bio = self._extract_bio_from_response(enhanced_content)
            
            # Analyze improvements with previous attempts comparison
            improvements = self._analyze_iterative_improvements(request.original_bio, enhanced_bio, previous_attempts)
            
            # Get usage data for cost calculation
            usage_data = response.get("usage", {})
            cost_info = self.calculate_actual_cost(usage_data, self.config.model)
            
            result = EnhancementResult(
                enhanced_bio=enhanced_bio,
                enhancement_score=self._calculate_enhancement_score(request.original_bio, enhanced_bio),
                improvements_made=improvements["improvements"],
                suggestions=improvements["suggestions"],
                readability_improvement=improvements["readability_improvement"],
                engagement_improvement=improvements["engagement_improvement"],
                keyword_optimization=improvements["keyword_optimization"],
                model_used=self.config.model,
                tokens_used=usage_data.get("total_tokens", 0),
                processing_time=0.0,  # Will be set by caller
                actual_cost=cost_info.get("total_cost", 0.0) if "error" not in cost_info else 0.0,
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                generation_id=response.get("id", ""),
                cost_breakdown=cost_info.get("cost_breakdown", {}) if "error" not in cost_info else {}
            )
            
            return result
            
        finally:
            # Restore original model
            self.config.model = original_model
    
    def _build_iterative_improvement_prompt(self, request: EnhancementRequest, previous_attempts: List[str], user_feedback: str) -> str:
        """Build prompt for iterative improvement with learning from previous attempts."""
        
        context_info = self._build_context_section(request)
        
        # Build previous attempts analysis
        attempts_analysis = ""
        if previous_attempts:
            attempts_analysis = f"""
=== PREVIOUS ATTEMPTS ANALYSIS ===
I've generated {len(previous_attempts)} previous versions. Here's what we've tried:

{chr(10).join(f"Attempt {i+1}: {attempt[:100]}..." for i, attempt in enumerate(previous_attempts))}

LEARNING POINTS:
• Avoid repeating exact phrases from previous attempts
• Build on successful elements while exploring new directions
• Ensure each iteration brings meaningful improvements
"""
        
        # Build user feedback section
        feedback_section = ""
        if user_feedback:
            feedback_section = f"""
=== USER FEEDBACK ===
The user specifically mentioned: "{user_feedback}"

INSTRUCTIONS: Address this feedback directly while maintaining bio quality.
"""
        
        # Build enhancement approach with iteration awareness
        prompt = f"""
You are an expert LinkedIn bio strategist specializing in iterative improvement. Your mission is to create a bio that learns from previous attempts and user feedback while avoiding repetition.

=== CONTEXT & BACKGROUND ===
{context_info}

=== ORIGINAL BIO ===
{request.original_bio}

{attempts_analysis}

{feedback_section}

=== ITERATIVE IMPROVEMENT STRATEGY ===
1. ANALYZE what worked well in previous attempts (if any)
2. IDENTIFY patterns to avoid repeating
3. INCORPORATE user feedback meaningfully
4. EXPLORE new angles and expressions
5. MAINTAIN authenticity while pushing creative boundaries

=== STYLE REQUIREMENTS ===
{self._get_style_specific_instructions(request.target_style)}

=== SUCCESS CRITERIA ===
✨ Must feel fresh and different from previous attempts
🎯 Directly address any user feedback provided
📈 Improve upon the strongest elements of previous versions
🚀 Push creative boundaries while staying professional
🔍 Optimize for LinkedIn engagement and discoverability

=== OUTPUT REQUIREMENTS ===
Provide ONLY the enhanced bio text. No explanations, no commentary.
Make this iteration significantly better than previous attempts.

ENHANCED BIO:
"""
        
        return prompt
    
    def _select_iterative_model(self, style: str) -> str:
        """Select optimal model for iterative improvement tasks."""
        
        # Models that excel at iterative and creative tasks
        iterative_models = {
            "creative": "anthropic/claude-3-opus",  # Best for creative iteration
            "technical": "anthropic/claude-sonnet-4.5",  # Best for technical precision
            "professional": "openai/gpt-4-turbo",  # Good balance for professional content
            "executive": "anthropic/claude-3-sonnet",  # Strategic thinking
            "startup": "google/gemini-2.5-flash"  # Fast and energetic
        }
        
        selected = iterative_models.get(style, "anthropic/claude-3-sonnet")
        
        # Fallback to current model if selected model not available
        if selected not in self.model_pricing:
            return self.config.model
        
        return selected
    
    def _analyze_iterative_improvements(self, original: str, enhanced: str, previous_attempts: List[str]) -> Dict[str, Any]:
        """Analyze improvements with awareness of previous iterations."""
        
        # Get base improvements analysis
        base_improvements = self._analyze_improvements(original, enhanced)
        
        # Add iteration-specific analysis
        iteration_insights = []
        
        if previous_attempts:
            # Check for novelty
            enhanced_lower = enhanced.lower()
            novelty_score = 0
            
            for attempt in previous_attempts:
                # Calculate similarity (simplified)
                attempt_lower = attempt.lower()
                common_phrases = []
                
                # Check for repeated phrases
                enhanced_words = set(enhanced_lower.split())
                attempt_words = set(attempt_lower.split())
                overlap = len(enhanced_words.intersection(attempt_words))
                total_words = len(enhanced_words.union(attempt_words))
                
                similarity = overlap / total_words if total_words > 0 else 0
                novelty_score += (1 - similarity) * 100
            
            novelty_score = novelty_score / len(previous_attempts)
            
            if novelty_score > 70:
                iteration_insights.append("Successfully avoided repetition from previous attempts")
            elif novelty_score > 50:
                iteration_insights.append("Some fresh elements added, but could be more distinctive")
            else:
                iteration_insights.append("High similarity to previous attempts - needs more differentiation")
            
            # Check for improvement trends
            word_counts = [len(attempt.split()) for attempt in previous_attempts]
            enhanced_words = len(enhanced.split())
            
            if word_counts:
                avg_previous_length = sum(word_counts) / len(word_counts)
                if enhanced_words > avg_previous_length * 1.1:
                    iteration_insights.append("Expanded content compared to previous iterations")
                elif enhanced_words < avg_previous_length * 0.9:
                    iteration_insights.append("Condensed content for better impact")
        
        # Combine with base improvements
        base_improvements["iteration_insights"] = iteration_insights
        base_improvements["improvements"].extend(iteration_insights)
        
        return base_improvements
    
    def suggest_improvement_direction(self, bio: str, style: str, current_score: float) -> List[str]:
        """Suggest specific directions for improvement based on current bio analysis."""
        
        suggestions = []
        
        # Analyze current bio
        analysis = self._analyze_bio_text(bio)
        style_evaluation = self.evaluate_bio_by_style(bio, style)
        
        # Score-based suggestions
        if current_score < 60:
            suggestions.append("Complete restructure recommended - consider different approach")
        elif current_score < 75:
            suggestions.append("Good foundation - focus on specific enhancements")
        else:
            suggestions.append("Fine-tuning for excellence - polish specific elements")
        
        # Style-specific suggestions
        category_scores = style_evaluation.get('category_scores', {})
        lowest_score_category = min(category_scores.items(), key=lambda x: x[1]) if category_scores else None
        
        if lowest_score_category:
            category, score = lowest_score_category
            if score < 70:
                suggestions.append(f"Focus on improving {category.replace('_', ' ')} (current score: {score:.0f})")
        
        # Content-specific suggestions
        if analysis['word_count'] < 150:
            suggestions.append("Expand with more specific achievements and context")
        elif analysis['word_count'] > 300:
            suggestions.append("Condense for better impact and readability")
        
        if analysis['number_count'] < 2:
            suggestions.append("Add specific metrics and quantifiable results")
        
        if analysis['action_verbs'] < 3:
            suggestions.append("Include more dynamic action verbs")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _create_fallback_enhancement(self, request: EnhancementRequest) -> EnhancementResult:
        """Create a fallback enhancement when API is unavailable."""
        self.logger.info("🛡️ Using fallback bio enhancement")
        
        # Use template-based enhancement when API fails
        enhanced_bio = self._template_based_enhancement(request)
        
        # Basic analysis
        improvements = self._analyze_improvements(request.original_bio, enhanced_bio)
        
        return EnhancementResult(
            enhanced_bio=enhanced_bio,
            enhancement_score=70.0,  # Conservative score for template-based
            improvements_made=["Applied template-based enhancement (API unavailable)"],
            suggestions=["Retry with API when connection is stable"],
            readability_improvement=improvements.get("readability_improvement", 0),
            engagement_improvement=improvements.get("engagement_improvement", 0),
            keyword_optimization=improvements.get("keyword_optimization", 0),
            model_used="fallback-template",
            tokens_used=0,
            processing_time=0.1,
            actual_cost=0.0,
            estimated_cost=0.0,
            prompt_tokens=0,
            completion_tokens=0,
            generation_id="fallback",
            cost_breakdown={}
        )
    
    def _template_based_enhancement(self, request: EnhancementRequest) -> str:
        """Template-based bio enhancement when API is unavailable."""
        
        # Extract key information
        languages = ", ".join(request.primary_languages[:3]) if request.primary_languages else "modern technologies"
        projects = ", ".join(request.project_highlights[:2]) if request.project_highlights else "innovative solutions"
        achievements = ", ".join(request.technical_achievements[:2]) if request.technical_achievements else "significant impact"
        
        # Style-specific templates
        templates = {
            "professional": f"""
Experienced {request.target_role} with expertise in {languages}. Proven track record of delivering high-quality solutions and driving technical excellence in {request.target_industry}.

Key accomplishments include {achievements} through projects like {projects}. Skilled in building scalable applications and leading technical initiatives that deliver measurable business value.

Passionate about innovation and continuous learning, with a focus on leveraging cutting-edge technologies to solve complex challenges. Always seeking opportunities to collaborate with talented teams and contribute to impactful projects.

Let's connect to discuss {request.target_industry} opportunities and technical collaboration.""",
            
            "creative": f"""
I'm a {request.target_role} who loves turning ideas into reality through code! 🚀

My toolkit includes {languages}, and I've had the pleasure of building {projects}. What drives me is the opportunity to create solutions that make a real difference.

Some highlights from my journey: {achievements}. Each project has taught me something new and pushed me to grow as both a developer and a problem-solver.

When I'm not coding, you'll find me exploring new technologies and contributing to the {request.target_industry} community. I believe the best software comes from passionate people working together.

Always excited to connect with fellow creators and innovators! Let's build something amazing together. ✨""",
            
            "technical": f"""
Senior {request.target_role} specializing in {languages} with focus on scalable architecture and system optimization.

Technical expertise includes {achievements} across projects involving {projects}. Experience spans full-stack development, performance optimization, and building robust systems that handle scale.

Core competencies:
• Architecture design and implementation
• Performance optimization and scalability
• Code quality and engineering best practices
• Technical leadership and mentorship

Committed to engineering excellence and continuous improvement. Open to discussing technical challenges, architecture decisions, and engineering opportunities in {request.target_industry}."""
        }
        
        # Select appropriate template
        template = templates.get(request.target_style, templates["professional"])
        
        # Clean up the template
        enhanced = template.strip()
        
        # Basic validation and cleanup
        if len(enhanced) < 100:
            enhanced = f"Experienced {request.target_role} with {len(request.primary_languages) if request.primary_languages else 3}+ years in {request.target_industry}. " + enhanced
        
        return enhanced
    
    def _get_style_specific_instructions(self, style: str) -> str:
        """Get detailed style-specific instructions."""
        style_guides = {
            "professional": """
• Tone: Confident, accomplished, approachable
• Language: Clear, direct, industry-appropriate
• Structure: Achievement-focused with quantifiable results
• Voice: Third-person perspective, authoritative but humble
• Keywords: Leadership, expertise, results, innovation
• Avoid: Overly casual language, buzzword overload""",
            
            "creative": """
• Tone: Innovative, passionate, authentic
• Language: Vivid, engaging, story-driven
• Structure: Journey narrative with creative metaphors
• Voice: First-person, personal yet professional
• Keywords: Innovation, creativity, vision, impact
• Avoid: Corporate jargon, overly formal language""",
            
            "technical": """
• Tone: Precise, knowledgeable, solution-oriented
• Language: Technical accuracy with accessibility
• Structure: Problem-solution focused with metrics
• Voice: Expert practitioner, thought leader
• Keywords: Architecture, scalability, optimization, systems
• Avoid: Non-technical fluff, generic statements""",
            
            "executive": """
• Tone: Strategic, visionary, results-driven
• Language: Business-focused, outcome-oriented
• Structure: Vision → execution → impact → future
• Voice: Thought leader, change agent
• Keywords: Strategy, transformation, growth, leadership
• Avoid: Operational details, technical jargon""",
            
            "startup": """
• Tone: Energetic, agile, growth-minded
• Language: Fast-paced, opportunity-focused
• Structure: Problem → solution → traction → vision
• Voice: Builder, innovator, risk-taker
• Keywords: Scale, disruption, innovation, growth
• Avoid: Corporate bureaucracy language, slow/safe terminology"""
        }
        
        return style_guides.get(style, style_guides["professional"])
    
    def _get_enhancement_approach(self, enhancement_type: str) -> str:
        """Get specific enhancement approach instructions."""
        approaches = {
            "improve": "Transform this bio into a compelling narrative that showcases expertise while maintaining authenticity. Enhance clarity, impact, and professional appeal.",
            "rewrite": "Completely reimagine this bio with fresh perspective, better flow, and stronger positioning. Create a new narrative structure while preserving core achievements.",
            "optimize": "Engineer this bio for maximum LinkedIn visibility and engagement. Focus on keyword optimization, algorithm-friendly structure, and recruiter appeal.",
            "personalize": "Inject authentic personality and unique voice while maintaining professional standards. Make it memorable and distinctly human."
        }
        
        return approaches.get(enhancement_type, approaches["improve"])
    
    def _get_target_audience(self, role: str, industry: str) -> str:
        """Get target audience description."""
        audience_map = {
            "technology": "CTOs, Engineering Managers, Tech Recruiters, Startup Founders",
            "fintech": "Finance Leaders, Risk Managers, Fintech Recruiters, Investment Partners",
            "healthcare": "Healthcare CIOs, Medical Directors, Health Tech Recruiters",
            "ecommerce": "E-commerce Leaders, Product Managers, Digital Marketing Directors",
            "gaming": "Game Studio Leaders, Creative Directors, Gaming Industry Recruiters",
            "ai_ml": "AI Research Leaders, Data Science Managers, ML Engineering Directors"
        }
        
        return audience_map.get(industry, "Hiring Managers, Team Leaders, Industry Recruiters")
    
    def _get_industry_keywords(self, industry: str) -> str:
        """Get industry-specific keywords to integrate."""
        keyword_sets = {
            "technology": "software engineering, scalability, architecture, DevOps, cloud",
            "fintech": "financial technology, compliance, risk management, payments, blockchain",
            "healthcare": "healthcare technology, patient care, medical software, HIPAA, clinical",
            "ecommerce": "e-commerce, conversion optimization, customer experience, analytics",
            "gaming": "game development, user engagement, monetization, player experience",
            "ai_ml": "artificial intelligence, machine learning, data science, automation"
        }
        
        return keyword_sets.get(industry, "innovation, technology, leadership, results")
    
    def suggest_optimal_model(self, request: EnhancementRequest, budget_preference: str = "balanced") -> str:
        """Suggest optimal model based on bio requirements and budget."""
        
        # Define model categories by strength
        creative_models = [
            "anthropic/claude-3-opus",
            "anthropic/claude-sonnet-4.5", 
            "openai/gpt-4-turbo",
            "anthropic/claude-3-sonnet"
        ]
        
        technical_models = [
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-4-turbo",
            "deepseek/deepseek-v3.2-exp",
            "anthropic/claude-3-sonnet"
        ]
        
        cost_effective_models = [
            "meta-llama/llama-3-8b-instruct",
            "google/gemini-2.5-flash",
            "anthropic/claude-3-haiku",
            "deepseek/deepseek-v3.2-exp"
        ]
        
        premium_models = [
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-4-turbo",
            "anthropic/claude-3-opus",
            "openai/gpt-4"
        ]
        
        # Selection logic based on style and budget
        if budget_preference == "economy":
            candidate_models = cost_effective_models
        elif budget_preference == "premium":
            candidate_models = premium_models
        else:  # balanced
            # Choose based on style requirements
            if request.target_style == "creative":
                candidate_models = ["anthropic/claude-3-sonnet", "openai/gpt-3.5-turbo", "google/gemini-2.5-flash"]
            elif request.target_style == "technical":
                candidate_models = ["deepseek/deepseek-v3.2-exp", "anthropic/claude-3-sonnet", "meta-llama/llama-3-8b-instruct"]
            else:
                candidate_models = ["anthropic/claude-3-haiku", "google/gemini-2.5-flash", "meta-llama/llama-3-8b-instruct"]
        
        # Return first available model (could add availability checking)
        for model in candidate_models:
            if model in self.model_pricing:
                return model
        
        # Fallback to default
        return self.config.model
    
    def get_model_recommendations(self, request: EnhancementRequest) -> List[Dict[str, Any]]:
        """Get ranked model recommendations with cost and quality estimates."""
        recommendations = []
        
        bio_length = len(request.original_bio.split())
        
        for model_id, pricing in self.model_pricing.items():
            # Estimate cost for this bio
            estimated_cost = pricing.estimate_bio_cost()
            
            # Calculate quality score based on model characteristics
            quality_score = self._calculate_model_quality_score(model_id, request.target_style)
            
            # Calculate speed score
            speed_score = max(0, 100 - (pricing.latency * 20))  # Lower latency = higher score
            
            recommendations.append({
                "model_id": model_id,
                "model_name": pricing.model_name,
                "provider": pricing.provider,
                "estimated_cost": estimated_cost,
                "cost_formatted": f"${estimated_cost:.4f}",
                "quality_score": quality_score,
                "speed_score": speed_score,
                "overall_score": (quality_score * 0.5) + (speed_score * 0.2) + (max(0, 100 - estimated_cost * 1000) * 0.3),
                "description": pricing.description,
                "best_for": self._get_model_best_use_case(model_id, request.target_style)
            })
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return recommendations
    
    def _calculate_model_quality_score(self, model_id: str, style: str) -> float:
        """Calculate quality score for model based on style requirements."""
        
        # Base scores for each model (subjective, based on general performance)
        base_scores = {
            "anthropic/claude-sonnet-4.5": 95,
            "anthropic/claude-3-opus": 92,
            "openai/gpt-4-turbo": 90,
            "openai/gpt-4": 88,
            "anthropic/claude-3-sonnet": 85,
            "deepseek/deepseek-v3.2-exp": 82,
            "google/gemini-2.5-flash": 80,
            "anthropic/claude-3-haiku": 78,
            "openai/gpt-3.5-turbo": 75,
            "meta-llama/llama-3-70b-instruct": 73,
            "meta-llama/llama-3-8b-instruct": 70
        }
        
        base_score = base_scores.get(model_id, 70)
        
        # Style-specific adjustments
        style_adjustments = {
            "creative": {
                "anthropic/claude-3-opus": 8,
                "anthropic/claude-sonnet-4.5": 6,
                "openai/gpt-4-turbo": 5,
                "anthropic/claude-3-sonnet": 4
            },
            "technical": {
                "deepseek/deepseek-v3.2-exp": 8,
                "anthropic/claude-sonnet-4.5": 6,
                "openai/gpt-4-turbo": 5,
                "meta-llama/llama-3-8b-instruct": 3
            },
            "professional": {
                "anthropic/claude-3-sonnet": 5,
                "openai/gpt-3.5-turbo": 4,
                "anthropic/claude-3-haiku": 3
            }
        }
        
        adjustment = style_adjustments.get(style, {}).get(model_id, 0)
        
        return min(100, base_score + adjustment)
    
    def _get_model_best_use_case(self, model_id: str, style: str) -> str:
        """Get best use case description for model."""
        
        use_cases = {
            "anthropic/claude-sonnet-4.5": "Premium content with exceptional reasoning",
            "anthropic/claude-3-opus": "Highest quality creative writing",
            "openai/gpt-4-turbo": "Professional content with reliability",
            "anthropic/claude-3-sonnet": "Balanced quality and cost",
            "deepseek/deepseek-v3.2-exp": "Technical content, excellent value",
            "google/gemini-2.5-flash": "Fast, cost-effective generation",
            "anthropic/claude-3-haiku": "Budget-friendly, reliable quality",
            "openai/gpt-3.5-turbo": "Standard professional content",
            "meta-llama/llama-3-8b-instruct": "Very cost-effective, good quality"
        }
        
    def optimize_for_budget(self, request: EnhancementRequest, max_budget: float = 0.01) -> Dict[str, Any]:
        """Optimize model selection and parameters for budget constraints."""
        
        # Get all viable models within budget
        viable_models = []
        for model_id, pricing in self.model_pricing.items():
            estimated_cost = pricing.estimate_bio_cost()
            if estimated_cost <= max_budget:
                quality_score = self._calculate_model_quality_score(model_id, request.target_style)
                viable_models.append({
                    "model_id": model_id,
                    "estimated_cost": estimated_cost,
                    "quality_score": quality_score,
                    "value_score": quality_score / (estimated_cost * 1000)  # Quality per cent
                })
        
        if not viable_models:
            # If no models within budget, suggest cheapest option
            cheapest = min(self.model_pricing.items(), key=lambda x: x[1].estimate_bio_cost())
            return {
                "recommended_model": cheapest[0],
                "estimated_cost": cheapest[1].estimate_bio_cost(),
                "budget_exceeded": True,
                "message": f"Budget too low. Cheapest option is ${cheapest[1].estimate_bio_cost():.4f}"
            }
        
        # Sort by value score (quality per cost)
        viable_models.sort(key=lambda x: x["value_score"], reverse=True)
        best_option = viable_models[0]
        
        return {
            "recommended_model": best_option["model_id"],
            "estimated_cost": best_option["estimated_cost"],
            "quality_score": best_option["quality_score"],
            "value_score": best_option["value_score"],
            "budget_exceeded": False,
            "alternatives": viable_models[1:3],  # Top 2 alternatives
            "savings": max_budget - best_option["estimated_cost"]
        }
    
    def get_cost_vs_quality_analysis(self, request: EnhancementRequest) -> Dict[str, Any]:
        """Analyze cost vs quality trade-offs for all models."""
        
        analysis = {
            "budget_tiers": {
                "economy": {"max_cost": 0.001, "models": []},
                "balanced": {"max_cost": 0.005, "models": []},
                "premium": {"max_cost": 0.02, "models": []}
            },
            "best_value": None,
            "highest_quality": None,
            "most_economical": None
        }
        
        models_data = []
        
        for model_id, pricing in self.model_pricing.items():
            estimated_cost = pricing.estimate_bio_cost()
            quality_score = self._calculate_model_quality_score(model_id, request.target_style)
            value_score = quality_score / (estimated_cost * 1000)
            
            model_data = {
                "model_id": model_id,
                "model_name": pricing.model_name,
                "provider": pricing.provider,
                "estimated_cost": estimated_cost,
                "quality_score": quality_score,
                "value_score": value_score
            }
            
            models_data.append(model_data)
            
            # Categorize by budget tiers
            if estimated_cost <= 0.001:
                analysis["budget_tiers"]["economy"]["models"].append(model_data)
            elif estimated_cost <= 0.005:
                analysis["budget_tiers"]["balanced"]["models"].append(model_data)
            else:
                analysis["budget_tiers"]["premium"]["models"].append(model_data)
        
        # Find best in each category
        if models_data:
            analysis["best_value"] = max(models_data, key=lambda x: x["value_score"])
            analysis["highest_quality"] = max(models_data, key=lambda x: x["quality_score"])
            analysis["most_economical"] = min(models_data, key=lambda x: x["estimated_cost"])
        
        # Sort each tier by value score
        for tier in analysis["budget_tiers"].values():
            tier["models"].sort(key=lambda x: x["value_score"], reverse=True)
        
        return analysis
    
    def estimate_monthly_costs(self, daily_bio_count: int, model_id: str = None) -> Dict[str, Any]:
        """Estimate monthly costs based on usage patterns."""
        
        model_id = model_id or self.config.model
        pricing = self.get_model_pricing(model_id)
        
        if not pricing:
            return {"error": "Model pricing not available"}
        
        daily_cost = pricing.estimate_bio_cost() * daily_bio_count
        monthly_cost = daily_cost * 30
        
        # Cost breakdown by volume
        volume_analysis = {
            "light_usage": {"daily_bios": 1, "monthly_cost": pricing.estimate_bio_cost() * 30},
            "moderate_usage": {"daily_bios": 5, "monthly_cost": pricing.estimate_bio_cost() * 150},
            "heavy_usage": {"daily_bios": 20, "monthly_cost": pricing.estimate_bio_cost() * 600}
        }
        
        # Budget recommendations
        budget_recommendations = []
        if monthly_cost < 1.0:
            budget_recommendations.append("Very economical - suitable for regular use")
        elif monthly_cost < 5.0:
            budget_recommendations.append("Reasonable for business use")
        elif monthly_cost < 20.0:
            budget_recommendations.append("Higher cost - consider usage optimization")
        else:
            budget_recommendations.append("Expensive - evaluate cheaper alternatives")
        
        return {
            "model": pricing.model_name,
            "daily_bios": daily_bio_count,
            "daily_cost": daily_cost,
            "monthly_cost": monthly_cost,
            "yearly_cost": monthly_cost * 12,
            "cost_per_bio": pricing.estimate_bio_cost(),
            "volume_analysis": volume_analysis,
            "recommendations": budget_recommendations
        }
    
    def _make_api_request(self, prompt: str, max_tokens: int = None, temperature: float = None) -> Optional[Dict]:
        """Make API request to OpenRouter with robust error handling and retry logic."""
        if not self.config.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        url = f"{self.config.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/dev-alt/RepoReadme",
            "X-Title": "RepoReadme AI Bio Generator"
        }
        
        data = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature
        }
        
        # Multiple attempt strategy with different approaches
        last_error = None
        
        for attempt in range(3):
            try:
                self.logger.debug(f"OpenRouter API attempt {attempt + 1}/3")
                
                if attempt == 0:
                    # First attempt: Normal request with session
                    response = self.session.post(
                        url, 
                        headers=headers, 
                        json=data, 
                        timeout=60,
                        verify=True
                    )
                elif attempt == 1:
                    # Second attempt: Disable SSL verification
                    self.logger.warning("Attempting request with SSL verification disabled")
                    response = self.session.post(
                        url, 
                        headers=headers, 
                        json=data, 
                        timeout=60,
                        verify=False
                    )
                else:
                    # Third attempt: Fresh session with basic requests
                    self.logger.warning("Attempting with fresh requests session")
                    response = requests.post(
                        url, 
                        headers=headers, 
                        json=data, 
                        timeout=60,
                        verify=False
                    )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.SSLError as e:
                last_error = e
                self.logger.warning(f"SSL error on attempt {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            except requests.exceptions.ConnectionError as e:
                last_error = e
                self.logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                continue
                
            except requests.exceptions.Timeout as e:
                last_error = e
                self.logger.warning(f"Timeout error on attempt {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(1)
                continue
                
            except requests.exceptions.RequestException as e:
                last_error = e
                self.logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(1)
                continue
                
            except Exception as e:
                last_error = e
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(1)
                continue
        
        # All attempts failed
        self.logger.error(f"All API request attempts failed. Last error: {last_error}")
        raise last_error
    
    def _extract_bio_from_response(self, response_content: str) -> str:
        """Extract clean bio from AI response."""
        # Remove common AI response prefixes/suffixes
        bio = response_content.strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Enhanced bio:",
            "Optimized bio:",
            "Alternative bio:",
            "Here's the enhanced bio:",
            "Here's an optimized version:",
            "Bio:",
            "LinkedIn bio:"
        ]
        
        for prefix in prefixes_to_remove:
            if bio.lower().startswith(prefix.lower()):
                bio = bio[len(prefix):].strip()
        
        # Remove quotes if the entire bio is quoted
        if bio.startswith('"') and bio.endswith('"'):
            bio = bio[1:-1].strip()
        
        return bio
    
    def _analyze_improvements(self, original: str, enhanced: str) -> Dict[str, Any]:
        """Analyze improvements made to the bio with sophisticated metrics."""
        improvements = []
        suggestions = []
        
        # Advanced text analysis
        original_analysis = self._analyze_bio_text(original)
        enhanced_analysis = self._analyze_bio_text(enhanced)
        
        # Content expansion analysis
        if enhanced_analysis['word_count'] > original_analysis['word_count'] * 1.2:
            improvements.append("Expanded content with more detail")
        elif enhanced_analysis['word_count'] < original_analysis['word_count'] * 0.8:
            improvements.append("Condensed content for better impact")
        
        # Quantification improvements
        if enhanced_analysis['number_count'] > original_analysis['number_count']:
            improvements.append("Added quantified achievements")
        
        # Technical skills enhancement
        if enhanced_analysis['technical_terms'] > original_analysis['technical_terms']:
            improvements.append("Enhanced technical skills listing")
        
        # Action verb strengthening
        if enhanced_analysis['action_verbs'] > original_analysis['action_verbs']:
            improvements.append("Strengthened action verbs")
        
        # Structure improvements
        if enhanced_analysis['sentence_variety'] > original_analysis['sentence_variety']:
            improvements.append("Improved sentence structure variety")
        
        # Keyword optimization
        if enhanced_analysis['keyword_density'] > original_analysis['keyword_density']:
            improvements.append("Optimized keyword usage")
        
        # Calculate sophisticated improvement scores
        readability_improvement = self._calculate_readability_improvement(original_analysis, enhanced_analysis)
        engagement_improvement = self._calculate_engagement_improvement(original_analysis, enhanced_analysis)
        keyword_optimization = self._calculate_keyword_optimization(original_analysis, enhanced_analysis)
        
        # Generate suggestions based on analysis
        suggestions = self._generate_improvement_suggestions(enhanced_analysis)
        
        return {
            "improvements": improvements,
            "suggestions": suggestions,
            "readability_improvement": readability_improvement,
            "engagement_improvement": engagement_improvement,
            "keyword_optimization": keyword_optimization,
            "original_analysis": original_analysis,
            "enhanced_analysis": enhanced_analysis
        }
    
    def _analyze_bio_text(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive text analysis on bio content."""
        import re
        
        words = text.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        
        # Basic metrics
        word_count = len(words)
        sentence_count = len(sentences)
        char_count = len(text)
        
        # Advanced metrics
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        avg_chars_per_word = char_count / max(word_count, 1)
        
        # Count specific elements
        numbers = re.findall(r'\\d+', text)
        number_count = len(numbers)
        
        # Action verbs (common professional action words)
        action_verbs = ['led', 'managed', 'built', 'created', 'developed', 'designed', 'implemented', 'optimized',
                       'delivered', 'achieved', 'improved', 'increased', 'reduced', 'launched', 'architected']
        action_verb_count = sum(1 for verb in action_verbs if verb in text.lower())
        
        # Technical terms (common in software engineering bios)
        technical_terms = ['api', 'database', 'architecture', 'framework', 'algorithm', 'optimization',
                          'scalability', 'microservices', 'cloud', 'devops', 'automation', 'ci/cd']
        technical_term_count = sum(1 for term in technical_terms if term in text.lower())
        
        # Keyword density (industry-relevant terms)
        industry_keywords = ['software', 'engineering', 'development', 'programming', 'technology',
                           'innovation', 'solutions', 'systems', 'applications', 'projects']
        keyword_matches = sum(1 for keyword in industry_keywords if keyword in text.lower())
        keyword_density = (keyword_matches / max(word_count, 1)) * 100
        
        # Sentence length variety (standard deviation)
        sentence_lengths = [len(s.split()) for s in sentences]
        if len(sentence_lengths) > 1:
            import statistics
            sentence_variety = statistics.stdev(sentence_lengths)
        else:
            sentence_variety = 0
        
        # Engagement indicators
        engagement_words = ['passionate', 'innovative', 'excited', 'driven', 'love', 'enjoy',
                           'enthusiastic', 'committed', 'dedicated', 'focused']
        engagement_count = sum(1 for word in engagement_words if word in text.lower())
        
        # Professional indicators
        professional_words = ['experience', 'expertise', 'proven', 'results', 'successful',
                             'accomplished', 'established', 'recognized', 'certified']
        professional_count = sum(1 for word in professional_words if word in text.lower())
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'char_count': char_count,
            'avg_words_per_sentence': avg_words_per_sentence,
            'avg_chars_per_word': avg_chars_per_word,
            'number_count': number_count,
            'action_verbs': action_verb_count,
            'technical_terms': technical_term_count,
            'keyword_density': keyword_density,
            'sentence_variety': sentence_variety,
            'engagement_count': engagement_count,
            'professional_count': professional_count
        }
    
    def _calculate_readability_improvement(self, original: Dict, enhanced: Dict) -> float:
        """Calculate readability improvement score."""
        
        # Ideal ranges for LinkedIn bios
        ideal_avg_sentence_length = 15  # words per sentence
        ideal_avg_word_length = 5      # characters per word
        
        # Score original readability
        orig_sentence_score = max(0, 100 - abs(original['avg_words_per_sentence'] - ideal_avg_sentence_length) * 5)
        orig_word_score = max(0, 100 - abs(original['avg_chars_per_word'] - ideal_avg_word_length) * 10)
        orig_variety_score = min(100, original['sentence_variety'] * 10)
        original_readability = (orig_sentence_score + orig_word_score + orig_variety_score) / 3
        
        # Score enhanced readability
        enh_sentence_score = max(0, 100 - abs(enhanced['avg_words_per_sentence'] - ideal_avg_sentence_length) * 5)
        enh_word_score = max(0, 100 - abs(enhanced['avg_chars_per_word'] - ideal_avg_word_length) * 10)
        enh_variety_score = min(100, enhanced['sentence_variety'] * 10)
        enhanced_readability = (enh_sentence_score + enh_word_score + enh_variety_score) / 3
        
        # Calculate improvement
        return enhanced_readability - original_readability
    
    def _calculate_engagement_improvement(self, original: Dict, enhanced: Dict) -> float:
        """Calculate engagement improvement score."""
        
        # Weight different factors
        engagement_weight = 0.3
        action_weight = 0.4
        professional_weight = 0.3
        
        # Calculate scores (normalized)
        orig_engagement = min(100, original['engagement_count'] * 25)
        orig_action = min(100, original['action_verbs'] * 20)
        orig_professional = min(100, original['professional_count'] * 15)
        original_engagement_score = (orig_engagement * engagement_weight + 
                                   orig_action * action_weight + 
                                   orig_professional * professional_weight)
        
        enh_engagement = min(100, enhanced['engagement_count'] * 25)
        enh_action = min(100, enhanced['action_verbs'] * 20)
        enh_professional = min(100, enhanced['professional_count'] * 15)
        enhanced_engagement_score = (enh_engagement * engagement_weight + 
                                   enh_action * action_weight + 
                                   enh_professional * professional_weight)
        
        return enhanced_engagement_score - original_engagement_score
    
    def _calculate_keyword_optimization(self, original: Dict, enhanced: Dict) -> float:
        """Calculate keyword optimization improvement."""
        
        # Compare keyword density improvements
        keyword_improvement = enhanced['keyword_density'] - original['keyword_density']
        
        # Compare technical term usage
        technical_improvement = (enhanced['technical_terms'] - original['technical_terms']) * 10
        
        # Quantification improvement
        number_improvement = (enhanced['number_count'] - original['number_count']) * 15
        
        # Combine scores
        total_improvement = keyword_improvement + technical_improvement + number_improvement
        
        # Normalize to 0-100 scale
        return min(100, max(-100, total_improvement))
    
    def _generate_improvement_suggestions(self, analysis: Dict) -> List[str]:
        """Generate specific improvement suggestions based on analysis."""
        suggestions = []
        
        if analysis['number_count'] < 2:
            suggestions.append("Add more specific metrics and quantifiable achievements")
        
        if analysis['action_verbs'] < 3:
            suggestions.append("Include more strong action verbs (led, built, optimized, etc.)")
        
        if analysis['avg_words_per_sentence'] > 20:
            suggestions.append("Break up long sentences for better readability")
        
        if analysis['technical_terms'] < 2:
            suggestions.append("Include more relevant technical terminology")
        
        if analysis['engagement_count'] < 1:
            suggestions.append("Add more personality with passion statements")
        
        if analysis['word_count'] < 150:
            suggestions.append("Expand content to reach optimal LinkedIn bio length (180-280 words)")
        
        if analysis['word_count'] > 300:
            suggestions.append("Consider condensing content for better impact")
        
        return suggestions
    
    def _calculate_enhancement_score(self, original: str, enhanced: str) -> float:
        """Calculate overall enhancement score."""
        # Simplified scoring - would be more sophisticated in production
        score = 75.0
        
        # Length optimization
        original_words = len(original.split())
        enhanced_words = len(enhanced.split())
        
        if 150 <= enhanced_words <= 300:  # Ideal LinkedIn bio length
            score += 10
        
        # Content enrichment
        if enhanced_words > original_words * 1.2:
            score += 10
        
        # Action words
        action_words = ['led', 'built', 'created', 'developed', 'managed', 'designed']
        enhanced_actions = sum(1 for word in action_words if word in enhanced.lower())
        original_actions = sum(1 for word in action_words if word in original.lower())
        
        if enhanced_actions > original_actions:
            score += 5
        
        return min(score, 100.0)
    
    def _estimate_cost_for_request(self, request: EnhancementRequest) -> float:
        """Estimate cost for enhancement request (used for comparison with actual)."""
        pricing = self.get_model_pricing(self.config.model)
        if not pricing:
            return 0.0
        
        # Rough estimation for comparison
        words = len(request.original_bio.split())
        input_tokens = int(words / 0.75) + 200  # Add system prompt tokens
        output_tokens = 300  # Typical enhanced bio length
        
        return pricing.estimate_cost(input_tokens, output_tokens)


# Export classes
__all__ = [
    'OpenRouterConfig',
    'EnhancementRequest', 
    'EnhancementResult',
    'OpenRouterAIService'
]