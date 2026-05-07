"""Tests for React codebase feature parser."""

import os
import tempfile

from engineering_intelligence.services.feature_parser import (
    ParseResult,
    build_hierarchy_from_parse,
    parse_codebase,
    _dir_to_feature_name,
    _route_to_feature_name,
)


class TestParseCodebase:
    def test_detects_function_component(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            comp_dir = os.path.join(tmpdir, "src", "components", "auth")
            os.makedirs(comp_dir)
            with open(os.path.join(comp_dir, "LoginForm.tsx"), "w") as f:
                f.write("""
import React from 'react';
import { useAuth } from '../hooks/useAuth';

export default function LoginForm() {
    return <div>Login</div>;
}
""")
            result = parse_codebase(tmpdir)
            assert len(result.components) == 1
            assert result.components[0].name == "LoginForm"
            assert result.components[0].component_type == "component"

    def test_detects_arrow_component(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            comp_dir = os.path.join(tmpdir, "src", "components")
            os.makedirs(comp_dir)
            with open(os.path.join(comp_dir, "Button.tsx"), "w") as f:
                f.write("""
export const Button = () => {
    return <button>Click</button>;
};
""")
            result = parse_codebase(tmpdir)
            assert len(result.components) == 1
            assert result.components[0].name == "Button"

    def test_detects_hooks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            hook_dir = os.path.join(tmpdir, "src", "hooks")
            os.makedirs(hook_dir)
            with open(os.path.join(hook_dir, "useAuth.ts"), "w") as f:
                f.write("""
export function useAuth() {
    return { isLoggedIn: true };
}
""")
            result = parse_codebase(tmpdir)
            assert len(result.components) == 1
            assert result.components[0].name == "useAuth"
            assert result.components[0].component_type == "hook"

    def test_detects_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx_dir = os.path.join(tmpdir, "src", "context")
            os.makedirs(ctx_dir)
            with open(os.path.join(ctx_dir, "ThemeContext.tsx"), "w") as f:
                f.write("""
import React from 'react';
export const ThemeContext = React.createContext({ dark: false });
""")
            result = parse_codebase(tmpdir)
            assert any(c.name == "ThemeContext" for c in result.components)
            theme = [c for c in result.components if c.name == "ThemeContext"][0]
            assert theme.component_type == "context"

    def test_detects_page_by_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            page_dir = os.path.join(tmpdir, "src", "pages")
            os.makedirs(page_dir)
            with open(os.path.join(page_dir, "Dashboard.tsx"), "w") as f:
                f.write("""
export default function Dashboard() {
    return <div>Dashboard</div>;
}
""")
            result = parse_codebase(tmpdir)
            assert result.components[0].component_type == "page"

    def test_detects_routes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "src"))
            with open(os.path.join(tmpdir, "src", "App.tsx"), "w") as f:
                f.write("""
import { Route } from 'react-router-dom';

function App() {
    return (
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/settings" element={<SettingsPage />} />
    );
}
""")
            result = parse_codebase(tmpdir)
            assert len(result.routes) == 2
            assert result.routes[0].path == "/dashboard"
            assert result.routes[0].component_name == "Dashboard"
            assert result.routes[1].path == "/settings"
            assert result.routes[1].component_name == "SettingsPage"

    def test_feature_groups_by_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            auth_dir = os.path.join(tmpdir, "src", "features", "auth")
            os.makedirs(auth_dir)
            with open(os.path.join(auth_dir, "LoginForm.tsx"), "w") as f:
                f.write("export function LoginForm() { return null; }")
            with open(os.path.join(auth_dir, "RegisterForm.tsx"), "w") as f:
                f.write("export function RegisterForm() { return null; }")

            result = parse_codebase(tmpdir)
            assert "Auth" in result.feature_groups
            assert "LoginForm" in result.feature_groups["Auth"]
            assert "RegisterForm" in result.feature_groups["Auth"]

    def test_skips_node_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nm_dir = os.path.join(tmpdir, "node_modules", "react")
            os.makedirs(nm_dir)
            with open(os.path.join(nm_dir, "index.js"), "w") as f:
                f.write("export function React() {}")

            result = parse_codebase(tmpdir)
            assert len(result.components) == 0

    def test_imports_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            comp_dir = os.path.join(tmpdir, "src")
            os.makedirs(comp_dir)
            with open(os.path.join(comp_dir, "App.tsx"), "w") as f:
                f.write("""
import React from 'react';
import { Button } from './components/Button';

export function App() { return null; }
""")
            result = parse_codebase(tmpdir)
            assert len(result.components) == 1
            assert "react" in result.components[0].imports
            assert "./components/Button" in result.components[0].imports

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = parse_codebase(tmpdir)
            assert len(result.components) == 0
            assert len(result.routes) == 0
            assert len(result.feature_groups) == 0


class TestHelpers:
    def test_dir_to_feature_name(self):
        assert _dir_to_feature_name("src/features/auth") == "Auth"
        assert _dir_to_feature_name("src/components/dashboard") == "Dashboard"

    def test_route_to_feature_name(self):
        assert _route_to_feature_name("/dashboard") == "Dashboard"
        assert _route_to_feature_name("/settings/profile") == "Settings"
        assert _route_to_feature_name("/") == "Root"

    def test_parse_result_to_dict(self):
        result = ParseResult(components=[], routes=[], feature_groups={"Auth": ["Login"]})
        d = result.to_dict()
        assert d["components"] == []
        assert d["routes"] == []
        assert d["feature_groups"] == {"Auth": ["Login"]}


class TestBuildHierarchy:
    def test_route_based_hierarchy(self):
        from engineering_intelligence.services.feature_parser import ParsedComponent, ParsedRoute
        result = ParseResult(
            components=[
                ParsedComponent(name="Dashboard", file_path="pages/Dashboard.tsx", component_type="page"),
                ParsedComponent(name="Sidebar", file_path="components/Sidebar.tsx", component_type="component"),
            ],
            routes=[
                ParsedRoute(path="/dashboard", component_name="Dashboard", file_path="App.tsx"),
            ],
            feature_groups={"Components": ["Sidebar"]},
        )
        hierarchy = build_hierarchy_from_parse(result)
        assert "Dashboard" in hierarchy
        assert "Dashboard" in hierarchy["Dashboard"]
        assert "Components" in hierarchy
        assert "Sidebar" in hierarchy["Components"]
