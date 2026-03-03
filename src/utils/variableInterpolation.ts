import { Variable } from '../types';

/**
 * Interpolate dashboard variables in a query expression.
 * Supports $variable and ${variable} syntax.
 */
export function interpolateVariables(expr: string, variables: Variable[]): string {
  let result = expr;

  for (const variable of variables) {
    // Replace ${variableName} syntax
    const bracketPattern = new RegExp(`\\$\\{${variable.name}\\}`, 'g');
    result = result.replace(bracketPattern, variable.current);

    // Replace $variableName syntax (not followed by alphanumeric/underscore)
    const dollarPattern = new RegExp(`\\$${variable.name}(?![a-zA-Z0-9_])`, 'g');
    result = result.replace(dollarPattern, variable.current);
  }

  return result;
}

/**
 * Extract variable names referenced in an expression.
 */
export function extractVariableNames(expr: string): string[] {
  const matches = new Set<string>();

  // Match ${variable} syntax
  const bracketRegex = /\$\{(\w+)\}/g;
  let match;
  while ((match = bracketRegex.exec(expr)) !== null) {
    matches.add(match[1]);
  }

  // Match $variable syntax
  const dollarRegex = /\$(\w+)/g;
  while ((match = dollarRegex.exec(expr)) !== null) {
    matches.add(match[1]);
  }

  return Array.from(matches);
}

/**
 * Check if an expression contains any variable references.
 */
export function hasVariables(expr: string): boolean {
  return /\$\{?\w+\}?/.test(expr);
}
