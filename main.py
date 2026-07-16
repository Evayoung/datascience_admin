"""Portfolio admin PWA entrypoint."""
from __future__ import annotations

from fasthtml.common import (  # noqa: E402
    A,
    Div,
    FastHTML,
    Form,
    H1,
    H2,
    Img,
    Input,
    Li,
    Link,
    Nav,
    Option,
    P,
    Script,
    Select,
    Span,
    Table,
    Tbody,
    Td,
    Textarea,
    Th,
    Thead,
    Title,
    Tr,
    Ul,
    serve,
)
from faststrap import Alert, Badge, Button, Card, Col, Container, EmptyState, FormGroup, Icon, Placeholder, Row, StatCard, TabPane, Tabs, ThemeToggle, Tooltip, add_bootstrap, create_theme, mount_assets  # noqa: E402
from faststrap.accessibility import SkipLink  # noqa: E402
from faststrap.pwa import add_pwa  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import RedirectResponse  # noqa: E402

from admin_security import (  # noqa: E402
    change_admin_password,
    clear_attempts,
    generate_csrf_token,
    get_audit_logs,
    log_admin_action,
    password_matches,
    password_override_enabled,
    record_failed_attempt,
    reset_admin_password,
    verify_csrf_token,
    _is_locked_out,
)
from config import ADMIN_APP_NAME, ADMIN_AUTH_PORTRAIT_URL, ADMIN_PASSWORD, ADMIN_SECRET_KEY, PORTFOLIO_OWNER_NAME, PROFILE_ID, SESSION_TIMEOUT_SECONDS  # noqa: E402
from schema import Field, TABLES, TableConfig  # noqa: E402
from supabase_admin import (  # noqa: E402
    SupabaseAdminError,
    configured,
    count_rows,
    create_row,
    delete_row,
    delete_storage_file,
    encoded_pk,
    get_row,
    list_rows,
    list_rows_page,
    option_rows,
    update_row,
    upload_image,
    using_service_role,
)
from ui import page_shell  # noqa: E402


theme = create_theme(primary="#C9A84C", dark="#111111", light="#F5F0E8")
AUTH_PORTRAIT_URL = ADMIN_AUTH_PORTRAIT_URL or "https://pdfsfspkptysfowokzgi.supabase.co/storage/v1/object/public/portfolio-images/profile/1779887668-5779de3f-profile.jpeg"

app = FastHTML(
    hdrs=(
        Link(rel="stylesheet", href="/assets/css/admin.css"),
        Script(src="/assets/js/install.js", defer=True),
    ),
    secret_key=ADMIN_SECRET_KEY,
    session_cookie="datascience_admin_session",
)

add_bootstrap(app, theme=theme, font_family="Inter", mode="auto")
add_pwa(
    app,
    name=ADMIN_APP_NAME,
    short_name=ADMIN_APP_NAME,
    description=f"PWA admin for managing the {PORTFOLIO_OWNER_NAME} portfolio website.",
    theme_color="#111111",
    background_color="#F5F0E8",
    icon_path="/assets/icon.svg",
    display="standalone",
    start_url="/admin",
    scope="/",
    service_worker=True,
    offline_page=True,
    cache_name="sb-admin",
    cache_version="v1",
)
mount_assets(app, "assets", url_path="/assets")


def _is_authenticated(request: Request) -> bool:
    """Check if the user is authenticated and the session hasn't timed out."""
    if not request.session.get("admin_authenticated"):
        return False
    # Check session timeout
    login_time = request.session.get("login_time")
    if login_time:
        import time
        if time.time() - login_time > SESSION_TIMEOUT_SECONDS:
            request.session.clear()
            return False
    return True


def _require_admin(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    return None


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


def _csrf_hidden(request: Request) -> Input:
    """Generate a hidden CSRF token input for forms."""
    token = generate_csrf_token(ADMIN_SECRET_KEY, request.session.get("_sid", ""))
    return Input(type="hidden", name="csrf_token", value=token)


def _verify_csrf(request: Request, form) -> bool:
    """Verify the CSRF token from a form submission."""
    token = form.get("csrf_token", "")
    return verify_csrf_token(ADMIN_SECRET_KEY, request.session.get("_sid", ""), str(token))


def _login_form(error: str | None = None, request: Request | None = None):
    csrf = _csrf_hidden(request) if request else Input(type="hidden", name="csrf_token", value="")
    return (
        Title(f"Login - {ADMIN_APP_NAME}"),
        Div(
            Div(
                Div(
                    Img(
                        src=AUTH_PORTRAIT_URL,
                        alt="",
                        aria_hidden="true",
                        onerror="this.style.display='none'",
                        cls="admin-auth-portrait",
                    ),
                    Div(
                        Badge(ADMIN_APP_NAME, cls="admin-auth-badge mb-3"),
                        H1("Welcome back", cls="admin-auth-visual-title"),
                        P(
                            f"Manage {PORTFOLIO_OWNER_NAME}'s portfolio content, projects, media, images, and messages from one focused workspace.",
                            cls="admin-auth-visual-copy",
                        ),
                        Div(
                            Div(Icon("shield-check"), Span("Private admin access"), cls="admin-auth-proof"),
                            Div(Icon("database-check"), Span("Connected to Supabase"), cls="admin-auth-proof"),
                            cls="admin-auth-proof-grid",
                        ),
                        cls="admin-auth-visual-content",
                    ),
                    cls="admin-auth-visual",
                ),
                Card(
                    Div(
                        Span("SB", cls="admin-brand-mark mb-4"),
                        H1("Sign in", cls="admin-auth-title mb-2"),
                        P("Enter the admin password to continue.", cls="admin-auth mb-4"),
                        Alert(error, variant="danger", cls="mb-4") if error else "",
                        Form(
                            csrf,
                            FormGroup(
                                Input(
                                    type="password",
                                    name="password",
                                    placeholder="Enter admin password",
                                    required=True,
                                    cls="form-control form-control-lg",
                                ),
                                label="Password",
                            ),
                            Button(Icon("box-arrow-in-right"), " Sign In", type="submit", cls="w-100 mt-3 admin-auth-submit"),
                            method="post",
                            action="/login",
                            cls="admin-auth-form",
                        ),
                        P(
                            "Set ADMIN_PASSWORD in the admin environment before production use.",
                            cls="small admin-muted mt-3 mb-0",
                        )
                        if ADMIN_PASSWORD == "change-me"
                        else "",
                        cls="admin-auth-card-inner",
                    ),
                    cls="admin-auth-card",
                    body_cls="p-0",
                ),
                cls="admin-auth-layout",
            ),
            cls="admin-auth-shell",
        ),
    )


def _status_alert(kind: str | None):
    messages = {
        "saved": ("Saved successfully.", "success"),
        "deleted": ("Deleted successfully.", "success"),
        "error": ("The last action could not be completed.", "danger"),
    }
    if kind not in messages:
        return ""
    text, variant = messages[kind]
    return Alert(text, variant=variant, cls="mb-4")


def _safe_text(value, limit: int = 90) -> str:
    """Truncate and HTML-escape text for safe display in table cells."""
    from html import escape
    text = "" if value is None else str(value)
    text = escape(text)
    return text if len(text) <= limit else f"{text[:limit - 3]}..."


def _safe_error_message(exc: Exception) -> str:
    """Convert an exception to a user-friendly error message without leaking internal details."""
    msg = str(exc)
    # Strip any SQL, JSON, or URL patterns that might leak internals
    if any(keyword in msg.lower() for keyword in ("select", "insert", "update", "delete", "from where", "syntax error")):
        return "A database error occurred. Please try again or contact support."
    if "connection" in msg.lower() or "timeout" in msg.lower():
        return "Could not connect to the database. Please try again later."
    if len(msg) > 120:
        return "An unexpected error occurred. Please try again."
    return msg


def _table_options(relation: str) -> list[tuple[str, str]]:
    """Fetch dropdown options from a related table using schema config instead of hardcoded names."""
    config = TABLES.get(relation)
    if not config:
        return []
    try:
        # Determine label fields and value field based on the relation's schema
        if relation == "work_categories" or relation == "video_categories":
            return option_rows(config.table, ("label",), "id")
        if relation == "projects":
            return option_rows(config.table, ("title",), "slug")
        if relation == "experience":
            return option_rows(config.table, ("role", "organization"), "id")
        # Generic fallback: use first text field as label, pk as value
        text_fields = [f.name for f in config.fields if f.kind in ("text", "email") and not f.hidden]
        if text_fields:
            return option_rows(config.table, (text_fields[0],), config.pk)
        return option_rows(config.table, (config.pk,), config.pk)
    except SupabaseAdminError:
        return []


def _field_value(row: dict | None, field: Field):
    if row and field.name in row and row[field.name] is not None:
        return row[field.name]
    if field.name == "profile_id":
        return PROFILE_ID
    return field.default if field.default is not None else ""


def _field_control(field: Field, row: dict | None):
    value = _field_value(row, field)
    if field.hidden:
        return Input(type="hidden", name=field.name, value=str(value))

    if field.kind == "textarea":
        return Textarea(str(value or ""), name=field.name, rows=5, cls="form-control", required=field.required)

    if field.kind == "checkbox":
        return Div(
            Input(type="checkbox", name=field.name, value="true", checked=bool(value), cls="form-check-input me-2"),
            Span("Enabled", cls="form-check-label"),
            cls="form-check mt-2",
        )

    if field.kind == "select":
        options = [
            Option(label, value=option_value, selected=str(option_value) == str(value))
            for option_value, label in _table_options(field.relation or "")
        ]
        return Select(*options, name=field.name, cls="form-select", required=field.required)

    if field.kind == "choice":
        options = [
            Option(label, value=option_value, selected=str(option_value) == str(value))
            for option_value, label in field.choices
        ]
        return Select(*options, name=field.name, cls="form-select", required=field.required)

    if field.kind == "image":
        preview = (
            Img(src=str(value), alt="", cls="admin-image-preview mt-3")
            if value
            else P("Upload an image or paste a hosted image URL.", cls="small admin-muted mt-2 mb-0")
        )
        return Div(
            Input(
                type="url",
                name=field.name,
                value=str(value or ""),
                placeholder="https://... or leave blank and upload below",
                cls="form-control",
            ),
            Input(type="file", name=f"upload__{field.name}", accept="image/*", cls="form-control mt-2"),
            preview,
        )

    input_type = "number" if field.kind == "number" else field.kind
    return Input(
        type=input_type,
        name=field.name,
        value=str(value or ""),
        placeholder=field.label,
        required=field.required,
        cls="form-control",
    )


def _resource_form(config: TableConfig, row: dict | None = None, error: str | None = None, request: Request | None = None):
    is_edit = bool(row)
    controls = []
    hidden_controls = []
    for field in config.fields:
        control = _field_control(field, row)
        if field.hidden:
            hidden_controls.append(control)
            continue
        if is_edit and field.name == config.pk:
            hidden_controls.append(Input(type="hidden", name=field.name, value=str(row.get(config.pk, ""))))
            controls.append(
                Div(
                    Span(field.label, cls="form-label fw-semibold"),
                    Div(str(row.get(config.pk, "")), cls="form-control bg-light"),
                    cls="admin-field-full" if field.full else "",
                )
            )
            continue
        controls.append(
            Div(
                FormGroup(control, label=field.label, required=field.required),
                cls="admin-field-full" if field.full else "",
            )
        )

    csrf = _csrf_hidden(request) if request else Input(type="hidden", name="csrf_token", value="")

    return Card(
        Div(
            Div(
                H2("Edit item" if is_edit else "Create item", cls="h5 fw-bold mb-1"),
                P(config.description or f"Manage {config.label.lower()} content.", cls="admin-muted mb-0"),
            ),
            Alert(error, variant="danger", cls="mt-3") if error else "",
                Form(
                csrf,
                *hidden_controls,
                Div(*controls, cls="admin-form-grid mt-4"),
                Div(
                    Button(Icon("check2"), " Save", type="submit", cls="me-2"),
                    A("Cancel", href=f"/admin/resource/{config.key}", cls="btn btn-outline-secondary"),
                    cls="mt-4",
                ),
                method="post",
                action=f"/admin/resource/{config.key}/save",
                enctype="multipart/form-data",
            ),
            cls="p-3 p-md-4",
        ),
        cls="admin-card mb-4",
        body_cls="p-0",
    )


def _delete_confirm_modal(row_pk: str, config_key: str, request: Request | None = None):
    """Generate a Bootstrap modal confirm dialog for delete actions."""
    from fasthtml.common import NotStr
    modal_id = f"delete-confirm-{config_key}-{row_pk}"
    return Div(
        Div(
            Div(
                Div(
                    H2("Confirm Delete", cls="modal-title"),
                    Button(type="button", cls="btn-close", data_bs_dismiss="modal", aria_label="Close"),
                    cls="modal-header",
                ),
                Div(
                    P("Are you sure you want to delete this record? This action cannot be undone."),
                    cls="modal-body",
                ),
                Div(
                    Button("Cancel", type="button", cls="btn btn-secondary", data_bs_dismiss="modal"),
                    Button(
                        Icon("trash"),
                        " Delete",
                        type="button",
                        cls="btn btn-danger",
                        onclick=f"document.getElementById('delete-form-{config_key}-{row_pk}').submit();",
                    ),
                    cls="d-flex justify-content-end gap-2",
                ),
                cls="modal-content",
            ),
            cls="modal-dialog modal-dialog-centered",
        ),
        id=modal_id,
        cls="modal fade",
        tabindex="-1",
        **{"aria-hidden": "true"},
    )


def _table_skeleton(config: TableConfig, per_page: int = 5):
    """Generate a skeleton loading placeholder for the resource table."""
    headings = list(config.table_columns) or [field.name for field in config.fields if not field.hidden][:4]
    rows = []
    for _ in range(per_page):
        cells = [Td(Placeholder(width="80%", animation="glow"), cls="py-2") for _ in headings]
        cells.append(
            Td(
                Div(
                    PlaceholderButton(width="60px", animation="glow", cls="me-1"),
                    PlaceholderButton(width="70px", animation="glow"),
                    cls="text-end text-nowrap",
                ) if not config.readonly else "",
                cls="py-2",
            )
        )
        rows.append(Tr(*cells))

    return Div(
        Table(
            Thead(Tr(*[Th(label.replace("_", " ").title()) for label in headings], Th("Actions", cls="text-end") if not config.readonly else "")),
            Tbody(*rows),
            cls="table admin-table",
        ),
        cls="admin-table-wrap mb-4",
    )


def _resource_table(config: TableConfig, rows: list[dict], request: Request | None = None, page: int = 1, total: int = 0, per_page: int = 25):
    if not rows:
        empty_msg = "No records found." if config.readonly else "Create the first item with the form above."
        return EmptyState(
            icon=Icon("database-x", style="font-size:2rem;color:#C9A84C;"),
            title="No records yet",
            description=empty_msg,
            cls="admin-empty",
        )

    headings = list(config.table_columns) or [field.name for field in config.fields if not field.hidden][:4]
    total_pages = max(1, (total + per_page - 1) // per_page)

    # Build pagination controls
    pagination = ""
    if total_pages > 1:
        page_links = []
        if page > 1:
            page_links.append(
                A(
                    Icon("chevron-left"),
                    href="#",
                    cls="page-link",
                    hx_get=f"/admin/resource/{config.key}/table?page={page - 1}",
                    hx_target=f"#resource-table-{config.key}",
                    hx_swap="innerHTML",
                )
            )

        # Show page numbers (max 5 visible)
        start_p = max(1, page - 2)
        end_p = min(total_pages, page + 2)
        if start_p > 1:
            page_links.append(A("1", href="#", cls="page-link", hx_get=f"/admin/resource/{config.key}/table?page=1", hx_target=f"#resource-table-{config.key}", hx_swap="innerHTML"))
            if start_p > 2:
                page_links.append(Span("...", cls="page-link text-muted"))

        for p in range(start_p, end_p + 1):
            active_cls = " active" if p == page else ""
            page_links.append(
                A(
                    str(p),
                    href="#",
                    cls=f"page-link{active_cls}",
                    hx_get=f"/admin/resource/{config.key}/table?page={p}",
                    hx_target=f"#resource-table-{config.key}",
                    hx_swap="innerHTML",
                )
            )

        if end_p < total_pages:
            if end_p < total_pages - 1:
                page_links.append(Span("...", cls="page-link text-muted"))
            page_links.append(A(str(total_pages), href="#", cls="page-link", hx_get=f"/admin/resource/{config.key}/table?page={total_pages}", hx_target=f"#resource-table-{config.key}", hx_swap="innerHTML"))

        if page < total_pages:
            page_links.append(
                A(
                    Icon("chevron-right"),
                    href="#",
                    cls="page-link",
                    hx_get=f"/admin/resource/{config.key}/table?page={page + 1}",
                    hx_target=f"#resource-table-{config.key}",
                    hx_swap="innerHTML",
                )
            )

        start_item = (page - 1) * per_page + 1
        end_item = min(page * per_page, total)
        pagination = Div(
            Div(
                Span(f"Showing {start_item}-{end_item} of {total}", cls="text-muted small"),
                Nav(
                    Ul(*[Li(link, cls="page-item") for link in page_links], cls="pagination pagination-sm mb-0"),
                ),
                cls="d-flex align-items-center justify-content-between mt-3",
            ),
        )

    modals = []
    rows_html = []
    for row in rows:
        pk_val = encoded_pk(row[config.pk])
        modal_id = f"delete-confirm-{config.key}-{pk_val}"
        modals.append(_delete_confirm_modal(pk_val, config.key, request))
        rows_html.append(
            Tr(
                *[Td(_safe_text(row.get(col))) for col in headings],
                Td(
                    Div(
                        Tooltip(
                            "Edit this record",
                            A("Edit", href=f"/admin/resource/{config.key}/{pk_val}", cls="btn btn-sm btn-outline-warning me-2"),
                            placement="top",
                        )
                        if not config.readonly
                        else "",
                        Form(
                            Input(type="hidden", name="csrf_token", value=generate_csrf_token(ADMIN_SECRET_KEY, request.session.get("_sid", "")) if request else ""),
                            Button(
                                Icon("trash"),
                                " Delete",
                                type="button",
                                cls="btn btn-sm btn-outline-danger",
                                data_bs_toggle="modal",
                                data_bs_target=f"#{modal_id}",
                            ),
                            method="post",
                            action=f"/admin/resource/{config.key}/{pk_val}/delete",
                            id=f"delete-form-{config.key}-{pk_val}",
                            cls="d-inline",
                        ) if not config.readonly else "",
                        cls="text-end text-nowrap",
                    )
                ),
            )
        )

    return Div(
        Table(
            Thead(Tr(*[Th(label.replace("_", " ").title()) for label in headings], Th("Actions", cls="text-end") if not config.readonly else "")),
            Tbody(*rows_html),
            cls="table admin-table",
        ),
        pagination,
        *modals,
        cls="admin-table-wrap mb-4",
    )


def _row_counts() -> dict[str, int | str]:
    """Get row counts for all tables using efficient count queries instead of fetching all rows."""
    counts = {}
    for key, config in TABLES.items():
        try:
            counts[key] = count_rows(config.table)
        except Exception:
            counts[key] = "!"
    return counts


@app.get("/")
def index():
    return _redirect("/admin")


@app.get("/login")
def login_page(request: Request):
    if _is_authenticated(request):
        return _redirect("/admin")
    return _login_form(request=request)


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()

    # CSRF verification
    if not _verify_csrf(request, form):
        return _login_form("Invalid form submission. Please try again.", request=request)

    # Brute-force protection
    client_ip = request.client.host if request.client else "unknown"
    if _is_locked_out(client_ip):
        return _login_form("Too many failed attempts. Please wait a few minutes and try again.", request=request)

    if not password_matches(str(form.get("password", ""))):
        record_failed_attempt(client_ip)
        log_admin_action("login_failed", "Invalid password attempt", client_ip)
        return _login_form("That password did not match.", request=request)

    # Successful login: clear attempts and regenerate session to prevent session fixation
    clear_attempts(client_ip)
    log_admin_action("login_success", "Admin logged in", client_ip)
    # Preserve redirect path if any, then regenerate session
    import time
    request.session.clear()
    request.session["admin_authenticated"] = True
    request.session["login_time"] = time.time()
    return _redirect("/admin")


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return _redirect("/login")


@app.get("/admin")
def dashboard(request: Request, status: str | None = None):
    redirect = _require_admin(request)
    if redirect:
        return redirect

    counts = _row_counts() if configured() else {}
    cards = [
        ("Projects", counts.get("projects", 0), "kanban", "/admin/resource/projects"),
        ("Experience", counts.get("experience", 0), "briefcase", "/admin/resource/experience"),
        ("Skills", counts.get("skills", 0), "tools", "/admin/resource/skills"),
        ("Messages", counts.get("messages", 0), "inbox", "/admin/resource/messages"),
    ]

    return page_shell(
        "dashboard",
        "Dashboard",
        "Manage the live portfolio content from one small PWA.",
        _status_alert(status),
        Alert("Supabase is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.", variant="warning")
        if not configured()
        else "",
        Alert(
            "Read access is working, but create/update/delete requires SUPABASE_SERVICE_ROLE_KEY in this admin app environment.",
            variant="warning",
        )
        if configured() and not using_service_role()
        else "",
        Row(
            *[
                Col(
                    A(
                        StatCard(
                            title=label,
                            value=str(value),
                            icon=Icon(icon, cls="text-warning", style="font-size:1.4rem;"),
                            cls="admin-card h-100",
                        ),
                        href=href,
                        cls="text-decoration-none",
                    ),
                    span=12,
                    md=6,
                    xl=3,
                )
                for label, value, icon, href in cards
            ],
            cls="g-3 mb-4",
        ),
        Card(
            Div(
                Span("Quick Start", cls="admin-kicker"),
                H2("Edit portfolio content by section", cls="h4 fw-bold mt-2"),
                P(
                    "Use the sidebar to move through profile, resume, projects, media, and inbox tables. "
                    "Changes are written directly to Supabase and reflected on the portfolio after reload.",
                    cls="admin-muted",
                ),
                Ul(
                    *[
                        Li("Edit Profile first for headline/contact changes."),
                        Li("Use Project Tools after creating or editing a project."),
                        Li("Use Experience Highlights to manage bullet points under a role."),
                    ],
                    cls="mb-0",
                ),
                cls="p-3 p-md-4",
            ),
            cls="admin-card",
            body_cls="p-0",
        ),
    )


def _security_panel(error: str | None = None, status: str | None = None, request: Request | None = None):
    override_active = password_override_enabled()
    status_message = ""
    if status == "changed":
        status_message = Alert("Admin password changed successfully.", variant="success", cls="mb-4")
    elif status == "reset":
        status_message = Alert("Admin password reset to the environment default.", variant="success", cls="mb-4")

    csrf = _csrf_hidden(request) if request else Input(type="hidden", name="csrf_token", value="")

    # Fetch recent audit logs
    try:
        audit_logs = get_audit_logs(limit=15)
    except Exception:
        audit_logs = []

    # Build audit log table rows
    audit_rows = []
    for log in audit_logs:
        action = log.get("action", "unknown")
        details = _safe_text(log.get("details", ""), limit=60)
        ip = _safe_text(log.get("ip_address", "—"), limit=20)
        timestamp = log.get("created_at", "")
        if timestamp:
            # Truncate ISO timestamp to readable format
            timestamp = timestamp[:19].replace("T", " ")
        variant_map = {
            "login_failed": "danger",
            "login_success": "success",
            "password_changed": "warning",
            "password_reset": "warning",
            "record_deleted": "danger",
        }
        badge_variant = variant_map.get(action, "secondary")
        audit_rows.append(
            Tr(
                Td(Badge(action.replace("_", " ").title(), cls=f"badge bg-{badge_variant}")),
                Td(details),
                Td(ip, cls="text-muted small"),
                Td(timestamp, cls="text-muted small"),
            )
        )

    # Tab 1: Change Password
    change_tab = Card(
        Div(
            Span("Access", cls="admin-kicker"),
            H2("Change admin password", cls="h4 fw-bold mt-2"),
            P(
                "This stores a hashed password override in Supabase. The environment password remains the reset/default password.",
                cls="admin-muted",
            ),
            status_message,
            Alert(error, variant="danger", cls="mb-4") if error else "",
            Form(
                csrf,
                FormGroup(
                    Input(type="password", name="current_password", cls="form-control", required=True),
                    label="Current Password",
                    required=True,
                ),
                FormGroup(
                    Input(type="password", name="new_password", cls="form-control", required=True),
                    label="New Password",
                    required=True,
                    help_text="Use at least 8 characters.",
                ),
                FormGroup(
                    Input(type="password", name="confirm_password", cls="form-control", required=True),
                    label="Confirm New Password",
                    required=True,
                ),
                Button(Icon("shield-lock"), " Update Password", type="submit", cls="mt-2"),
                method="post",
                action="/admin/security/password",
            ),
            cls="p-3 p-md-4",
        ),
        cls="admin-card h-100",
        body_cls="p-0",
    )

    # Tab 2: Reset Password
    reset_tab = Card(
        Div(
            Span("Default", cls="admin-kicker"),
            H2("Reset to default", cls="h4 fw-bold mt-2"),
            P(
                "Reset removes the Supabase override and uses the current ADMIN_PASSWORD value from the deployment environment again.",
                cls="admin-muted",
            ),
            Badge(
                "Custom password active" if override_active else "Using environment default",
                cls="admin-pill mb-4",
            ),
            Form(
                csrf,
                FormGroup(
                    Input(type="password", name="current_password", cls="form-control", required=True),
                    label="Current Password",
                    required=True,
                ),
                Button(Icon("arrow-counterclockwise"), " Reset Password", type="submit", cls="btn btn-outline-warning mt-2"),
                method="post",
                action="/admin/security/reset",
            ),
            cls="p-3 p-md-4",
        ),
        cls="admin-card h-100",
        body_cls="p-0",
    )

    # Tab 3: Audit Log
    if audit_rows:
        audit_table = Table(
            Thead(Tr(Th("Action"), Th("Details"), Th("IP"), Th("Time"))),
            Tbody(*audit_rows),
            cls="table table-sm admin-table mb-0",
        )
    else:
        audit_table = P("No audit log entries yet.", cls="admin-muted mb-0")

    audit_tab = Card(
        Div(
            Span("Audit", cls="admin-kicker"),
            H2("Recent activity", cls="h4 fw-bold mt-2"),
            P(
                "Tracks login attempts, password changes, and record deletions.",
                cls="admin-muted",
            ),
            Div(audit_table, cls="table-responsive mt-3"),
            cls="p-3 p-md-4",
        ),
        cls="admin-card h-100",
        body_cls="p-0",
    )

    # Tabs container
    tab_content = Div(
        TabPane(change_tab, tab_id="security-change", active=True),
        TabPane(reset_tab, tab_id="security-reset"),
        TabPane(audit_tab, tab_id="security-audit"),
        cls="tab-content mt-3",
    )

    return Div(
        Tabs(
            ("security-change", "Change Password"),
            ("security-reset", "Reset Password"),
            ("security-audit", "Audit Log"),
            variant="pills",
            fill=True,
            cls="mb-3",
        ),
        tab_content,
    )


@app.get("/admin/security")
def security_page(request: Request, status: str | None = None):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return page_shell(
        "security",
        "Security",
        "Change or reset the admin login password.",
        _security_panel(status=status, request=request),
    )


@app.post("/admin/security/password")
async def security_change_password(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    form = await request.form()
    if not _verify_csrf(request, form):
        return page_shell("security", "Security", "Change or reset the admin login password.", _security_panel("Invalid form submission. Please try again.", request=request))
    current_password = str(form.get("current_password", ""))
    new_password = str(form.get("new_password", ""))
    confirm_password = str(form.get("confirm_password", ""))

    if not password_matches(current_password):
        return page_shell("security", "Security", "Change or reset the admin login password.", _security_panel("Current password is incorrect.", request=request))
    if len(new_password) < 8:
        return page_shell("security", "Security", "Change or reset the admin login password.", _security_panel("New password must be at least 8 characters.", request=request))
    if new_password != confirm_password:
        return page_shell("security", "Security", "Change or reset the admin login password.", _security_panel("New password and confirmation do not match.", request=request))

    try:
        change_admin_password(new_password)
        client_ip = request.client.host if request.client else "unknown"
        log_admin_action("password_changed", "Admin password updated", client_ip)
    except SupabaseAdminError as exc:
        return page_shell(
            "security",
            "Security",
            "Change or reset the admin login password.",
            _security_panel(f"Password could not be saved. Please run the admin settings SQL script in Supabase and try again.", request=request),
        )
    return _redirect("/admin/security?status=changed")


@app.post("/admin/security/reset")
async def security_reset_password(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    form = await request.form()
    if not _verify_csrf(request, form):
        return page_shell("security", "Security", "Change or reset the admin login password.", _security_panel("Invalid form submission. Please try again.", request=request))
    current_password = str(form.get("current_password", ""))
    if not password_matches(current_password):
        return page_shell("security", "Security", "Change or reset the admin login password.", _security_panel("Current password is incorrect.", request=request))
    try:
        reset_admin_password()
        client_ip = request.client.host if request.client else "unknown"
        log_admin_action("password_reset", "Admin password reset to environment default", client_ip)
    except SupabaseAdminError as exc:
        return page_shell(
            "security",
            "Security",
            "Change or reset the admin login password.",
            _security_panel(f"Password could not be reset. Please run the admin settings SQL script in Supabase and try again.", request=request),
        )
    return _redirect("/admin/security?status=reset")


@app.get("/admin/resource/{key}")
def resource_page(request: Request, key: str, status: str | None = None, page_num: int = 1):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config:
        return _redirect("/admin")
    try:
        rows, total = list_rows_page(config.table, page=page_num, per_page=25, order=config.order)
        error = None
    except SupabaseAdminError as exc:
        rows, total = [], 0
        error = _safe_error_message(exc)

    return page_shell(
        key,
        config.label,
        config.description or f"Manage {config.label.lower()} records.",
        _status_alert(status),
        Alert(error, variant="danger") if error else "",
        "" if config.readonly else _resource_form(config, request=request),
        Div(
            _resource_table(config, rows, request=request, page=page_num, total=total),
            id=f"resource-table-{key}",
        ),
        request=request,
    )


@app.get("/admin/resource/{key}/table")
def resource_table_htmx(request: Request, key: str, page: int = 1):
    """HTMX endpoint for paginated table content."""
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config:
        return ""
    try:
        rows, total = list_rows_page(config.table, page=page, per_page=25, order=config.order)
    except SupabaseAdminError:
        rows, total = [], 0
    return _resource_table(config, rows, request=request, page=page, total=total)


@app.get("/admin/resource/{key}/{pk_value}")
def edit_resource(request: Request, key: str, pk_value: str):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config or config.readonly:
        return _redirect(f"/admin/resource/{key}")
    try:
        row = get_row(config.table, config.pk, pk_value)
    except SupabaseAdminError as exc:
        return page_shell(key, config.label, "Edit record", Alert(_safe_error_message(exc), variant="danger"))
    if not row:
        return _redirect(f"/admin/resource/{key}?status=error")
    return page_shell(
        key,
        config.label,
        "Edit a Supabase record.",
        _resource_form(config, row=row, request=request),
    )


def _payload_from_form(config: TableConfig, values) -> tuple[dict, list[str]]:
    payload = {}
    errors = []
    for field in config.fields:
        if field.kind == "checkbox":
            value = field.name in values
        else:
            value = str(values.get(field.name, "")).strip()
            if field.hidden and not value:
                value = str(field.default or PROFILE_ID)

        if field.required and (value is None or value == ""):
            errors.append(f"{field.label} is required.")
            continue

        if field.kind == "number":
            if value == "":
                payload[field.name] = None
            else:
                try:
                    payload[field.name] = int(value)
                except (ValueError, TypeError):
                    errors.append(f"{field.label} must be a valid whole number.")
                    continue
        elif field.kind == "checkbox":
            payload[field.name] = bool(value)
        else:
            payload[field.name] = value if value != "" else None
    return payload, errors


async def _apply_image_uploads(config: TableConfig, values, payload: dict) -> list[str]:
    errors = []
    for field in config.fields:
        if field.kind != "image":
            continue
        upload = values.get(f"upload__{field.name}")
        filename = getattr(upload, "filename", "")
        if not filename:
            continue
        try:
            content = await upload.read()
            payload[field.name] = upload_image(
                filename=filename,
                content=content,
                content_type=getattr(upload, "content_type", None),
                folder=config.key,
            )
        except SupabaseAdminError as exc:
            errors.append(f"{field.label} upload failed: {exc}")
    return errors


@app.post("/admin/resource/{key}/save")
async def save_resource(request: Request, key: str):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config or config.readonly:
        return _redirect("/admin")

    form = await request.form()
    if not _verify_csrf(request, form):
        return _redirect(f"/admin/resource/{key}?status=error")

    payload, errors = _payload_from_form(config, form)
    errors.extend(await _apply_image_uploads(config, form, payload))
    pk_value = str(form.get(config.pk, "")).strip()
    try:
        is_edit = bool(pk_value and get_row(config.table, config.pk, pk_value))
    except SupabaseAdminError as exc:
        return page_shell(key, config.label, "Unable to read the current record.", Alert(_safe_error_message(exc), variant="danger"), request=request)

    if is_edit and config.pk in payload:
        payload.pop(config.pk, None)
    if not is_edit and config.pk_kind == "generated":
        payload.pop(config.pk, None)

    if errors:
        return page_shell(
            key,
            config.label,
            "Fix the highlighted fields.",
            _resource_form(config, row=dict(form), error=" ".join(errors), request=request),
        )

    try:
        if is_edit:
            update_row(config.table, config.pk, pk_value, payload)
        else:
            create_row(config.table, payload)
    except SupabaseAdminError:
        return _redirect(f"/admin/resource/{key}?status=error")
    return _redirect(f"/admin/resource/{key}?status=saved")


def _image_upload_form(error: str | None = None, uploaded_url: str | None = None, request: Request | None = None):
    csrf = _csrf_hidden(request) if request else Input(type="hidden", name="csrf_token", value="")
    return Card(
        Div(
            Span("Media Library", cls="admin-kicker"),
            H2("Upload portfolio images", cls="h4 fw-bold mt-2"),
            P(
                "Images are stored in Supabase Storage and can be pasted into project image fields or reused anywhere on the portfolio.",
                cls="admin-muted",
            ),
            Alert(error, variant="danger", cls="mt-3") if error else "",
            Div(
                Img(src=uploaded_url, alt="Uploaded image preview", cls="admin-image-preview mb-3")
                if uploaded_url
                else "",
                Div(uploaded_url, cls="admin-upload-url small mb-3") if uploaded_url else "",
            ),
            Form(
                csrf,
                FormGroup(Input(type="file", name="image", accept="image/*", required=True, cls="form-control"), label="Image file", required=True),
                FormGroup(Input(type="text", name="folder", value="uploads", cls="form-control"), label="Storage folder"),
                Button(Icon("cloud-upload"), " Upload Image", type="submit", cls="mt-2"),
                method="post",
                action="/admin/images/upload",
                enctype="multipart/form-data",
            ),
            cls="p-3 p-md-4",
        ),
        cls="admin-card mb-4",
        body_cls="p-0",
    )


@app.get("/admin/images")
def images_page(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    return page_shell(
        "images",
        "Images",
        "Upload hosted portfolio images to Supabase Storage.",
        _image_upload_form(request=request),
    )


@app.post("/admin/images/upload")
async def image_upload_submit(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    form = await request.form()
    if not _verify_csrf(request, form):
        return page_shell("images", "Images", "Upload hosted portfolio images to Supabase Storage.", _image_upload_form("Invalid form submission. Please try again.", request=request))
    upload = form.get("image")
    filename = getattr(upload, "filename", "")
    if not filename:
        return page_shell("images", "Images", "Upload hosted portfolio images to Supabase Storage.", _image_upload_form("Choose an image file first.", request=request))
    try:
        url = upload_image(
            filename=filename,
            content=await upload.read(),
            content_type=getattr(upload, "content_type", None),
            folder=str(form.get("folder") or "uploads"),
        )
    except SupabaseAdminError as exc:
        return page_shell("images", "Images", "Upload hosted portfolio images to Supabase Storage.", _image_upload_form(_safe_error_message(exc), request=request))
    return page_shell(
        "images",
        "Images",
        "Upload hosted portfolio images to Supabase Storage.",
        Alert("Image uploaded successfully.", variant="success", cls="mb-4"),
        _image_upload_form(uploaded_url=url, request=request),
    )


@app.post("/admin/resource/{key}/{pk_value}/delete")
async def delete_resource(request: Request, key: str, pk_value: str):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config or config.readonly:
        return _redirect("/admin")
    form = await request.form()
    if not _verify_csrf(request, form):
        return _redirect(f"/admin/resource/{key}?status=error")
    try:
        # Clean up any associated storage files before deleting the row
        try:
            row = get_row(config.table, config.pk, pk_value)
            if row:
                for field in config.fields:
                    if field.kind == "image" and row.get(field.name):
                        delete_storage_file(str(row[field.name]))
        except SupabaseAdminError:
            pass  # Best-effort cleanup; proceed with delete even if cleanup fails
        delete_row(config.table, config.pk, pk_value)
        client_ip = request.client.host if request.client else "unknown"
        log_admin_action("record_deleted", f"Deleted {pk_value} from {key}", client_ip)
    except SupabaseAdminError:
        return _redirect(f"/admin/resource/{key}?status=error")
    return _redirect(f"/admin/resource/{key}?status=deleted")


@app.get("/health")
def health(request: Request):
    """Health check endpoint. Only reveals minimal status to authenticated admins."""
    result = {"status": "ok"}
    # Only reveal Supabase status to authenticated admins
    if _is_authenticated(request):
        result["supabase"] = configured()
    return result


@app.post("/admin/theme/toggle")
async def toggle_theme(request: Request):
    """Toggle dark/light theme preference stored in session."""
    if not _is_authenticated(request):
        return _redirect("/login")
    current = request.session.get("theme", "auto")
    # Cycle: auto → dark → light → auto
    cycle = {"auto": "dark", "dark": "light", "light": "auto"}
    request.session["theme"] = cycle.get(current, "auto")
    from fasthtml.common import NotStr
    return NotStr("")  # Return empty to trigger HTMX swap (hx_swap="none")


if __name__ == "__main__":
    serve(port=8064)
