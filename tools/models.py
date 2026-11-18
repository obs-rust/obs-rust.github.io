"""Typed data structures for the site build (tools/build.py, mcp.py, corpus.py, check.py).

Every JSON boundary parses into a pydantic model here; business logic then uses attribute
access only. Two bases:

  * ``Ours``   frozen, ``extra="forbid"``: files this project writes or owns (sessions, the
               corpus, the MCP artifacts, obs-studio's control-api schema and .mcp.json), so
               an unexpected key fails the build instead of being dropped silently.
  * ``Theirs`` frozen, ``extra="ignore"``: third-party JSON (GitHub API, protocol.json,
               the leaderboard's conversion.json) of which only the used fields are modelled.

JSON Schema bodies are arbitrary, so they stay ``JsonSchema`` (``dict[str, JsonValue]``) and are
walked by the typed helpers in mcp.py. Internal records are frozen, slotted dataclasses.

Field order matters: models serialize in declaration order, and the output must stay
byte-identical, so each model lists its fields in the order the source JSON carries them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, RootModel, TypeAdapter

type JsonSchema = dict[str, JsonValue]
JSON_SCHEMA = TypeAdapter[JsonSchema](dict[str, JsonValue])

Tier = Literal["core", "process", "reference", "archive"]
ChunkKind = Literal["prose", "ws-request", "ws-event", "ws-enum", "mcp-tool", "mcp-resource", "c-symbol",
                    "ledger-entry", "ledger-fix"]


class Ours(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Theirs(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")


class Upstream(BaseModel):
    """Upstream obs-studio data that this site republishes: unknown keys pass through, so a new
    upstream field (e.g. a new MCP annotation hint) neither breaks the daily build nor is dropped."""

    model_config = ConfigDict(frozen=True, extra="allow")


# ---------------------------------------------------------------- GitHub API
class GhLanguages(RootModel[dict[str, int]]):
    """GET /repos/{repo}/languages: language name -> bytes."""

    model_config = ConfigDict(frozen=True)

    def bytes_of(self, lang: str) -> int:
        return self.root.get(lang, 0)

    def total(self) -> int:
        return sum(self.root.values())


class GhRepo(Theirs):
    stargazers_count: int = 0
    forks_count: int = 0


class GhAsset(Theirs):
    name: str
    browser_download_url: str
    size: int


class GhCommitRef(Theirs):
    """GET /repos/{repo}/commits/{ref}: only the resolved SHA is used."""

    sha: str


class GhRelease(Theirs):
    tag_name: str
    name: str | None = None
    html_url: str
    published_at: str | None = None
    prerelease: bool = False
    assets: list[GhAsset] = []


class GhReleases(RootModel[list[GhRelease]]):
    model_config = ConfigDict(frozen=True)


# ---------------------------------------------------------------- leaderboard conversion.json
class ConvPercent(Theirs):
    percent: float


class ConvLibobs(Theirs):
    all: ConvPercent


class Conversion(Theirs):
    commit: str
    date: str
    libobs: ConvLibobs
    app: ConvPercent


# ---------------------------------------------------------------- obs-websocket protocol.json
class WsField(Theirs):
    valueName: str
    valueType: str
    valueDescription: str
    valueRestrictions: str | None = None
    valueOptional: bool | None = None
    valueOptionalBehavior: str | None = None


class WsRequest(Theirs):
    description: str
    requestType: str
    complexity: int
    deprecated: bool
    initialVersion: str
    category: str
    requestFields: list[WsField]
    responseFields: list[WsField]


class WsEvent(Theirs):
    description: str
    eventType: str
    eventSubscription: str
    deprecated: bool
    initialVersion: str
    category: str
    dataFields: list[WsField]


class WsEnumIdentifier(Theirs):
    description: str
    enumIdentifier: str
    enumValue: int | float | str


class WsEnumType(Theirs):
    enumType: str
    enumIdentifiers: list[WsEnumIdentifier]


class WsProtocol(Theirs):
    enums: list[WsEnumType]
    requests: list[WsRequest]
    events: list[WsEvent]


class WsRequestPayload(Ours):
    requestType: str
    requestId: str
    requestData: dict[str, JsonValue] | None = None


class WsRequestMessage(Ours):
    """An op 6 Request message, as shown in the reference's examples."""

    op: Literal[6] = 6
    d: WsRequestPayload


# ---------------------------------------------------------------- MCP surface
class ToolAnnotations(Upstream):
    destructiveHint: bool
    idempotentHint: bool
    openWorldHint: bool
    readOnlyHint: bool


class ControlApiTool(Upstream):
    name: str
    inputSchema: JsonSchema
    outputSchema: JsonSchema
    annotations: ToolAnnotations


class ControlApiSchema(Upstream):
    """obs-studio docs/rust-port/control-api.schema.json."""

    tools: list[ControlApiTool]
    toolError: JsonSchema


class McpTool(Ours):
    name: str
    description: str
    inputSchema: JsonSchema
    outputSchema: JsonSchema
    annotations: ToolAnnotations


class McpResource(Ours):
    uri: str
    name: str
    description: str
    mimeType: str


class ToolError(Ours):
    """structuredContent of a failed tool call (isError: true)."""

    code: int
    category: str
    message: str
    retryable: bool


class McpServerConfig(Theirs):
    command: str
    args: list[str] = []
    env: dict[str, str] | None = None


class McpJson(Theirs):
    """A client config (.mcp.json, claude_desktop_config.json)."""

    mcpServers: dict[str, McpServerConfig]


# ---------------------------------------------------------------- MCP session transcripts (mcp/sessions/*.jsonl)
type JsonRpcId = int | str


class TextContent(Ours):
    type: Literal["text"] = "text"
    text: str


class ToolCallParams(Ours):
    name: str
    arguments: dict[str, JsonValue]


class ToolCallRequest(Ours):
    jsonrpc: Literal["2.0"]
    id: JsonRpcId
    method: Literal["tools/call"]
    params: ToolCallParams


class JsonRpcRequest(Ours):
    jsonrpc: Literal["2.0"]
    id: JsonRpcId
    method: str
    params: dict[str, JsonValue] | None = None


class JsonRpcNotification(Ours):
    jsonrpc: Literal["2.0"]
    method: str
    params: dict[str, JsonValue] | None = None


class ToolCallResult(Ours):
    content: list[TextContent] | None = None
    structuredContent: dict[str, JsonValue]
    isError: bool


class JsonRpcResponse(Ours):
    jsonrpc: Literal["2.0"]
    id: JsonRpcId
    result: ToolCallResult | dict[str, JsonValue] = Field(union_mode="left_to_right")


type JsonRpcMessage = ToolCallRequest | JsonRpcRequest | JsonRpcNotification | JsonRpcResponse


class SessionHead(Ours):
    order: int = 99
    title: str
    summary: str
    caveat: str | None = None


class SessionStep(Ours):
    from_: Literal["agent", "server"] = Field(validation_alias="from")
    note: str | None = None
    msg: JsonRpcMessage = Field(union_mode="left_to_right")

    def msg_json(self) -> str:
        return msg_json(self.msg)


def msg_json(msg: JsonRpcMessage) -> str:
    """Compact JSON of a JSON-RPC message, as written to the .jsonl transcripts."""
    return json.dumps(msg.model_dump(mode="json", exclude_none=True), separators=(",", ":"))


# ---------------------------------------------------------------- MCP artifacts (/mcp/*.json)
class ServerCapabilities(Ours):
    tools: dict[str, JsonValue] = {}
    resources: dict[str, JsonValue] = {}


class ServerInfo(Ours):
    name: str
    version: str | None
    protocolVersion: str
    capabilities: ServerCapabilities
    transport: list[str]


class SchemaSource(Ours):
    repo: str
    commit: str
    paths: list[str]


class McpSchemaFile(Ours):
    """/mcp/schema.json: pre-fetched tools/list + resources/list + ToolError."""

    schema_version: int
    generated: str
    source: SchemaSource
    server: ServerInfo
    tools: list[McpTool]
    resources: list[McpResource]
    resourceTemplates: list[JsonValue]
    prompts: list[JsonValue]
    toolError: JsonSchema


class ToolsFile(Ours):
    tools: list[McpTool]


class ResourcesFile(Ours):
    resources: list[McpResource]


class Permissions(Ours):
    allow: list[str]


class AllowlistFile(Ours):
    permissions: Permissions


class RegistryRepository(Ours):
    url: str
    source: str
    subfolder: str


class RegistryServer(Ours):
    """/mcp/server.json for the MCP registry (validated against tools/vendor/server.schema.json)."""

    schema_: str = Field(serialization_alias="$schema")
    name: str
    title: str
    description: str
    version: str
    websiteUrl: str
    repository: RegistryRepository


# ---------------------------------------------------------------- AI corpus (/ai/corpus.json, DESIGN.md §7)
class Chunk(Ours):
    id: str
    doc: str
    group: str
    tier: Tier
    kind: ChunkKind
    breadcrumb: list[str]
    url: str
    source: str
    text: str
    chars: int
    tokens_est: int
    sha256: str


class DocRef(Ours):
    slug: str
    group: str
    tier: Tier
    title: str
    path: str
    url: str
    site_url: str


class CorpusFile(Ours):
    schema_version: int
    generated: str
    obs_studio_commit: str
    obs_websocket_commit: str
    docs: list[DocRef]
    chunks: list[Chunk]


# ---------------------------------------------------------------- internal records
@dataclass(frozen=True, slots=True)
class Doc:
    """One corpus document (DESIGN.md §7)."""

    group: str
    path: str
    text: str
    url: str
    title: str
    slug: str
    site_url: str
    tier: Tier
    source: str

    def ref(self) -> DocRef:
        return DocRef(slug=self.slug, group=self.group, tier=self.tier, title=self.title, path=self.path,
                      url=self.url, site_url=self.site_url)


@dataclass(frozen=True, slots=True)
class LedgerItem:
    section: str
    area: str
    text: str


@dataclass(frozen=True, slots=True)
class Feature(LedgerItem):
    name: str
    platforms: str
    date: str
    desc: str
    pr: str


@dataclass(frozen=True, slots=True)
class Ledger:
    features: list[Feature]
    fixed: list[LedgerItem]


@dataclass(frozen=True, slots=True)
class FieldRow:
    """One property of a JSON Schema object, as shown in the MCP reference."""

    name: str
    type: str
    required: bool
    default: JsonValue
    description: str


@dataclass(frozen=True, slots=True)
class Surface:
    """The MCP surface of obs-studio-rust."""

    tools: list[McpTool]
    resources: list[McpResource]
    tool_error: JsonSchema
    protocol: str
    version: str | None
    mcp_json: McpJson


@dataclass(frozen=True, slots=True)
class Session:
    slug: str
    head: SessionHead
    steps: list[SessionStep]


@dataclass(frozen=True, slots=True)
class Feed:
    name: str
    path: str
    size: int


@dataclass(frozen=True, slots=True)
class RepoStats:
    rust_pct: float
    c_pct: float
    cpp_pct: float
    other_pct: float
    rust_mb: str
    c_mb: str
    cpp_mb: str
    libobs_pct: str
    app_pct: str
    conv_commit: str
    conv_blob_sha: str
    conv_date: str
    stars: int
    forks: int


@dataclass(frozen=True, slots=True)
class McpStats:
    n_tools: int
    n_resources: int
    n_ro: int
    n_idem: int
    n_mut: int
    ro_allow: str
    schema_kb: str


class RouterRow(Ours):
    """One agent task -> the one file to fetch first."""

    task: str
    path: str
    bytes: int


class ManifestDoc(Ours):
    slug: str
    path: str
    title: str
    tier: Tier
    group: str
    url: str
    source: str
    bytes: int
    sha256: str


class Manifest(Ours):
    """/ai/manifest.json: every /ai/docs/*.md with its size and SHA-256."""

    schema_version: int
    generated: str
    obs_studio_commit: str
    obs_websocket_commit: str
    docs: list[ManifestDoc]


@dataclass(frozen=True, slots=True)
class Checksums:
    """A release's SHA256SUMS file: asset name -> lowercase hex digest."""

    by_name: dict[str, str]

    @staticmethod
    def parse(data: bytes) -> "Checksums":
        out: dict[str, str] = {}
        for line in data.decode().splitlines():
            if not line.strip():
                continue
            digest, _, name = line.partition("  ")
            if len(digest) != 64 or not name:
                raise ValueError(f"SHA256SUMS: bad line {line!r}")
            out[name.lstrip("*").strip()] = digest.lower()
        return Checksums(by_name=out)


@dataclass(frozen=True, slots=True)
class Channel:
    """A download channel: the newest stable or the newest beta obs-studio-rust-v* release."""

    name: str
    note: str
    rel: GhRelease
    sums: Checksums


@dataclass(frozen=True, slots=True)
class Limit:
    """A known limitation, quoted from the README; the build fails when the pattern stops matching."""

    os: str
    text: str
    readme_pattern: str


@dataclass(frozen=True, slots=True)
class HeroImage:
    """The upstream main-window screenshot, re-encoded for the hero."""

    hero_src: str
    hero_w: int
    hero_h: int
    hero_kb: str


@dataclass(frozen=True, slots=True)
class LedgerPicture:
    """Upstream's two status-bar captures (hardware GPU, CPU rendering), shown beside their features-ledger entry."""

    gpu_src: str
    gpu_w: int
    gpu_h: int
    gpu_alt: str
    gpu2_src: str
    gpu2_w: int
    gpu2_h: int
    gpu2_alt: str
    gpu_intro: str
    gpu_name: str
    gpu_desc: str
    gpu_area: str
    gpu_platforms: str
    gpu_date: str
    gpu_href: str


@dataclass(frozen=True, slots=True)
class SocialCard:
    """The generated og:image: a PNG of exactly width x height, at most max_bytes."""

    path: str
    width: int
    height: int
    size: int


@dataclass(frozen=True, slots=True)
class PageContext:
    """Every {{placeholder}} a page template may use. Nested stats are flattened by as_mapping()."""

    stats: RepoStats
    mcp: McpStats
    hero: HeroImage
    gpu: LedgerPicture
    release_tag: str
    release_name: str
    release_url: str
    release_date: str
    downloads: str
    feature_cards: str
    n_features: int
    n_fixed: int
    n_requests: int
    n_events: int
    n_enums: int
    corpus_docs: int
    corpus_chunks: int
    corpus_mb: str
    ctx_kb: str
    ai_doc_list: str
    ai_router: str
    cta_version: str
    release_line: str
    limits: str
    build_date: str
    obs_sha: str
    obs_sha_short: str
    ws_sha: str
    ws_sha_short: str
    ws_items: str
    ws_nav: str
    mcp_protocol: str
    mcp_ref: str
    mcp_ref_nav: str
    mcp_sessions: str
    mcp_hero_tx: str
    mcp_json_pretty: str
    mcp_resources: str

    def as_mapping(self) -> dict[str, str]:
        out: dict[str, str] = {}
        _flatten(self, out)
        return out


def _flatten(obj: object, out: dict[str, str]) -> None:
    if not is_dataclass(obj):
        raise TypeError(f"not a dataclass: {obj!r}")
    for f in fields(obj):
        v: object = getattr(obj, f.name)
        if is_dataclass(v):
            _flatten(v, out)
        else:
            out[f.name] = str(v)


# ---------------------------------------------------------------- static site tables
@dataclass(frozen=True, slots=True)
class ToolGroup:
    """An MCP tool group on /mcp/, by what an agent is trying to do."""

    id: str
    name: str
    description: str
    tools: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DownloadOption:
    suffix: str
    label: str


@dataclass(frozen=True, slots=True)
class DownloadGroup:
    os_name: str
    arch: str
    options: tuple[DownloadOption, ...]
