#!/usr/bin/env python3
"""
Test script for the enhanced OpenRouter service with SSL error handling
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.openrouter_service import OpenRouterAIService, EnhancementRequest, OpenRouterConfig
from src.utils.logger import get_logger

def test_ssl_error_handling():
    """Test SSL error handling and fallback functionality."""
    logger = get_logger()
    logger.info("🧪 Testing enhanced OpenRouter service")
    
    # Create service instance
    config = OpenRouterConfig()
    service = OpenRouterAIService(config)
    
    # Create test request
    request = EnhancementRequest(
        original_bio="Software engineer with experience in Python and JavaScript.",
        target_style="professional",
        target_role="Software Engineer",
        target_industry="technology",
        github_username="test-user",
        primary_languages=["Python", "JavaScript", "TypeScript"],
        project_highlights=["web application", "API service"],
        technical_achievements=["10+ GitHub stars", "3 successful projects"]
    )
    
    logger.info("📝 Test request created")
    logger.info(f"   Original bio: {request.original_bio}")
    logger.info(f"   Style: {request.target_style}")
    logger.info(f"   Languages: {request.primary_languages}")
    
    try:
        # Test enhancement (will likely fail due to SSL, triggering fallback)
        logger.info("🚀 Attempting bio enhancement...")
        result = service.enhance_linkedin_bio(request)
        
        logger.info("✅ Enhancement completed")
        logger.info(f"   Model used: {result.model_used}")
        logger.info(f"   Processing time: {result.processing_time:.2f}s")
        logger.info(f"   Enhancement score: {result.enhancement_score}")
        logger.info(f"   Cost: ${result.actual_cost:.6f}")
        
        logger.info("📋 Enhanced bio:")
        logger.info(f"   {result.enhanced_bio[:200]}...")
        
        if result.improvements_made:
            logger.info("🔧 Improvements made:")
            for improvement in result.improvements_made:
                logger.info(f"   • {improvement}")
        
        if result.suggestions:
            logger.info("💡 Suggestions:")
            for suggestion in result.suggestions:
                logger.info(f"   • {suggestion}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_cost_optimization():
    """Test cost optimization features."""
    logger = get_logger()
    logger.info("💰 Testing cost optimization features")
    
    service = OpenRouterAIService()
    
    # Test model recommendations
    request = EnhancementRequest(
        original_bio="Software engineer",
        target_style="technical"
    )
    
    try:
        # Get cost analysis
        cost_analysis = service.get_cost_vs_quality_analysis(request)
        logger.info("📊 Cost vs Quality Analysis:")
        
        if cost_analysis.get("best_value"):
            best_value = cost_analysis["best_value"]
            logger.info(f"   Best Value: {best_value['model_name']} (${best_value['estimated_cost']:.4f})")
        
        if cost_analysis.get("most_economical"):
            economical = cost_analysis["most_economical"]
            logger.info(f"   Most Economical: {economical['model_name']} (${economical['estimated_cost']:.4f})")
        
        # Test budget optimization
        budget_result = service.optimize_for_budget(request, max_budget=0.001)
        logger.info(f"💵 Budget optimization for $0.001:")
        logger.info(f"   Recommended: {budget_result.get('recommended_model', 'N/A')}")
        logger.info(f"   Cost: ${budget_result.get('estimated_cost', 0):.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cost optimization test failed: {e}")
        return False

def test_style_evaluation():
    """Test style-specific evaluation."""
    logger = get_logger()
    logger.info("🎨 Testing style-specific evaluation")
    
    service = OpenRouterAIService()
    
    test_bios = {
        "professional": "Experienced Software Engineer with 5+ years developing scalable applications. Led team of 4 developers, delivered 15+ projects with 99.9% uptime. Expert in Python, JavaScript, and cloud technologies.",
        "creative": "I'm a code artist who loves crafting digital experiences! 🎨 My journey includes building apps that spark joy and solve real problems. When I'm not coding, I'm exploring new tech and sharing knowledge with the community.",
        "technical": "Senior Software Engineer specializing in distributed systems architecture. Optimized database performance by 300%, implemented microservices handling 1M+ requests/day. Expert in system design, scalability, and performance optimization."
    }
    
    try:
        for style, bio in test_bios.items():
            logger.info(f"\n📝 Evaluating {style} bio:")
            evaluation = service.evaluate_bio_by_style(bio, style)
            
            logger.info(f"   Overall Score: {evaluation['overall_score']:.1f}/100")
            logger.info(f"   Style Compliance: {evaluation['style_compliance']}")
            
            if evaluation.get('category_scores'):
                logger.info("   Category Scores:")
                for category, score in evaluation['category_scores'].items():
                    logger.info(f"     {category.replace('_', ' ').title()}: {score:.1f}/100")
            
            if evaluation.get('feedback'):
                logger.info("   Feedback:")
                for feedback in evaluation['feedback']:
                    logger.info(f"     • {feedback}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Style evaluation test failed: {e}")
        return False

if __name__ == "__main__":
    logger = get_logger()
    logger.info("🚀 Starting OpenRouter enhancement tests")
    
    tests = [
        ("SSL Error Handling & Fallback", test_ssl_error_handling),
        ("Cost Optimization", test_cost_optimization),
        ("Style-Specific Evaluation", test_style_evaluation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info('='*50)
        
        if test_func():
            logger.info(f"✅ {test_name} PASSED")
            passed += 1
        else:
            logger.info(f"❌ {test_name} FAILED")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The enhanced system is working correctly.")
    else:
        logger.info("⚠️  Some tests failed. Check the logs above for details.")
    
    logger.info('='*50)