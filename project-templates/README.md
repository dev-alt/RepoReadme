# Project Templates

This directory contains JSON templates for creating new portfolio projects. Each template follows the established project data structure and includes common patterns found in existing projects.

## Available Templates

### Web Development (`web-development-template.json`)
- **Tech Stack:** Next.js, React, TypeScript, Tailwind CSS
- **Architecture:** Next.js App Router with React Context API
- **Use for:** Frontend applications, static sites, client-side applications

### Game Development (`game-development-template.json`)
- **Tech Stack:** Unity, C#
- **Architecture:** Component-based architecture with Unity
- **Use for:** 2D/3D games, interactive experiences

### Desktop Application (`desktop-application-template.json`)
- **Tech Stack:** C#, .NET
- **Architecture:** Model-View-ViewModel (MVVM)
- **Use for:** Windows/cross-platform desktop utilities, tools

### Mobile App (`mobile-app-template.json`)
- **Tech Stack:** React Native, TypeScript, Expo
- **Architecture:** React Native with Expo
- **Use for:** iOS/Android mobile applications

### API (`api-template.json`)
- **Tech Stack:** Node.js, Express, TypeScript, PostgreSQL
- **Architecture:** RESTful API with MVC pattern
- **Use for:** Backend services, REST APIs, microservices

### Full-Stack Application (`full-stack-template.json`)
- **Tech Stack:** Next.js, React, TypeScript, Tailwind, Node.js, PostgreSQL, Prisma
- **Architecture:** Full-stack Next.js with API routes and database
- **Use for:** Complete web applications with backend integration

## Usage Instructions

1. **Copy Template:** Choose the appropriate template for your project type
2. **Fill Required Fields:**
   - `id` - Unique project identifier (kebab-case)
   - `title` - Project display name
   - `slug` - URL-friendly version of title (usually same as id)
   - `summary` - Brief one-line description
   - `description` - Detailed project description
   - `dateCreated` - Project start date (YYYY-MM-DD format)
   - `dateUpdated` - Last modification date (YYYY-MM-DD format)

3. **Customize Technology Stack:** Modify the `technologies` array as needed
4. **Update Architecture:** Adjust the `architecture` field if using different patterns
5. **Add Technical Details:** Fill in `technicalDetails` with actual implementations
6. **Replace Placeholders:**
   - `PROJECT_NAME` - Your project name
   - `PROJECT_REPO` - GitHub repository name
   - `APP_NAME` - Application name
   - Image URLs and alt text

7. **Add Images:** Update image paths and dimensions
8. **Update Links:** Replace placeholder URLs with actual GitHub/demo links
9. **Customize Key Points:** Replace with project-specific highlights

## Project Data Location

Save completed project files in: `frontend/src/data/projects/PROJECT_ID.json`

## Common Technology Icons

Popular icon options for the `technologies` array:

**Frontend:**
- React: `logos:react`
- Vue: `logos:vue`
- Angular: `logos:angular-icon`
- Svelte: `logos:svelte-icon`

**Languages:**
- TypeScript: `logos:typescript-icon`
- JavaScript: `logos:javascript`
- Python: `logos:python`
- C#: `logos:c-sharp`
- Java: `logos:java`

**Frameworks:**
- Next.js: `logos:nextjs-icon`
- Express: `logos:express`
- Django: `logos:django-icon`
- .NET: `logos:dotnet`

**Databases:**
- PostgreSQL: `logos:postgresql`
- MongoDB: `logos:mongodb-icon`
- SQLite: `logos:sqlite`
- MySQL: `logos:mysql-icon`

**Tools:**
- Docker: `logos:docker-icon`
- Git: `logos:git-icon`
- Unity: `logos:unity`
- Figma: `logos:figma`

## Status Options

- `"In Development"` - Currently being worked on
- `"In Progress"` - Active development
- `"Completed"` - Finished project
- `"Archived"` - No longer maintained

## Category Options

- `"Web Development"`
- `"Game Development"`
- `"Desktop Application"`
- `"Mobile App"`
- `"API"`
- `"Full-Stack Application"`
- `"Other"`