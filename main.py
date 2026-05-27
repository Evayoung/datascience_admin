"""Portfolio admin PWA entrypoint."""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from fasthtml.common import (  # noqa: E402
    A,
    Div,
    FastHTML,
    Form,
    H1,
    H2,
    H3,
    Hr,
    Img,
    Input,
    Li,
    Link,
    Option,
    P,
    Section,
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
from faststrap import Alert, Badge, Button, Card, Col, Container, FormGroup, Icon, Row, add_bootstrap, create_theme, mount_assets  # noqa: E402
from faststrap.pwa import add_pwa  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import RedirectResponse  # noqa: E402

from config import ADMIN_PASSWORD, ADMIN_SECRET_KEY, PROFILE_ID  # noqa: E402
from schema import Field, TABLES, TableConfig  # noqa: E402
from supabase_admin import (  # noqa: E402
    SupabaseAdminError,
    configured,
    create_row,
    delete_row,
    encoded_pk,
    get_row,
    list_rows,
    option_rows,
    update_row,
    upload_image,
    using_service_role,
)
from ui import page_shell  # noqa: E402


theme = create_theme(primary="#C9A84C", dark="#111111", light="#F5F0E8")
AUTH_PORTRAIT_URL = "https://pdfsfspkptysfowokzgi.supabase.co/storage/v1/object/public/portfolio-images/profile/1779887668-5779de3f-profile.jpeg"

app = FastHTML(
    hdrs=(Link(rel="stylesheet", href="/assets/css/admin.css"),),
    secret_key=ADMIN_SECRET_KEY,
    session_cookie="datascience_admin_session",
)

add_bootstrap(app, theme=theme, font_family="Inter", mode="light")
add_pwa(
    app,
    name="Segun Banji Portfolio Admin",
    short_name="SB Admin",
    description="PWA admin for managing the Segun Banji portfolio website.",
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
    return bool(request.session.get("admin_authenticated"))


def _require_admin(request: Request):
    if not _is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    return None


def _redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


def _login_form(error: str | None = None):
    return (
        Title("Login - Portfolio Admin"),
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
                        Badge("Portfolio Admin", cls="admin-auth-badge mb-3"),
                        H1("Welcome back", cls="admin-auth-visual-title"),
                        P(
                            "Manage Segun Banji's portfolio content, projects, media, images, and messages from one focused workspace.",
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
                        P("Enter the admin password to continue.", cls="admin-muted mb-4"),
                        Alert(error, variant="danger", cls="mb-4") if error else "",
                        Form(
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
    text = "" if value is None else str(value)
    return text if len(text) <= limit else f"{text[:limit - 3]}..."


def _table_options(relation: str) -> list[tuple[str, str]]:
    try:
        if relation == "work_categories":
            return option_rows("work_categories", ("label",), "id")
        if relation == "video_categories":
            return option_rows("video_categories", ("label",), "id")
        if relation == "projects":
            return option_rows("portfolio_projects", ("title",), "slug")
        if relation == "experience":
            return option_rows("portfolio_experience", ("role", "organization"), "id")
    except SupabaseAdminError:
        return []
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


def _resource_form(config: TableConfig, row: dict | None = None, error: str | None = None):
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

    return Card(
        Div(
            Div(
                H2("Edit item" if is_edit else "Create item", cls="h5 fw-bold mb-1"),
                P(config.description or f"Manage {config.label.lower()} content.", cls="admin-muted mb-0"),
            ),
            Alert(error, variant="danger", cls="mt-3") if error else "",
                Form(
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


def _resource_table(config: TableConfig, rows: list[dict]):
    if not rows:
        return Div(
            Icon("database-x", style="font-size:2rem;color:#C9A84C;"),
            H3("No records yet", cls="h5 fw-bold mt-3"),
            P("Create the first item with the form above.", cls="mb-0"),
            cls="admin-empty",
        )

    headings = list(config.table_columns) or [field.name for field in config.fields if not field.hidden][:4]
    return Div(
        Table(
            Thead(Tr(*[Th(label.replace("_", " ").title()) for label in headings], Th("Actions", cls="text-end"))),
            Tbody(
                *[
                    Tr(
                        *[Td(_safe_text(row.get(col))) for col in headings],
                        Td(
                            Div(
                                A("Edit", href=f"/admin/resource/{config.key}/{encoded_pk(row[config.pk])}", cls="btn btn-sm btn-outline-warning me-2")
                                if not config.readonly
                                else "",
                                Form(
                                    Button("Delete", type="submit", cls="btn btn-sm btn-outline-danger"),
                                    method="post",
                                    action=f"/admin/resource/{config.key}/{encoded_pk(row[config.pk])}/delete",
                                    onsubmit="return confirm('Delete this item?')",
                                    cls="d-inline",
                                ),
                                cls="text-end text-nowrap",
                            )
                        ),
                    )
                    for row in rows
                ]
            ),
            cls="table admin-table",
        ),
        cls="admin-table-wrap mb-4",
    )


def _row_counts() -> dict[str, int | str]:
    counts = {}
    for key, config in TABLES.items():
        try:
            counts[key] = len(list_rows(config.table, order=config.order, limit=500))
        except SupabaseAdminError:
            counts[key] = "!"
    return counts


@app.get("/")
def index():
    return _redirect("/admin")


@app.get("/login")
def login_page(request: Request):
    if _is_authenticated(request):
        return _redirect("/admin")
    return _login_form()


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    if str(form.get("password", "")) != ADMIN_PASSWORD:
        return _login_form("That password did not match.")
    request.session["admin_authenticated"] = True
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
                        Card(
                            Div(
                                Icon(icon, cls="text-warning mb-3", style="font-size:1.6rem;"),
                                Div(str(value), cls="display-6 fw-bold text-dark"),
                                P(label, cls="admin-muted mb-0"),
                                cls="p-3 p-md-4 admin-stat",
                            ),
                            cls="admin-card h-100",
                            body_cls="p-0",
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


@app.get("/admin/resource/{key}")
def resource_page(request: Request, key: str, status: str | None = None):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config:
        return _redirect("/admin")
    try:
        rows = list_rows(config.table, order=config.order, limit=500)
        error = None
    except SupabaseAdminError as exc:
        rows = []
        error = str(exc)

    return page_shell(
        key,
        config.label,
        config.description or f"Manage {config.label.lower()} records.",
        _status_alert(status),
        Alert(error, variant="danger") if error else "",
        "" if config.readonly else _resource_form(config),
        _resource_table(config, rows),
    )


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
        return page_shell(key, config.label, "Edit record", Alert(str(exc), variant="danger"))
    if not row:
        return _redirect(f"/admin/resource/{key}?status=error")
    return page_shell(
        key,
        config.label,
        "Edit a Supabase record.",
        _resource_form(config, row=row),
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
            payload[field.name] = int(value) if value != "" else None
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
    payload, errors = _payload_from_form(config, form)
    errors.extend(await _apply_image_uploads(config, form, payload))
    pk_value = str(form.get(config.pk, "")).strip()
    try:
        is_edit = bool(pk_value and get_row(config.table, config.pk, pk_value))
    except SupabaseAdminError as exc:
        return page_shell(key, config.label, "Unable to read the current record.", Alert(str(exc), variant="danger"))

    if is_edit and config.pk in payload:
        payload.pop(config.pk, None)
    if not is_edit and config.pk_kind == "generated":
        payload.pop(config.pk, None)

    if errors:
        return page_shell(
            key,
            config.label,
            "Fix the highlighted fields.",
            _resource_form(config, row=dict(form), error=" ".join(errors)),
        )

    try:
        if is_edit:
            update_row(config.table, config.pk, pk_value, payload)
        else:
            create_row(config.table, payload)
    except SupabaseAdminError:
        return _redirect(f"/admin/resource/{key}?status=error")
    return _redirect(f"/admin/resource/{key}?status=saved")


def _image_upload_form(error: str | None = None, uploaded_url: str | None = None):
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
        _image_upload_form(),
    )


@app.post("/admin/images/upload")
async def image_upload_submit(request: Request):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    form = await request.form()
    upload = form.get("image")
    filename = getattr(upload, "filename", "")
    if not filename:
        return page_shell("images", "Images", "Upload hosted portfolio images to Supabase Storage.", _image_upload_form("Choose an image file first."))
    try:
        url = upload_image(
            filename=filename,
            content=await upload.read(),
            content_type=getattr(upload, "content_type", None),
            folder=str(form.get("folder") or "uploads"),
        )
    except SupabaseAdminError as exc:
        return page_shell("images", "Images", "Upload hosted portfolio images to Supabase Storage.", _image_upload_form(str(exc)))
    return page_shell(
        "images",
        "Images",
        "Upload hosted portfolio images to Supabase Storage.",
        Alert("Image uploaded successfully.", variant="success", cls="mb-4"),
        _image_upload_form(uploaded_url=url),
    )


@app.post("/admin/resource/{key}/{pk_value}/delete")
def delete_resource(request: Request, key: str, pk_value: str):
    redirect = _require_admin(request)
    if redirect:
        return redirect
    config = TABLES.get(key)
    if not config:
        return _redirect("/admin")
    try:
        delete_row(config.table, config.pk, pk_value)
    except SupabaseAdminError:
        return _redirect(f"/admin/resource/{key}?status=error")
    return _redirect(f"/admin/resource/{key}?status=deleted")


@app.get("/health")
def health():
    return {"status": "ok", "supabase": configured()}


if __name__ == "__main__":
    serve(port=8064)
