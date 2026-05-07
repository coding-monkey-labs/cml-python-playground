"""Feature graph parser — scans a React/TypeScript codebase to detect components and build a feature hierarchy."""

import os
import re
from dataclasses import dataclass, field


@dataclass
class ParsedComponent:
    """A detected React component or module."""

    name: str
    file_path: str
    component_type: str  # "component" | "page" | "route" | "hook" | "context" | "module"
    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)


@dataclass
class ParsedRoute:
    """A detected route from React Router definitions."""

    path: str
    component_name: str
    file_path: str


@dataclass
class ParseResult:
    """Result of parsing a React codebase."""

    components: list[ParsedComponent]
    routes: list[ParsedRoute]
    feature_groups: dict[str, list[str]]  # directory -> [component names]

    def to_dict(self) -> dict:
        return {
            "components": [
                {
                    "name": c.name,
                    "file_path": c.file_path,
                    "type": c.component_type,
                    "imports": c.imports,
                    "exports": c.exports,
                }
                for c in self.components
            ],
            "routes": [
                {"path": r.path, "component": r.component_name, "file": r.file_path}
                for r in self.routes
            ],
            "feature_groups": self.feature_groups,
        }


# ── Regex patterns for React/TS parsing ───────────────────────────────────────

_COMPONENT_PATTERNS = [
    # function Component() or const Component = () =>
    re.compile(r"(?:export\s+)?(?:default\s+)?function\s+([A-Z]\w+)\s*\("),
    re.compile(r"(?:export\s+)?(?:default\s+)?const\s+([A-Z]\w+)\s*[=:]\s*(?:\([^)]*\)|[^=])*=>"),
    re.compile(r"(?:export\s+)?(?:default\s+)?class\s+([A-Z]\w+)\s+extends\s+(?:React\.)?(?:Component|PureComponent)"),
]

_HOOK_PATTERN = re.compile(r"(?:export\s+)?(?:default\s+)?(?:function|const)\s+(use[A-Z]\w+)")

_CONTEXT_PATTERN = re.compile(r"(?:export\s+)?const\s+(\w+Context)\s*=\s*(?:React\.)?createContext")

_IMPORT_PATTERN = re.compile(r"import\s+(?:{[^}]+}|\w+)\s+from\s+['\"]([^'\"]+)['\"]")

_EXPORT_PATTERN = re.compile(r"export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)")

_ROUTE_PATTERNS = [
    # <Route path="/foo" component={Bar} />  or element={<Bar />}
    re.compile(r'<Route[^>]*path=["\']([^"\']+)["\'][^>]*(?:component=\{(\w+)\}|element=\{<(\w+))'),
    # { path: "/foo", component: Bar } or element: <Bar />
    re.compile(r'path:\s*["\']([^"\']+)["\'].*?(?:component:\s*(\w+)|element:\s*<(\w+))'),
]

# File extensions to scan
_EXTENSIONS = {".tsx", ".ts", ".jsx", ".js"}

# Directories to skip
_SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", "coverage"}


def parse_codebase(root_path: str) -> ParseResult:
    """Walk a React/TS codebase and extract components, routes, and feature groups."""
    components: list[ParsedComponent] = []
    routes: list[ParsedRoute] = []
    feature_groups: dict[str, list[str]] = {}

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune skip directories
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]

        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext not in _EXTENSIONS:
                continue

            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root_path)

            try:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError:
                continue

            file_components = _parse_file(content, rel_path)
            components.extend(file_components)

            file_routes = _parse_routes(content, rel_path)
            routes.extend(file_routes)

            # Group by parent directory as feature
            parent_dir = os.path.dirname(rel_path)
            if parent_dir and file_components:
                group_name = _dir_to_feature_name(parent_dir)
                if group_name not in feature_groups:
                    feature_groups[group_name] = []
                for comp in file_components:
                    feature_groups[group_name].append(comp.name)

    return ParseResult(
        components=components,
        routes=routes,
        feature_groups=feature_groups,
    )


def _parse_file(content: str, rel_path: str) -> list[ParsedComponent]:
    """Extract components, hooks, and contexts from a single file."""
    results: list[ParsedComponent] = []

    # Collect imports
    imports = [m.group(1) for m in _IMPORT_PATTERN.finditer(content)]
    exports = [m.group(1) for m in _EXPORT_PATTERN.finditer(content)]

    # Detect hooks
    for match in _HOOK_PATTERN.finditer(content):
        results.append(ParsedComponent(
            name=match.group(1),
            file_path=rel_path,
            component_type="hook",
            imports=imports,
            exports=exports,
        ))

    # Detect contexts
    for match in _CONTEXT_PATTERN.finditer(content):
        results.append(ParsedComponent(
            name=match.group(1),
            file_path=rel_path,
            component_type="context",
            imports=imports,
            exports=exports,
        ))

    # Detect components (skip names already captured as hooks/contexts)
    captured_names = {c.name for c in results}
    for pattern in _COMPONENT_PATTERNS:
        for match in pattern.finditer(content):
            name = match.group(1)
            if name in captured_names:
                continue
            captured_names.add(name)

            # Classify component type
            comp_type = _classify_component(name, rel_path, content)
            results.append(ParsedComponent(
                name=name,
                file_path=rel_path,
                component_type=comp_type,
                imports=imports,
                exports=exports,
            ))

    return results


def _parse_routes(content: str, rel_path: str) -> list[ParsedRoute]:
    """Extract route definitions from file content."""
    routes: list[ParsedRoute] = []
    for pattern in _ROUTE_PATTERNS:
        for match in pattern.finditer(content):
            path = match.group(1)
            component = match.group(2) or match.group(3) or "Unknown"
            routes.append(ParsedRoute(
                path=path,
                component_name=component,
                file_path=rel_path,
            ))
    return routes


def _classify_component(name: str, rel_path: str, content: str) -> str:
    """Classify a component as page, route, or regular component based on heuristics."""
    lower_path = rel_path.lower()

    if any(segment in lower_path for segment in ["pages/", "views/", "screens/"]):
        return "page"
    if "route" in lower_path or "router" in lower_path:
        return "route"
    if name.endswith("Page") or name.endswith("View") or name.endswith("Screen"):
        return "page"

    return "component"


def _dir_to_feature_name(dir_path: str) -> str:
    """Convert a directory path to a human-readable feature name."""
    # src/components/auth/LoginForm.tsx -> "Auth"
    # src/features/dashboard -> "Dashboard"
    parts = dir_path.replace("\\", "/").split("/")

    # Remove common non-feature prefixes
    skip = {"src", "app", "components", "features", "modules", "lib", "shared", "common"}
    meaningful = [p for p in parts if p.lower() not in skip and p]

    if meaningful:
        # Take the most meaningful part and title-case it
        name = meaningful[-1]
        return name[0].upper() + name[1:] if name else dir_path
    return parts[-1] if parts else dir_path


def build_hierarchy_from_parse(result: ParseResult) -> dict[str, list[str]]:
    """Build a feature -> subfeatures mapping from parse results.

    Uses routes as top-level features, then groups components under them.
    Falls back to directory-based grouping.
    """
    hierarchy: dict[str, list[str]] = {}

    # Route-based features take priority
    route_components = {r.component_name for r in result.routes}
    for route in result.routes:
        feature_name = _route_to_feature_name(route.path)
        if feature_name not in hierarchy:
            hierarchy[feature_name] = []
        hierarchy[feature_name].append(route.component_name)

    # Directory-based grouping for non-route components
    for group_name, comp_names in result.feature_groups.items():
        for comp in comp_names:
            if comp not in route_components:
                if group_name not in hierarchy:
                    hierarchy[group_name] = []
                hierarchy[group_name].append(comp)

    return hierarchy


def _route_to_feature_name(path: str) -> str:
    """Convert a route path to a feature name. /settings/profile -> Settings."""
    parts = [p for p in path.strip("/").split("/") if p and not p.startswith(":")]
    if parts:
        name = parts[0]
        return name[0].upper() + name[1:] if name else "Root"
    return "Root"
