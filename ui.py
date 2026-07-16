"""Shared UI helpers for the admin app."""
from __future__ import annotations

from fasthtml.common import A, Button, Div, H1, Li, P, Script, Span, Title, Ul
from faststrap import Badge, Breadcrumb, Container, Icon, ThemeToggle
from faststrap.accessibility import SkipLink

from config import ADMIN_APP_NAME, PORTFOLIO_OWNER_NAME, PORTFOLIO_SITE_URL
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


def _build_grouped_nav(active: str) -> list:
    """Build the grouped navigation items shared between sidebar and mobile sidebar."""
    grouped = []
    for group in NAV_GROUPS:
        links = [
            _link(key, f"/admin/resource/{key}", cfg.icon, cfg.label, active)
            for key, cfg in TABLES.items()
            if cfg.group == group
        ]
        grouped.extend([Div(group, cls="admin-nav-section"), *links])
    return grouped


def _bottom_actions(active: str, current_theme: str = "auto") -> Div:
    """Build the bottom action links shared between sidebar and mobile sidebar."""
    return Div(
        Button(Icon("download"), Span("Install App"), type="button", cls="admin-nav-link admin-install-button", data_install_app="true"),
        _link("security", "/admin/security", "shield-lock", "Security", active),
        ThemeToggle(current_theme=current_theme, endpoint="/admin/theme/toggle", show_label=True, label_text="Dark Mode", show_icon=True, cls="admin-nav-link"),
        A(Icon("box-arrow-up-right"), Span("View Site"), href=PORTFOLIO_SITE_URL, target="_blank", cls="admin-nav-link"),
        A(Icon("box-arrow-right"), Span("Logout"), href="/logout", cls="admin-nav-link"),
        cls="mt-4 pt-3 border-top border-warning border-opacity-25",
    )


def sidebar(active: str, current_theme: str = "auto") -> Div:
    grouped = _build_grouped_nav(active)

    return Div(
        A(
            Span("SB", cls="admin-brand-mark"),
            Div(
                Div(ADMIN_APP_NAME, cls="fw-bold"),
                Div(PORTFOLIO_OWNER_NAME, cls="small text-white-50"),
            ),
            href="/admin",
            cls="admin-brand",
        ),
        _link("dashboard", "/admin", "speedometer2", "Dashboard", active),
        *grouped,
        _bottom_actions(active, current_theme),
        cls="admin-sidebar d-none d-lg-block",
    )


def mobile_sidebar(active: str, current_theme: str = "auto") -> Div:
    grouped = _build_grouped_nav(active)

    return Div(
        Div(
            Div(
                Span("SB", cls="admin-brand-mark"),
                Div(
                    Div(ADMIN_APP_NAME, id="adminMobileMenuLabel", cls="fw-bold"),
                    Div(PORTFOLIO_OWNER_NAME, cls="small text-white-50"),
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
            _bottom_actions(active, current_theme),
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


def _toast_container() -> Div:
    """Toast notification container for status messages."""
    return Div(
        id="toast-container",
        cls="position-fixed top-0 end-0 p-3",
        style="z-index: 1090;",
        aria_live="polite",
        aria_atomic="true",
    )


def admin_toast(message: str, variant: str = "success", dismissible: bool = True) -> Div:
    """Create a Bootstrap toast notification."""
    close_btn = ""
    if dismissible:
        close_btn = Button(
            type="button",
            cls="btn-close",
            data_bs_dismiss="toast",
            aria_label="Close",
        )
    return Div(
        Div(
            Div(
                Span(message, cls="fw-semibold") if variant == "danger" else message,
                close_btn,
                cls="toast-header",
            ),
            cls="toast-body" if variant == "success" else f"toast-body text-bg-{variant}",
        ),
        cls=f"toast align-items-center text-bg-{variant} border-0",
        role="alert",
        aria_live="assertive",
        aria_atomic="true",
        data_bs_autohide="true",
        data_bs_delay="4000",
    )


def _build_breadcrumbs(active: str, title: str) -> Breadcrumb:
    """Build breadcrumb navigation based on the active page."""
    crumbs = [("Home", "/admin")]
    # Map active keys to breadcrumb labels
    breadcrumb_map = {
        "dashboard": "Dashboard",
        "profile": "Profile",
        "projects": "Projects",
        "experience": "Experience",
        "skills": "Skills",
        "work_categories": "Work Categories",
        "video_categories": "Video Categories",
        "education": "Education",
        "certifications": "Certifications",
        "messages": "Messages",
        "images": "Images",
        "security": "Security",
    }
    if active in breadcrumb_map and active != "dashboard":
        crumbs.append((breadcrumb_map[active], None))  # No href = active (last) item
    return Breadcrumb(*crumbs, cls="mb-2 small")


def page_shell(active: str, title: str, subtitle: str, *content, request=None):
    # Determine current theme from session or default to auto
    current_theme = "auto"
    if request and hasattr(request, "session"):
        current_theme = request.session.get("theme", "auto")
    return (
        SkipLink(target="#main-content"),
        Title(f"{title} - {ADMIN_APP_NAME}"),
        Div(
            sidebar(active, current_theme),
            mobile_sidebar(active, current_theme),
            Div(
                Div(
                    _build_breadcrumbs(active, title),
                    Div(
                        H1(title, cls="admin-page-title mb-1"),
                        P(subtitle, cls="admin-muted mb-0"),
                    ),
                    Div(
                        Badge(PORTFOLIO_OWNER_NAME, cls="admin-pill"),
                        Badge("Supabase", cls="admin-pill"),
                        A("View Site", href=PORTFOLIO_SITE_URL, target="_blank", cls="btn btn-outline-warning btn-sm ms-2 d-none d-md-inline-flex"),
                    ),
                    cls="admin-topbar d-flex align-items-center justify-content-between gap-3",
                ),
                Container(*content, fluid=True, cls="px-0", id="main-content"),
                cls="admin-main",
            ),
            bottom_nav(active),
            _toast_container(),
            Script("""
                // Toast auto-init from HTMX responses
                document.addEventListener('htmx:afterRequest', function(event) {
                    if (event.detail.xhr && event.detail.xhr.status === 200) {
                        var toastEl = event.detail.xhr.response;
                        if (toastEl && toastEl.includes('toast')) {
                            var container = document.getElementById('toast-container');
                            if (container) {
                                var temp = document.createElement('div');
                                temp.innerHTML = toastEl;
                                var toast = temp.querySelector('.toast');
                                if (toast) {
                                    container.appendChild(toast);
                                    var bsToast = new bootstrap.Toast(toast);
                                    bsToast.show();
                                    toast.addEventListener('hidden.bs.toast', function() { toast.remove(); });
                                }
                            }
                        }
                    }
                });
                document.querySelectorAll('#toast-container .toast').forEach(function(toastEl) {
                    var bsToast = new bootstrap.Toast(toastEl);
                    bsToast.show();
                    toastEl.addEventListener('hidden.bs.toast', function() { toastEl.remove(); });
                });

                // Loading button states for form submissions
                document.querySelectorAll('form').forEach(function(form) {
                    form.addEventListener('submit', function() {
                        var btn = form.querySelector('button[type="submit"]');
                        if (btn && !btn.classList.contains('btn-outline-danger')) {
                            btn.classList.add('is-loading');
                            btn.disabled = true;
                        }
                    });
                });
            """),
            cls="admin-shell",
        ),
    )
