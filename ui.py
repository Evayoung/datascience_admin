"""Shared UI helpers for the admin app."""
from __future__ import annotations

from fasthtml.common import A, Button, Div, H1, P, Span, Title
from faststrap import Badge, Container, Icon

from schema import NAV_GROUPS, TABLES


PRIMARY_NAV = [
    ("dashboard", "/admin", "speedometer2", "Home"),
    ("profile", "/admin/resource/profile", "person-badge", "Profile"),
    ("projects", "/admin/resource/projects", "kanban", "Projects"),
    ("images", "/admin/images", "image", "Images"),
]


def _link(item_key: str, href: str, icon: str, label: str, active: str) -> A:
    return A(
        Icon(icon),
        Span(label),
        href=href,
        cls=f"admin-nav-link {'active' if item_key == active else ''}",
    )


def sidebar(active: str) -> Div:
    grouped = []
    for group in NAV_GROUPS:
        links = [
            _link(key, f"/admin/resource/{key}", cfg.icon, cfg.label, active)
            for key, cfg in TABLES.items()
            if cfg.group == group
        ]
        grouped.extend([Div(group, cls="admin-nav-section"), *links])

    return Div(
        A(
            Span("SB", cls="admin-brand-mark"),
            Div(
                Div("Portfolio Admin", cls="fw-bold"),
                Div("Segun Banji", cls="small text-white-50"),
            ),
            href="/admin",
            cls="admin-brand",
        ),
        _link("dashboard", "/admin", "speedometer2", "Dashboard", active),
        *grouped,
        Div(
            A(Icon("box-arrow-up-right"), Span("View Site"), href="https://banjisegun.vercel.app", target="_blank", cls="admin-nav-link"),
            A(Icon("image"), Span("Images"), href="/admin/images", cls=f"admin-nav-link {'active' if active == 'images' else ''}"),
            A(Icon("box-arrow-right"), Span("Logout"), href="/logout", cls="admin-nav-link"),
            cls="mt-4 pt-3 border-top border-warning border-opacity-25",
        ),
        cls="admin-sidebar d-none d-lg-block",
    )


def mobile_sidebar(active: str) -> Div:
    grouped = []
    for group in NAV_GROUPS:
        links = [
            _link(key, f"/admin/resource/{key}", cfg.icon, cfg.label, active)
            for key, cfg in TABLES.items()
            if cfg.group == group
        ]
        grouped.extend([Div(group, cls="admin-nav-section"), *links])

    return Div(
        Div(
            Div(
                Span("SB", cls="admin-brand-mark"),
                Div(
                    Div("Portfolio Admin", id="adminMobileMenuLabel", cls="fw-bold"),
                    Div("All content sections", cls="small text-white-50"),
                ),
                cls="d-flex align-items-center gap-2",
            ),
            Button(
                Icon("x-lg"),
                type="button",
                cls="admin-menu-close",
                data_bs_dismiss="offcanvas",
                aria_label="Close menu",
            ),
            cls="offcanvas-header",
        ),
        Div(
            _link("dashboard", "/admin", "speedometer2", "Dashboard", active),
            A(Icon("image"), Span("Images"), href="/admin/images", cls=f"admin-nav-link {'active' if active == 'images' else ''}"),
            *grouped,
            Div(
                A(Icon("box-arrow-up-right"), Span("View Site"), href="https://banjisegun.vercel.app", target="_blank", cls="admin-nav-link"),
                A(Icon("box-arrow-right"), Span("Logout"), href="/logout", cls="admin-nav-link"),
                cls="mt-4 pt-3 border-top border-warning border-opacity-25",
            ),
            cls="offcanvas-body",
        ),
        id="adminMobileMenu",
        tabindex="-1",
        aria_labelledby="adminMobileMenuLabel",
        cls="offcanvas offcanvas-start admin-mobile-menu d-lg-none",
    )


def bottom_nav(active: str) -> Div:
    return Div(
        *[
            A(Icon(icon), Span(label), href=href, cls="active" if key == active else "")
            for key, href, icon, label in PRIMARY_NAV
        ],
        Button(
            Icon("list"),
            Span("Menu"),
            type="button",
            cls="active" if active not in {item[0] for item in PRIMARY_NAV} else "",
            data_bs_toggle="offcanvas",
            data_bs_target="#adminMobileMenu",
            aria_controls="adminMobileMenu",
            aria_label="Open admin menu",
        ),
        cls="admin-bottom-nav d-lg-none",
    )


def page_shell(active: str, title: str, subtitle: str, *content):
    return (
        Title(f"{title} - Portfolio Admin"),
        Div(
            sidebar(active),
            mobile_sidebar(active),
            Div(
                Div(
                    Div(
                        H1(title, cls="admin-page-title mb-1"),
                        P(subtitle, cls="admin-muted mb-0"),
                    ),
                    Div(
                        Badge("Supabase", cls="admin-pill"),
                        A("View Site", href="https://banjisegun.vercel.app", target="_blank", cls="btn btn-outline-warning btn-sm ms-2 d-none d-md-inline-flex"),
                    ),
                    cls="admin-topbar d-flex align-items-center justify-content-between gap-3",
                ),
                Container(*content, fluid=True, cls="px-0"),
                cls="admin-main",
            ),
            bottom_nav(active),
            cls="admin-shell",
        ),
    )
