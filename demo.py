#!/usr/bin/env python3
"""
RepoReadme - Command Line Demo

Demonstrates the core functionality of RepoReadme without GUI.
Perfect for testing and automation.
"""

import sys
import os
sys.path.insert(0, 'src')

from analyzers.repository_analyzer import RepositoryAnalyzer, ProjectMetadata
from templates.readme_templates import ReadmeTemplateEngine, TemplateConfig
import argparse
import time

def main():
    parser = argparse.ArgumentParser(description='RepoReadme - Automatic README Generator')
    parser.add_argument('repository_path', help='Path to repository to analyze')
    parser.add_argument('--template', choices=['modern', 'classic', 'minimalist', 'developer', 'academic', 'corporate'], 
                       default='modern', help='README template to use')
    parser.add_argument('--output', '-o', help='Output file path (default: README_generated.md)')
    parser.add_argument('--no-badges', action='store_true', help='Disable badges')
    parser.add_argument('--no-toc', action='store_true', help='Disable table of contents')
    parser.add_argument('--emoji-style', choices=['unicode', 'github', 'none'], 
                       default='unicode', help='Emoji style to use')
    
    args = parser.parse_args()
    
    # Validate repository path
    if not os.path.exists(args.repository_path):
        print(f"❌ Error: Repository path '{args.repository_path}' does not exist")
        sys.exit(1)
    
    repo_name = os.path.basename(os.path.abspath(args.repository_path))
    output_path = args.output or f"{repo_name}_README.md"
    
    print("🚀 RepoReadme - Automatic README Generator")
    print("=" * 50)
    print(f"📁 Repository: {repo_name}")
    print(f"📂 Path: {args.repository_path}")
    print(f"🎨 Template: {args.template}")
    print(f"💾 Output: {output_path}")
    print()
    
    try:
        # Step 1: Analyze Repository
        print("🔍 Step 1: Analyzing repository...")
        start_time = time.time()
        
        analyzer = RepositoryAnalyzer()
        metadata = analyzer.analyze_repository(args.repository_path, repo_name)
        
        analysis_time = time.time() - start_time
        print(f"✅ Analysis completed in {analysis_time:.2f}s")
        
        # Display analysis summary
        print(f"   📊 Found {metadata.total_files:,} files")
        print(f"   💻 Primary language: {metadata.primary_language}")
        print(f"   🏗️ Project type: {metadata.project_type}")
        print(f"   📈 Lines of code: {metadata.code_lines:,}")
        if metadata.frameworks:
            print(f"   🛠️ Frameworks: {', '.join(metadata.frameworks)}")
        print(f"   🎯 Quality score: {metadata.code_quality_score:.1f}/100")
        print()
        
        # Step 2: Generate README
        print("📝 Step 2: Generating README...")
        start_time = time.time()
        
        # Create template configuration
        config = TemplateConfig(
            template_name=args.template,
            include_badges=not args.no_badges,
            include_toc=not args.no_toc,
            emoji_style=args.emoji_style,
            include_api_docs=True,
            include_contributing=True,
            include_license_section=True
        )
        
        template_engine = ReadmeTemplateEngine()
        readme_content = template_engine.generate_readme(metadata, config)
        
        generation_time = time.time() - start_time
        print(f"✅ README generated in {generation_time:.2f}s")
        print(f"   📏 Content length: {len(readme_content):,} characters")
        print(f"   📄 Lines: {len(readme_content.splitlines())}")
        print()
        
        # Step 3: Save to file
        print("💾 Step 3: Saving README...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        file_size = os.path.getsize(output_path)
        print(f"✅ README saved to {output_path}")
        print(f"   💽 File size: {file_size:,} bytes")
        print()
        
        # Success summary
        print("🎉 SUCCESS! README Generated")
        print("=" * 30)
        print(f"📁 Repository: {repo_name}")
        print(f"🎨 Template: {args.template}")
        print(f"💾 Output: {output_path}")
        print(f"⏱️ Total time: {analysis_time + generation_time:.2f}s")
        print()
        
        # Show preview
        print("👁️ Preview (first 10 lines):")
        print("-" * 30)
        lines = readme_content.splitlines()
        for i, line in enumerate(lines[:10], 1):
            print(f"{i:2d}: {line}")
        if len(lines) > 10:
            print(f"... and {len(lines) - 10} more lines")
        print()
        
        print("💡 Open the generated file in your editor or markdown viewer!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"💡 Make sure the repository path is valid and accessible")
        sys.exit(1)

if __name__ == "__main__":
    main()