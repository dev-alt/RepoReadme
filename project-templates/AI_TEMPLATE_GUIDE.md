# AI Agent Guide: Portfolio Project Template Creation

This guide instructs AI agents on how to properly fill out project templates for the Dev-Alt portfolio website.

## Template Selection

Choose the appropriate template based on project type:

- **Web Development**: Frontend apps, static sites, React/Next.js projects
- **Game Development**: Unity games, interactive experiences
- **Desktop Application**: Windows/cross-platform desktop tools
- **Mobile App**: iOS/Android applications
- **API**: Backend services, REST APIs, microservices  
- **Full-Stack Application**: Complete web apps with backend integration

## Required Field Instructions

### Basic Identifiers
```json
{
  "id": "project-name-kebab-case",
  "title": "Human Readable Project Title",
  "slug": "project-name-kebab-case"
}
```
- **id**: Lowercase, hyphen-separated, unique identifier
- **title**: Proper case, spaces allowed, display name
- **slug**: Usually identical to id, URL-friendly

### Project Description
```json
{
  "summary": "Brief one-line description of the project",
  "description": "Detailed multi-paragraph description with features, purpose, and technical highlights"
}
```
- **summary**: 1 sentence, under 100 characters
- **description**: 2-4 paragraphs, include features and technical details

### Classification
```json
{
  "category": "Web Development",
  "status": "Completed",
  "dateCreated": "2024-01-15",
  "dateUpdated": "2024-02-20"
}
```
- **category**: Use exact strings from template options
- **status**: "Completed", "In Development", "In Progress", or "Archived"
- **dates**: YYYY-MM-DD format

### Technology Stack
```json
{
  "technologies": [
    { 
      "name": "React", 
      "icon": "logos:react", 
      "category": "Frontend" 
    }
  ]
}
```

**Technology Categories:**
- Frontend, Backend, Database, Language, Framework
- Game Engine, Mobile, Desktop, API, Testing
- DevOps, Build System, Architecture

**Common Icons:**
- React: `logos:react`
- TypeScript: `logos:typescript-icon`
- Unity: `logos:unity`
- C#: `logos:c-sharp`
- Node.js: `logos:nodejs-icon`
- PostgreSQL: `logos:postgresql`

### Architecture
```json
{
  "architecture": "Model-View-ViewModel (MVVM)"
}
```
**Common Patterns:**
- "Next.js App Router with React Context API"
- "Model-View-ViewModel (MVVM)"
- "Component-based architecture with Unity"
- "RESTful API with MVC pattern"

### Technical Details
```json
{
  "technicalDetails": [
    {
      "title": "Feature Name",
      "description": "Brief explanation of the technical implementation",
      "codeSnippet": "public class Example { ... }"
    }
  ]
}
```
- Include 2-4 key technical implementations
- Code snippets should be real, functional examples
- Focus on unique or complex features

### Images
```json
{
  "images": [
    {
      "url": "/Projects/ProjectName_Main.png",
      "alt": "ProjectName Main Interface",
      "width": 1920,
      "height": 1080,
      "isFeatured": true
    }
  ]
}
```
**Image Guidelines:**
- Path format: `/Projects/ProjectName_DescriptiveName.png`
- Standard dimensions: 1920x1080 for desktop, 375x812 for mobile
- Always include descriptive alt text
- Mark primary screenshot as `isFeatured: true`

### Links
```json
{
  "links": [
    {
      "type": "github",
      "url": "https://github.com/dev-alt/project-repo",
      "label": "Source Code"
    }
  ]
}
```
**Link Types:**
- `github`: Source code repository
- `demo`: Live application/demo
- `download`: Downloadable application
- `documentation`: API docs or user guides

### Key Points
```json
{
  "keyPoints": [
    "Modern React application with TypeScript",
    "Responsive design with Tailwind CSS",
    "Real-time data synchronization",
    "Cross-platform compatibility"
  ]
}
```
- 4-8 bullet points highlighting main features
- Focus on technical achievements and user benefits
- Use present tense, active voice

## Project-Specific Guidelines

### Game Development Projects
- Include gameplay mechanics in keyPoints
- Mention Unity version if relevant
- Include platform compatibility
- Add system requirements in description

### Web Development Projects  
- Emphasize responsive design
- Include deployment platform
- Mention performance optimizations
- Add accessibility features

### Desktop Applications
- Specify supported operating systems
- Include installation requirements
- Mention UI framework used
- Add file handling capabilities

### Mobile Apps
- Specify iOS/Android compatibility
- Include app store links if published
- Mention device permissions used
- Add offline functionality details

### APIs
- Include endpoint documentation
- Mention authentication methods
- Add rate limiting details
- Include supported data formats

## Quality Checklist

Before finalizing, verify:

- [ ] All placeholder text (PROJECT_NAME, APP_NAME) replaced
- [ ] Valid JSON syntax with proper escaping
- [ ] Dates in YYYY-MM-DD format
- [ ] Technology icons exist and are correct
- [ ] Image paths follow naming convention
- [ ] GitHub URLs point to actual repositories
- [ ] Key points are specific and technical
- [ ] Description includes practical benefits
- [ ] No duplicate information between fields
- [ ] Status reflects actual project state

## Example Workflow

1. **Gather Information**: Collect project details, repository URL, tech stack
2. **Select Template**: Choose based on primary project type
3. **Fill Basic Fields**: ID, title, summary, dates
4. **Add Technologies**: Include all major tools and frameworks
5. **Write Description**: 2-4 paragraphs with features and purpose
6. **Add Technical Details**: 2-4 key implementation highlights
7. **Configure Images**: At least one main screenshot
8. **Set Links**: GitHub (required), demo/download (if available)
9. **List Key Points**: 4-8 technical achievements
10. **Validate**: Check JSON syntax and completeness

## Common Mistakes to Avoid

- Don't use placeholder text in final output
- Don't duplicate technology entries
- Don't use vague descriptions ("modern app")
- Don't forget to update image paths
- Don't leave required fields empty
- Don't use incorrect date formats
- Don't mix categories inappropriately