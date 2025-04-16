# Talent Matcher Frontend

This is the frontend application for the Talent Matcher system, a platform that uses knowledge graph technology to match candidates with jobs based on skills and requirements.

## Tech Stack

- **Framework**: Next.js (React framework)
- **Styling**: Tailwind CSS
- **Language**: TypeScript
- **Data Visualization**: D3.js
- **API Integration**: Client-side API calls to backend endpoints

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn

### Installation

1. Clone the repository
2. Navigate to the frontend directory:
   ```
   cd frontend
   ```
3. Install dependencies:
   ```
   npm install
   # or
   yarn install
   ```
4. Create a `.env.local` file in the frontend directory with the following content:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```
   Adjust the URL according to your backend setup.

### Development

Run the development server:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

### Build for Production

To build the application for production:

```bash
npm run build
# or
yarn build
```

To start the production server:

```bash
npm run start
# or
yarn start
```

## Project Structure

- `/app` - Next.js app router pages
- `/components` - Reusable UI components
- `/lib` - API client and utility functions
- `/types` - TypeScript type definitions
- `/public` - Static assets

## Main Features

1. **Job Listing & Details**: Browse and search available jobs with matching capabilities
2. **Candidate Profiles**: View candidate information and skill profiles
3. **Skill Visualization**: Interactive graphs showing skill relationships
4. **Matching Analysis**: View and analyze matches between candidates and jobs
5. **Skill Gap Analysis**: Identify missing skills and recommendations

## API Integration

The frontend communicates with the backend through a set of API client functions in `/lib/api.ts`. These functions handle all requests to the backend endpoints.

## Contributing

1. Follow the existing code style and conventions
2. Create feature branches for new functionality
3. Write tests for new features
4. Submit pull requests for review
