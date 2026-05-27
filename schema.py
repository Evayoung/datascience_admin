"""Admin table configuration for Supabase portfolio content."""
from __future__ import annotations

from dataclasses import dataclass, field


SOCIAL_ICON_OPTIONS = (
    ("linkedin", "LinkedIn"),
    ("github", "GitHub"),
    ("envelope-fill", "Email"),
    ("youtube", "YouTube"),
    ("twitter-x", "X / Twitter"),
    ("instagram", "Instagram"),
    ("facebook", "Facebook"),
    ("globe2", "Website"),
)


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    kind: str = "text"
    required: bool = False
    full: bool = False
    hidden: bool = False
    default: str | int | bool | None = None
    relation: str | None = None
    choices: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class TableConfig:
    key: str
    table: str
    label: str
    group: str
    icon: str
    pk: str = "id"
    pk_kind: str = "generated"
    order: str = "sort_order.asc"
    description: str = ""
    fields: tuple[Field, ...] = field(default_factory=tuple)
    table_columns: tuple[str, ...] = field(default_factory=tuple)
    readonly: bool = False


TABLES: dict[str, TableConfig] = {
    "profile": TableConfig(
        key="profile",
        table="portfolio_profiles",
        label="Profile",
        group="Profile",
        icon="person-badge",
        pk="id",
        pk_kind="text",
        order="name.asc",
        description="Core identity, contact details, summary, and availability.",
        fields=(
            Field("id", "Profile ID", required=True),
            Field("name", "Name", required=True),
            Field("initials", "Initials", required=True),
            Field("title", "Title", required=True),
            Field("tagline", "Tagline", full=True, required=True),
            Field("phone", "Phone"),
            Field("email", "Email", kind="email", required=True),
            Field("linkedin_url", "LinkedIn URL", full=True),
            Field("github_url", "GitHub URL", full=True),
            Field("location", "Location"),
            Field("summary", "Professional Summary", kind="textarea", full=True),
            Field("how_i_work", "How I Work", kind="textarea", full=True),
            Field("youtube_channel_url", "YouTube Channel URL", full=True),
            Field("availability", "Availability"),
        ),
        table_columns=("name", "title", "email", "location"),
    ),
    "bio": TableConfig(
        "bio", "portfolio_bio_paragraphs", "Bio Paragraphs", "Profile", "body-text",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("body", "Paragraph", kind="textarea", full=True, required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("body", "sort_order"),
    ),
    "stats": TableConfig(
        "stats", "portfolio_stats", "Stats", "Profile", "speedometer2",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("value", "Value", kind="number", required=True),
            Field("suffix", "Suffix"),
            Field("label", "Label", required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("label", "value", "suffix", "sort_order"),
    ),
    "skills": TableConfig(
        "skills", "portfolio_skills", "Skills", "Profile", "tools",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("name", "Skill", required=True),
            Field("group_name", "Group"),
            Field("proficiency", "Proficiency", kind="number"),
            Field("show_on_home", "Show on Home", kind="checkbox", default=False),
            Field("show_on_cv", "Show on CV", kind="checkbox", default=False),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("name", "group_name", "proficiency", "show_on_home", "show_on_cv"),
    ),
    "social": TableConfig(
        "social", "portfolio_social_links", "Social Links", "Profile", "share",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("label", "Label", required=True),
            Field("icon", "Icon", kind="choice", choices=SOCIAL_ICON_OPTIONS, required=True),
            Field("href", "URL", full=True, required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("label", "icon", "href", "sort_order"),
    ),
    "specialisations": TableConfig(
        "specialisations", "portfolio_specialisations", "Specialisations", "Profile", "stars",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("icon", "Bootstrap Icon", required=True),
            Field("title", "Title", required=True),
            Field("description", "Description", kind="textarea", full=True, required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("title", "icon", "sort_order"),
    ),
    "experience": TableConfig(
        "experience", "portfolio_experience", "Experience", "Resume", "briefcase",
        order="sort_order.asc",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("role", "Role", required=True),
            Field("organization", "Organization", required=True),
            Field("location", "Location"),
            Field("date_label", "Date Label", required=True),
            Field("description", "Description", kind="textarea", full=True, required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("role", "organization", "date_label", "sort_order"),
    ),
    "experience_highlights": TableConfig(
        "experience_highlights", "portfolio_experience_highlights", "Experience Highlights", "Resume", "list-check",
        fields=(
            Field("experience_id", "Experience", kind="select", relation="experience", required=True),
            Field("body", "Highlight", kind="textarea", full=True, required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("body", "sort_order"),
    ),
    "education": TableConfig(
        "education", "portfolio_education", "Education", "Resume", "mortarboard",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("degree", "Degree", required=True),
            Field("institution", "Institution", required=True),
            Field("location", "Location"),
            Field("year", "Year", required=True),
            Field("gpa", "GPA"),
            Field("honors", "Honors"),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("degree", "institution", "year", "honors"),
    ),
    "certifications": TableConfig(
        "certifications", "portfolio_certifications", "Certifications", "Resume", "patch-check",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("title", "Title", required=True),
            Field("issuer", "Issuer"),
            Field("date_label", "Date Label"),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("title", "issuer", "date_label", "sort_order"),
    ),
    "languages": TableConfig(
        "languages", "portfolio_languages", "Languages", "Resume", "translate",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("label", "Label", required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("label", "sort_order"),
    ),
    "soft_skills": TableConfig(
        "soft_skills", "portfolio_soft_skills", "Soft Skills", "Resume", "people",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("label", "Label", required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("label", "sort_order"),
    ),
    "work_categories": TableConfig(
        "work_categories", "work_categories", "Work Categories", "Projects", "folder",
        pk="id", pk_kind="text",
        fields=(Field("id", "Category ID", required=True), Field("label", "Label", required=True), Field("sort_order", "Sort Order", kind="number", default=0)),
        table_columns=("id", "label", "sort_order"),
    ),
    "projects": TableConfig(
        "projects", "portfolio_projects", "Projects", "Projects", "kanban",
        pk="slug", pk_kind="text",
        fields=(
            Field("slug", "Slug", required=True),
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("title", "Title", required=True),
            Field("category_id", "Category", kind="select", relation="work_categories", required=True),
            Field("project_year", "Year"),
            Field("description", "Short Description", kind="textarea", full=True, required=True),
            Field("detail", "Detail", kind="textarea", full=True, required=True),
            Field("image_path", "Project Image", kind="image", full=True),
            Field("featured", "Featured", kind="checkbox", default=False),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("title", "category_id", "project_year", "featured", "sort_order"),
    ),
    "project_tools": TableConfig(
        "project_tools", "portfolio_project_tools", "Project Tools", "Projects", "wrench",
        fields=(
            Field("project_slug", "Project", kind="select", relation="projects", required=True),
            Field("name", "Tool", required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("project_slug", "name", "sort_order"),
    ),
    "project_links": TableConfig(
        "project_links", "portfolio_project_links", "Project Links", "Projects", "link-45deg",
        fields=(
            Field("project_slug", "Project", kind="select", relation="projects", required=True),
            Field("label", "Label", required=True),
            Field("url", "URL", full=True, required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("project_slug", "label", "url", "sort_order"),
    ),
    "video_categories": TableConfig(
        "video_categories", "video_categories", "Video Categories", "Media", "collection-play",
        pk="id", pk_kind="text",
        fields=(Field("id", "Category ID", required=True), Field("label", "Label", required=True), Field("sort_order", "Sort Order", kind="number", default=0)),
        table_columns=("id", "label", "sort_order"),
    ),
    "videos": TableConfig(
        "videos", "portfolio_videos", "Videos", "Media", "youtube",
        fields=(
            Field("profile_id", "Profile", hidden=True, default="segun-banji"),
            Field("video_id", "YouTube Video ID", required=True),
            Field("title", "Title", required=True),
            Field("description", "Description", kind="textarea", full=True, required=True),
            Field("category_id", "Category", kind="select", relation="video_categories", required=True),
            Field("sort_order", "Sort Order", kind="number", default=0),
        ),
        table_columns=("title", "video_id", "category_id", "sort_order"),
    ),
    "messages": TableConfig(
        "messages", "contact_messages", "Contact Messages", "Inbox", "inbox",
        order="created_at.desc",
        readonly=True,
        description="Messages submitted from the public contact form.",
        table_columns=("name", "email", "subject", "created_at"),
    ),
}


NAV_GROUPS = ("Profile", "Resume", "Projects", "Media", "Inbox")
