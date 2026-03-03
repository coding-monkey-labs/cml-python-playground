# FluxBoard

A modern, extensible dashboard builder inspired by Grafana. Built with React, TypeScript, and Redux Toolkit.

## Features

### Panel Types (11)
- **Stat** - Single value display with sparkline
- **Gauge** - SVG arc gauge with thresholds
- **Time Series** - Line/area charts with Recharts
- **Graph** - Alias for Time Series
- **Table** - Sortable data table with status highlighting
- **Bar Chart** - Horizontal/vertical bar charts
- **Pie Chart** - Pie and donut charts
- **Heatmap** - SVG heatmap grid visualization
- **Logs** - Log viewer with level coloring
- **Alert List** - Active alerts with severity/state
- **Text** - Markdown/HTML/code content

### Dashboard Features
- Grid-based panel layout (12-column)
- Panel editing (title, type, queries, options, thresholds)
- Add / duplicate / remove panels
- Dashboard title editing
- Dashboard tags
- Save dashboard
- Dashboard settings modal

### Data & Query System
- Variable interpolation (`$variable` / `${variable}` syntax)
- Demo data generation for all panel types
- Query editor with multiple queries per panel
- Data transformation pipeline (filter, sort, group, calculate, organize, reduce)
- Auto-refresh (configurable interval)

### UI/UX
- Dark/Light theme toggle with CSS variables
- Time range picker with presets
- Variable controls bar
- Sidebar navigation
- Toast notifications
- Responsive layout

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build

```bash
npm run build
npm run preview
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Redux Toolkit** - State management
- **Recharts** - Charts library
- **Vite** - Build tool
- **CSS Variables** - Theming

## Project Structure

```
src/
├── components/           25 React components
│   ├── Dashboard/        Main dashboard grid
│   ├── DashboardHeader/  Top toolbar
│   ├── PanelRenderer/    Panel type routing
│   ├── PanelContainer/   Panel wrapper with data fetching
│   ├── PanelEditor/      Panel configuration modal
│   ├── GridLayout/       CSS grid layout
│   ├── GaugePanel/       SVG gauge visualization
│   ├── StatPanel/        Stat with sparkline
│   ├── TimeSeriesPanel/  Recharts line/area charts
│   ├── GraphPanel/       Graph (TimeSeries alias)
│   ├── TablePanel/       Data table
│   ├── BarChartPanel/    Bar chart
│   ├── PieChartPanel/    Pie/donut chart
│   ├── HeatmapPanel/     SVG heatmap
│   ├── LogsPanel/        Log viewer
│   ├── AlertListPanel/   Alert list
│   ├── TextPanel/        Markdown/HTML/code
│   ├── ThemeToggle/      Dark/light switch
│   ├── VariableControls/ Variable dropdowns
│   ├── TimeRangePicker/  Time range selection
│   ├── QueryEditor/      Query configuration
│   ├── AddPanelWidget/   Add new panels
│   ├── DashboardSettings/ Dashboard config modal
│   ├── Sidebar/          Navigation sidebar
│   └── Notification/     Toast notifications
├── services/             Data services
│   ├── queryService.ts   Query execution & demo data
│   ├── dataTransformService.ts  Data transformations
│   └── apiService.ts     Simulated API
├── store/                Redux state
│   ├── index.ts          Store config
│   ├── dashboardSlice.ts Dashboard state
│   └── themeSlice.ts     Theme state
├── types/                TypeScript definitions
│   └── dashboard.ts      All type definitions
├── utils/                Utilities
│   ├── variableInterpolation.ts
│   └── formatting.ts
├── App.tsx               Main app component
├── main.tsx              Entry point
├── index.css             Global styles & theme
└── App.css               App layout styles
```
