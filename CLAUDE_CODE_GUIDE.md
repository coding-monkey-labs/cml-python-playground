# FluxBoard - Development Guide

## Architecture Overview

FluxBoard follows a component-based architecture with centralized state management:

```
User Interaction → Redux Dispatch → State Update → Component Re-render
                                                  → Query Execution → Data Display
```

### Key Architectural Decisions
1. **Redux Toolkit** for all state (dashboard, panels, variables, UI state)
2. **CSS Variables** for theming (no CSS-in-JS dependency)
3. **Recharts** for chart rendering (lightweight, React-native)
4. **Demo data** via query service (no external API needed for development)
5. **CSS Grid** for dashboard layout

## Common Development Tasks

### Adding a New Panel Type

1. Create component in `src/components/NewPanel/NewPanel.tsx`
2. Add type to `PanelType` union in `src/types/dashboard.ts`
3. Register in `src/components/PanelRenderer/PanelRenderer.tsx`
4. Add demo data generator in `src/services/queryService.ts`
5. Add to panel type selector in `src/components/AddPanelWidget/AddPanelWidget.tsx`
6. Add options UI in `src/components/PanelEditor/PanelEditor.tsx`

### Adding a New Variable Type

1. Add type to `VariableType` union in `src/types/dashboard.ts`
2. Handle rendering in `src/components/VariableControls/VariableControls.tsx`
3. Handle interpolation in `src/utils/variableInterpolation.ts`

### Modifying Theme

Edit CSS variables in `src/index.css` under `:root` (dark) and `[data-theme="light"]`.

### Adding a New Transform

1. Add type to `TransformType` union in `src/types/dashboard.ts`
2. Implement in `src/services/dataTransformService.ts`

## Data Flow

```
Panel Mount
  → PanelContainer.tsx
    → executeQueries() [queryService.ts]
      → interpolateVariables() [variableInterpolation.ts]
      → generate demo data based on panel type
    → applyTransforms() [dataTransformService.ts]
    → PanelRenderer.tsx → specific panel component
      → renders with data
```

## File Locations Quick Reference

| What | Where |
|------|-------|
| Type definitions | `src/types/dashboard.ts` |
| Redux store | `src/store/` |
| Panel components | `src/components/*Panel/` |
| Query execution | `src/services/queryService.ts` |
| Data transforms | `src/services/dataTransformService.ts` |
| Variable system | `src/utils/variableInterpolation.ts` |
| Theme variables | `src/index.css` |
| Panel routing | `src/components/PanelRenderer/PanelRenderer.tsx` |
| Data fetching | `src/components/PanelContainer/PanelContainer.tsx` |
| Global state | `src/store/dashboardSlice.ts` |
