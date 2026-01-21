# MALRS-Frontend

This is the frontend for the Multi-Agent Literature Review System (MALRS). It is a React-based application built with Vite and TypeScript, designed to provide an interface for the Agentic AI-powered novelty assessment platform.

## Features

-   **Tabbed Interface**: Easily switch between configuring input, viewing results, and managing your paper library.
-   **File Management**: Upload and manage research papers for analysis.
-   **Dynamic Analysis**: Configure and run analysis on your research ideas and papers.
-   **Interactive Visualizations**: View the results of your analysis with interactive components.
-   **Responsive Design**: The application is designed to work on various screen sizes.

## Technologies Used

-   **React**: A JavaScript library for building user interfaces.
-   **Vite**: A fast build tool for modern web projects.
-   **TypeScript**: A typed superset of JavaScript that compiles to plain JavaScript.
-   **Tailwind CSS**: A utility-first CSS framework for rapid UI development.
-   **shadcn/ui**: A collection of re-usable components built with Radix UI and Tailwind CSS.
-   **React Router**: For declarative routing in the application.
-   **Framer Motion**: For animations and transitions.
-   **TanStack Query**: For data fetching and state management.

## Getting Started

### Prerequisites

-   Node.js (v18 or higher recommended)
-   npm, pnpm, or bun

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    ```
2.  Navigate to the `MALRS-Frontend` directory:
    ```bash
    cd MALRS-Frontend
    ```
3.  Install the dependencies:
    ```bash
    npm install
    # or
    pnpm install
    # or
    bun install
    ```

### Running the Development Server

To run the application in development mode, use the following command:

```bash
npm run dev
```

This will start the Vite development server, and you can view the application at `http://localhost:5173`.

## Available Scripts

-   `npm run dev`: Starts the development server.
-   `npm run build`: Builds the application for production.
-   `npm run lint`: Lints the source code using ESLint.
-   `npm run preview`: Starts a local server to preview the production build.
-   `npm run test`: Runs the tests using Vitest.

## Project Structure

```
MALRS-Frontend/
├── public/                # Static assets
├── src/
│   ├── components/        # Reusable components
│   │   ├── tabs/          # Components for the different tabs
│   │   └── ui/            # UI components from shadcn/ui
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility functions
│   ├── pages/             # Application pages
│   ├── test/              # Test files
│   ├── App.tsx            # Main application component
│   ├── main.tsx           # Entry point of the application
│   └── index.css          # Global styles
├── .eslintrc.cjs          # ESLint configuration
├── postcss.config.js      # PostCSS configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
└── vite.config.ts       # Vite configuration
```
