"""SynapseFlow dashboard - FastAPI app."""

from __future__ import annotations

from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from anim.agents import PipelineOrchestrator
from anim.blueprint.schema import Blueprint, Element, Scene, SceneType
from anim.input.extractor import extract_text
from anim.storage import Storage

app = FastAPI(title="SynapseFlow 2026", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MEDIA_DIR = Path("media")
VIDEOS_DIR = MEDIA_DIR / "videos"
storage = Storage(MEDIA_DIR)

# In-memory job status (simple)
jobs: dict[str, dict[str, Any]] = {}

# Sites: id -> { name, base_url, topics: [ { slug, title, description, url } ] }
# Topic slug is used for video matching and studio_url.
def _default_sites() -> dict[str, dict[str, Any]]:
    return {
        "systemdr": {
            "id": "systemdr",
            "name": "System Design Roadmap",
            "base_url": "https://systemdr.substack.com/",
            "topics": SYSTEM_DESIGN_TOPICS,
        }
    }


# System Design Interview Roadmap topics from https://systemdr.substack.com/ posts
# (2026 posts + key 2025 posts; full list in docs/systemdr-substack-topics.md)
SYSTEM_DESIGN_TOPICS = [
    # 2026
    {"slug": "chaos-engineering-implementation", "title": "Chaos Engineering Implementation Strategies", "description": "Testing resilience in distributed systems", "url": "https://systemdr.substack.com/p/chaos-engineering-implementation"},
    {"slug": "push-vs-pull-architectures-in-real", "title": "Push vs. Pull Architectures in Real-Time Systems", "description": "When to poll and when to push", "url": "https://systemdr.substack.com/p/push-vs-pull-architectures-in-real"},
    {"slug": "kubernetes-native-application-design", "title": "Kubernetes-Native Application Design", "description": "When your app becomes a bad Kubernetes citizen", "url": "https://systemdr.substack.com/p/kubernetes-native-application-design"},
    {"slug": "designing-a-chat-system-storing-history", "title": "Designing a Chat System: History, Read Receipts, Presence", "description": "Storing history, read receipts, and online status", "url": "https://systemdr.substack.com/p/designing-a-chat-system-storing-history"},
    {"slug": "infrastructure-as-code-architectural", "title": "Infrastructure as Code: Architectural Implications", "description": "Deploying infrastructure at scale", "url": "https://systemdr.substack.com/p/infrastructure-as-code-architectural"},
    {"slug": "high-frequency-trading-architecture", "title": "High-Frequency Trading Architecture", "description": "Kernel bypass, DPDK, ultra-low latency", "url": "https://systemdr.substack.com/p/high-frequency-trading-architecture"},
    {"slug": "designing-for-observability-from", "title": "Designing for Observability from Day One", "description": "Why your production system is a black box", "url": "https://systemdr.substack.com/p/designing-for-observability-from"},
    {"slug": "udp-vs-tcp-in-multiplayer-gaming", "title": "UDP vs. TCP in Multiplayer Gaming", "description": "State sync and lag compensation", "url": "https://systemdr.substack.com/p/udp-vs-tcp-in-multiplayer-gaming"},
    {"slug": "service-mesh-architecture-explained", "title": "Service Mesh Architecture Explained", "description": "The silent traffic controller", "url": "https://systemdr.substack.com/p/service-mesh-architecture-explained"},
    {"slug": "adaptive-bitrate-streaming-hls-vs", "title": "Adaptive Bitrate Streaming (HLS vs. DASH)", "description": "How YouTube optimizes video quality", "url": "https://systemdr.substack.com/p/adaptive-bitrate-streaming-hls-vs"},
    {"slug": "issue-166-api-gateway-design-patterns", "title": "API Gateway Design Patterns", "description": "Gateway patterns and trade-offs", "url": "https://systemdr.substack.com/p/issue-166-api-gateway-design-patterns"},
    {"slug": "geofencing-at-scale-quadtrees-geohashes", "title": "Geofencing at Scale", "description": "QuadTrees, geohashes, real-time location", "url": "https://systemdr.substack.com/p/geofencing-at-scale-quadtrees-geohashes"},
    {"slug": "graphql-federation-multi-service", "title": "GraphQL Federation: Multi-Service Schemas", "description": "Federated GraphQL at scale", "url": "https://systemdr.substack.com/p/graphql-federation-multi-service"},
    {"slug": "designing-real-time-leaderboards", "title": "Designing Real-Time Leaderboards", "description": "Redis sorted sets and architecture", "url": "https://systemdr.substack.com/p/designing-real-time-leaderboards"},
    {"slug": "zero-trust-security-architecture", "title": "Zero-Trust Security Architecture", "description": "Security without perimeter", "url": "https://systemdr.substack.com/p/zero-trust-security-architecture"},
    {"slug": "crdts-vs-operational-transformation", "title": "CRDTs vs. Operational Transformation", "description": "How Google Docs handles collaborative editing", "url": "https://systemdr.substack.com/p/crdts-vs-operational-transformation"},
    {"slug": "edge-computing-architecture-patterns", "title": "Edge Computing Architecture Patterns", "description": "Compute at the edge", "url": "https://systemdr.substack.com/p/edge-computing-architecture-patterns"},
    {"slug": "designing-for-low-latency-trading", "title": "Designing for Low-Latency Trading Systems", "description": "Ultra-low latency patterns", "url": "https://systemdr.substack.com/p/designing-for-low-latency-trading"},
    {"slug": "connection-exhaustion-in-high-traffic", "title": "Connection Exhaustion in High-Traffic Systems", "description": "Managing connections at scale", "url": "https://systemdr.substack.com/p/connection-exhaustion-in-high-traffic"},
    {"slug": "designing-systems-for-global-scale", "title": "Designing Systems for Global Scale: Airbnb Case Study", "description": "Global scale patterns", "url": "https://systemdr.substack.com/p/designing-systems-for-global-scale"},
    # 2025 (key posts)
    {"slug": "message-queues-explained-with-cafe", "title": "Message Queues Explained with Café Analogies", "description": "Queues and messaging patterns", "url": "https://systemdr.substack.com/p/message-queues-explained-with-cafe"},
    {"slug": "load-balancing-101-how-traffic-gets", "title": "Load Balancing 101: How Traffic Gets Distributed", "description": "Traffic distribution at scale", "url": "https://systemdr.substack.com/p/load-balancing-101-how-traffic-gets"},
    {"slug": "system-design-interview-roadmap-proxies", "title": "Proxies vs. API Gateways: Understanding the Differences", "description": "Proxy vs gateway trade-offs", "url": "https://systemdr.substack.com/p/system-design-interview-roadmap-proxies"},
    {"slug": "data-serialization-formats-json-protobuf", "title": "Data Serialization Formats: JSON, Protobuf, Avro", "description": "Serialization for performance", "url": "https://systemdr.substack.com/p/data-serialization-formats-json-protobuf"},
    {"slug": "fraud-detection-system-architecture", "title": "Fraud Detection System Architecture", "description": "Real-time and batch fraud detection", "url": "https://systemdr.substack.com/p/fraud-detection-system-architecture"},
    {"slug": "machine-learning-system-design-blueprint", "title": "Machine Learning System Design Blueprint", "description": "ML pipelines and serving", "url": "https://systemdr.substack.com/p/machine-learning-system-design-blueprint"},
    {"slug": "webrtc-system-design-video-conferencing", "title": "WebRTC System Design: Video Conferencing Architecture", "description": "Real-time video architecture", "url": "https://systemdr.substack.com/p/webrtc-system-design-video-conferencing"},
    {"slug": "designing-notification-systems-at", "title": "Designing Notification Systems at Scale", "description": "Push, email, in-app at scale", "url": "https://systemdr.substack.com/p/designing-notification-systems-at"},
    {"slug": "multi-tenant-system-architecture", "title": "Multi-Tenant System Architecture Patterns", "description": "Isolation and resource sharing", "url": "https://systemdr.substack.com/p/multi-tenant-system-architecture"},
    {"slug": "l4-vs-l7-load-balancers-the-trade", "title": "L4 vs. L7 Load Balancers: The Trade-offs", "description": "Layer 4 vs 7 explained", "url": "https://systemdr.substack.com/p/l4-vs-l7-load-balancers-the-trade"},
    {"slug": "implementing-recommendation-systems", "title": "Implementing Recommendation Systems at Scale", "description": "Collaborative filtering and ranking", "url": "https://systemdr.substack.com/p/implementing-recommendation-systems"},
    {"slug": "real-time-processing-systems-architecture", "title": "Real-Time Processing Systems: Architecture Patterns", "description": "Stream processing and low latency", "url": "https://systemdr.substack.com/p/real-time-processing-systems-architecture"},
    {"slug": "domain-driven-design-in-system-architecture", "title": "Domain-Driven Design in System Architecture", "description": "Bounded contexts and ubiquitous language", "url": "https://systemdr.substack.com/p/domain-driven-design-in-system-architecture"},
    {"slug": "event-driven-architectures-patterns", "title": "Event-Driven Architectures: Patterns and Anti-patterns", "description": "Events and message brokers", "url": "https://systemdr.substack.com/p/event-driven-architectures-patterns"},
    {"slug": "issue-141-site-reliability-engineering", "title": "Site Reliability Engineering: Core Principles", "description": "SLOs, error budgets, incident response", "url": "https://systemdr.substack.com/p/issue-141-site-reliability-engineering"},
    {"slug": "issue-140-database-failover-strategies", "title": "Database Failover Strategies Compared", "description": "Failover and HA for databases", "url": "https://systemdr.substack.com/p/issue-140-database-failover-strategies"},
    {"slug": "database-replication-master-slave", "title": "Database Replication: Master-Slave vs. Multi-Master", "description": "Replication patterns", "url": "https://systemdr.substack.com/p/database-replication-master-slave"},
    {"slug": "database-sharding-horizontal-partition", "title": "Database Sharding: Horizontal Partition Visualization", "description": "Sharding at scale", "url": "https://systemdr.substack.com/p/database-sharding-horizontal-partition"},
    {"slug": "consistent-hashing-how-cdns-and-caches", "title": "Consistent Hashing: How CDNs and Caches Scale", "description": "Consistent hashing explained", "url": "https://systemdr.substack.com/p/consistent-hashing-how-cdns-and-caches"},
    {"slug": "raft-consensus-algorithm-visualized", "title": "Raft Consensus Algorithm Visualized", "description": "Distributed consensus", "url": "https://systemdr.substack.com/p/raft-consensus-algorithm-visualized"},
    {"slug": "distributed-consensus-paxos-simplified", "title": "Distributed Consensus: Paxos Simplified", "description": "Paxos and consensus", "url": "https://systemdr.substack.com/p/distributed-consensus-paxos-simplified"},
    {"slug": "content-delivery-networks-how-netflix", "title": "Content Delivery Networks: How Netflix Delivers Movies", "description": "CDN architecture", "url": "https://systemdr.substack.com/p/content-delivery-networks-how-netflix"},
    {"slug": "caching-strategies-explained-to-a", "title": "Caching Strategies Explained", "description": "Cache-aside, write-through, invalidation", "url": "https://systemdr.substack.com/p/caching-strategies-explained-to-a"},
    {"slug": "microservices-vs-monoliths-visual", "title": "Microservices vs. Monoliths: Visual Decision Guide", "description": "When to split services", "url": "https://systemdr.substack.com/p/microservices-vs-monoliths-visual"},
    {"slug": "api-design-fundamentals-rest-vs-graphql", "title": "API Design Fundamentals: REST vs. GraphQL vs. gRPC", "description": "API styles compared", "url": "https://systemdr.substack.com/p/api-design-fundamentals-rest-vs-graphql"},
    {"slug": "the-cap-theorem-explained-with-pizza", "title": "The CAP Theorem Explained with Pizza Delivery Analogies", "description": "Consistency, availability, partition tolerance", "url": "https://systemdr.substack.com/p/the-cap-theorem-explained-with-pizza"},
    {"slug": "system-design-interviews-a-visual", "title": "System Design Interviews: A Visual Roadmap", "description": "Step-by-step interview process", "url": "https://systemdr.substack.com/p/system-design-interviews-a-visual"},
]

sites: dict[str, dict[str, Any]] = _default_sites()


def _run_generation(job_id: str, source: str, output_name: str):
    """Run generation via PipelineOrchestrator (Analyzer → WorkflowGenerator → Animator → Exporter)."""
    try:
        orch = PipelineOrchestrator(
            output_dir=MEDIA_DIR,
            quality="draft",
            storage=storage,
        )
        result = orch.generate(
            source,
            output_name=output_name or "generated",
        )
        jobs[job_id]["workflow"] = result.get("workflow", [])
        jobs[job_id]["status"] = result.get("status", "done")
        jobs[job_id]["path"] = result.get("url") or result.get("path", "")
        jobs[job_id]["output_name"] = result.get("output_name", output_name or "generated")
        jobs[job_id]["storage_id"] = result.get("storage_id")
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


def _workflow_from_blueprint(blueprint) -> list[dict]:
    """Extract workflow (scenes) from Blueprint for UI display."""
    out = []
    for i, s in enumerate(blueprint.scenes, 1):
        scene = {
            "index": i,
            "id": s.id,
            "type": s.scene_type.value,
            "duration": s.duration_seconds,
        }
        if s.elements:
            scene["content"] = [e.content[:80] + ("..." if len(e.content) > 80 else "") for e in s.elements[:3]]
        elif s.narration:
            scene["content"] = [s.narration[:80] + ("..." if len(s.narration) > 80 else "")]
        elif s.nodes:
            scene["content"] = [f"{n.id}: {n.label}" for n in s.nodes[:5]]
        else:
            scene["content"] = []
        out.append(scene)
    return out


def _list_videos() -> list[dict[str, str]]:
    """List rendered videos from media directory."""
    videos = []
    if not VIDEOS_DIR.exists():
        return videos
    for mp4 in VIDEOS_DIR.rglob("*.mp4"):
        rel = mp4.relative_to(MEDIA_DIR)
        videos.append({
            "name": mp4.stem,
            "path": f"/media/{rel.as_posix()}",
            "size_mb": round(mp4.stat().st_size / (1024 * 1024), 2),
        })
    return sorted(videos, key=lambda v: v["path"], reverse=True)


def _video_for_slug(slug: str, videos: list[dict]) -> dict | None:
    """Find a video whose name matches the topic slug (stem equals or contains slug)."""
    slug_lower = slug.lower().replace(" ", "-")
    for v in videos:
        name_lower = v["name"].lower()
        if name_lower == slug_lower or slug_lower in name_lower:
            return v
    return None


def _topic_slug(title: str, url: str) -> str:
    """Generate a URL-safe slug from title or URL."""
    if not title:
        from urllib.parse import urlparse
        path = urlparse(url).path.rstrip("/")
        title = path.split("/")[-1] if path else "topic"
    import re
    return re.sub(r"[^\w\-]", "-", title.lower()).strip("-") or "topic"


def _topics_with_videos(sites_dict: dict[str, dict[str, Any]] | None = None) -> list[dict]:
    """Return each topic from all sites with optional video, studio URL, post URL, and site info."""
    from urllib.parse import quote

    use_sites = sites_dict if sites_dict is not None else sites
    videos = _list_videos()
    out = []
    for site_id, site_data in use_sites.items():
        name = site_data.get("name", site_id)
        base_url = site_data.get("base_url", "")
        for t in site_data.get("topics", []):
            slug = t.get("slug") or _topic_slug(t.get("title", ""), t.get("url", ""))
            topic = {**t, "slug": slug}
            video = _video_for_slug(slug, videos)
            studio_url = "/studio?concept=" + quote(topic.get("title", slug), safe="")
            out.append({
                **topic,
                "video": video,
                "studio_url": studio_url,
                "url": topic.get("url"),
                "site_id": site_id,
                "site_name": name,
                "base_url": base_url,
            })
    return out


def _render_template(name: str, **kwargs) -> str:
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))
    return env.get_template(name).render(**kwargs)


@app.get("/api/topics")
async def api_topics():
    """Return all topics from all sites for Studio topic selector (with site_id, site_name)."""
    return {"topics": _topics_with_videos()}


class TopicInput(BaseModel):
    title: str
    url: str = ""
    description: str = ""


class AddSiteBody(BaseModel):
    name: str
    base_url: str = ""
    topics: list[TopicInput]


def _site_id_from_name(name: str) -> str:
    import re
    return re.sub(r"[^\w\-]", "-", name.lower()).strip("-") or "site"


@app.get("/api/sites")
async def api_sites():
    """List all sites with their topics (for add-site UI and grouping)."""
    out = []
    for site_id, data in sites.items():
        topics_with_video = _topics_with_videos({site_id: data})
        out.append({
            "id": site_id,
            "name": data.get("name", site_id),
            "base_url": data.get("base_url", ""),
            "topics": topics_with_video,
        })
    return {"sites": out}


@app.post("/api/sites")
async def api_add_site(body: AddSiteBody):
    """Add a new site with its topics. Topics get slugs generated from title/url."""
    site_id = _site_id_from_name(body.name)
    if site_id in sites:
        n = 1
        while f"{site_id}-{n}" in sites:
            n += 1
        site_id = f"{site_id}-{n}"
    topic_list = []
    for t in body.topics:
        slug = _topic_slug(t.title, t.url or "")
        topic_list.append({
            "slug": slug,
            "title": t.title,
            "description": t.description or "",
            "url": t.url or "",
        })
    sites[site_id] = {
        "id": site_id,
        "name": body.name.strip(),
        "base_url": (body.base_url or "").strip().rstrip("/"),
        "topics": topic_list,
    }
    return {"id": site_id, "name": sites[site_id]["name"], "topics_count": len(topic_list)}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render dashboard HTML with System Design topics and existing videos (Jinja)."""
    videos = _list_videos()
    topics_with_videos = _topics_with_videos()
    return _render_template(
        "dashboard.html",
        request=request,
        videos=videos,
        topics_with_videos=topics_with_videos,
        jobs=list(jobs.values()),
        active_tab="dashboard",
    )


@app.post("/generate")
async def generate(
    background_tasks: BackgroundTasks,
    source: str = Form(...),
    output_name: str = Form("output"),
):
    """Start video generation job."""
    import uuid

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"id": job_id, "status": "running", "source": source[:80], "workflow": []}
    background_tasks.add_task(_run_generation, job_id, source, output_name or "generated")
    return {"job_id": job_id, "status": "started"}


@app.get("/jobs/{job_id}")
async def job_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        return {"status": "not_found"}
    return jobs[job_id]


@app.get("/videos")
async def list_videos():
    """List rendered videos."""
    return {"videos": _list_videos()}


# --- Storage API (persistent animations & audio) ---

@app.get("/api/storage/animations")
async def api_storage_animations():
    """List all stored animations (from storage index)."""
    items = storage.list_animations()
    for e in items:
        e["url"] = f"/media/{e.get('path', '')}"
        e["size_mb"] = round((e.get("size_bytes") or 0) / (1024 * 1024), 2)
    return {"animations": items}


@app.get("/api/storage/audio")
async def api_storage_audio():
    """List all stored audio (from storage index)."""
    items = storage.list_audio()
    for e in items:
        e["url"] = f"/media/{e.get('path', '')}"
        e["size_mb"] = round((e.get("size_bytes") or 0) / (1024 * 1024), 2)
    return {"audio": items}


@app.delete("/api/storage/animations/{storage_id}")
async def api_delete_animation(storage_id: str):
    """Delete a stored animation."""
    if not storage.delete_animation(storage_id):
        raise HTTPException(status_code=404, detail="Animation not found")
    return {"deleted": storage_id}


@app.delete("/api/storage/audio/{storage_id}")
async def api_delete_audio(storage_id: str):
    """Delete stored audio."""
    if not storage.delete_audio(storage_id):
        raise HTTPException(status_code=404, detail="Audio not found")
    return {"deleted": storage_id}


@app.get("/media/{path:path}")
async def serve_media(path: str):
    """Serve media files (videos and audio)."""
    full = MEDIA_DIR / path
    if not full.exists() or not full.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    if path.startswith("audio/") or path.endswith(".wav"):
        return FileResponse(full, media_type="audio/wav")
    return FileResponse(full, media_type="video/mp4")


# --- Studio (ArchitectSVG-style) ---

@app.get("/studio", response_class=HTMLResponse)
async def studio_page(request: Request):
    """Studio: SVG + audio generation with video capture."""
    html = _render_template("studio.html", request=request, active_tab="studio")
    return Response(content=html, media_type="text/html", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


@app.post("/studio/generate")
async def studio_generate(
    concept: str = Form(...),
    aspect_ratio: str = Form("16:9"),
    target_duration_seconds: float | None = Form(None),
):
    """
    Studio: accept any input — topic, topic+description, description, article, or workflow steps.
    Research and think as Technology Architect; build detailed workflow (actors, entities,
    components, communication, state transitions, realtime issues, complex architectures);
    then generate SVG + script. Uses WorkflowGenerator (Gemini), Validators (SVG), Judge (quality/sync).
    """
    from anim.agents import JudgeAgent, TimelineValidatorAgent
    from anim.web.services.gemini_service import generate_svg_and_script_with_workflow

    try:
        duration = max(90.0, float(target_duration_seconds)) if target_duration_seconds is not None else 90.0
        result = generate_svg_and_script_with_workflow(
            concept, aspect_ratio=aspect_ratio, target_duration_seconds=duration
        )
        timeline = result.get("timeline") or []
        if timeline:
            result["timeline"] = TimelineValidatorAgent().run(timeline)
        script = result.get("voiceover_script") or result.get("full_script", "")
        judge_result = JudgeAgent().run(
            timeline=result.get("timeline"),
            full_script=script,
            target_duration_seconds=duration,
        )
        result["judge"] = {"passed": judge_result.passed, "feedback": judge_result.feedback}
        return result
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            return _fallback_studio_output(concept)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _fallback_studio_output(concept: str) -> dict[str, Any]:
    """Fallback when no Gemini API key: template SVG + script."""
    from anim.agents.svg_validator import SvgValidationAgent

    script = f"This diagram illustrates: {concept}. The process flows from left to right. Each step builds on the previous one."
    svg = f'''<svg id="root" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 540" width="960" height="540">
  <style>
    .panel {{ fill: var(--panel-bg, #1e293b); stroke: var(--accent-primary, #3b82f6); stroke-width: 2; }}
    .text {{ fill: var(--text-primary, #e2e8f0); font-family: Inter, sans-serif; font-size: 16px; }}
    .step {{ fill: var(--accent-primary, #3b82f6); opacity: 0.9; }}
  </style>
  <rect width="100%" height="100%" fill="var(--bg-canvas, #0a0a0b)"/>
  <rect x="40" y="40" width="280" height="120" rx="8" class="panel"/>
  <text x="60" y="75" class="text">Concept: {concept[:40]}...</text>
  <text x="60" y="110" class="text" font-size="14">Step 1: Input</text>
  <text x="60" y="135" class="text" font-size="14">Step 2: Process</text>
  <circle cx="450" cy="270" r="60" class="step"><animate attributeName="opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/></circle>
  <text x="420" y="280" class="text" font-size="14">Flow</text>
  <circle cx="750" cy="270" r="40" class="step"/>
  <text x="730" y="275" class="text" font-size="12">Output</text>
  <path d="M400 270 L340 270" stroke="var(--accent-primary)" stroke-width="3" fill="none"/>
  <path d="M550 270 L690 270" stroke="var(--accent-primary)" stroke-width="3" fill="none"/>
</svg>'''
    svg = SvgValidationAgent().validate_and_fix(svg)
    return {
        "workflow_spec": {"title": concept[:50], "summary": script, "input_type": "topic", "actors": [], "entities": [], "components": [], "communication": [], "state_transitions": [], "steps": []},
        "svg_source": svg,
        "voiceover_script": script,
        "timeline": [],
    }


class NarrateBody(BaseModel):
    text: str
    voice: str = "Kore"
    save: bool = True  # Save to storage by default


@app.post("/studio/narrate")
async def studio_narrate(body: NarrateBody):
    """Generate narration audio via Gemini TTS. Returns base64 WAV and optionally saves to storage."""
    from anim.web.services.gemini_service import generate_audio
    import base64

    try:
        audio_b64 = generate_audio(body.text, voice=body.voice)
        wav_bytes = base64.b64decode(audio_b64)
        payload: dict[str, Any] = {"audio_base64": audio_b64, "mime_type": "audio/wav"}
        if body.save:
            title = (body.text[:50] + "…") if len(body.text) > 50 else body.text
            sid = storage.save_audio(
                wav_bytes,
                title=title or "Narration",
                script_preview=body.text[:200],
                voice=body.voice,
            )
            payload["storage_id"] = sid
            payload["audio_url"] = f"/media/audio/{sid}.wav"
        return payload
    except ValueError as e:
        msg = str(e)
        if "GEMINI_API_KEY" in msg:
            raise HTTPException(
                status_code=503,
                detail="Narration requires GEMINI_API_KEY. Add GEMINI_API_KEY to a .env file in the project root or set it as an environment variable, then restart the app.",
            )
        raise HTTPException(status_code=400, detail=msg)
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e) or "Narration requires pip install google-genai. Install it and restart the app.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/studio/export-blueprint")
async def studio_export_blueprint(
    background_tasks: BackgroundTasks,
    script: str = Form(...),
    title: str = Form("Studio Export"),
    output_name: str = Form("studio_export"),
):
    """Convert script to Blueprint and render via PipelineOrchestrator (WorkflowGenerator → Animator → Exporter)."""
    import uuid

    from anim.agents import PipelineOrchestrator
    from anim.blueprint.schema import Element, Scene, SceneType

    # Parse script into scenes (simple: split by sentences)
    sentences = [s.strip() for s in script.replace("\n", " ").split(". ") if s.strip()]
    scenes = []
    for i, sent in enumerate(sentences[:8], 1):
        scenes.append(
            Scene(
                id=f"s{i}",
                scene_type=SceneType.TEXT if i > 1 else SceneType.TITLE,
                duration_seconds=3.0,
                elements=[Element(content=sent + ("" if sent.endswith(".") else "."))],
                narration=sent,
            )
        )
    if not scenes:
        scenes = [Scene(id="s1", scene_type=SceneType.TITLE, elements=[Element(content=title)])]

    blueprint = Blueprint(title=title, scenes=scenes)
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "id": job_id,
        "status": "running",
        "source": title,
        "workflow": _workflow_from_blueprint(blueprint),
    }

    def _render():
        try:
            orch = PipelineOrchestrator(output_dir=MEDIA_DIR, quality="draft", storage=storage)
            result = orch.render_blueprint(blueprint, output_name=output_name)
            jobs[job_id]["status"] = result.get("status", "done")
            jobs[job_id]["path"] = result.get("url") or result.get("path", "")
            jobs[job_id]["storage_id"] = result.get("storage_id")
            jobs[job_id]["output_name"] = result.get("output_name", output_name)
        except Exception as e:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)

    background_tasks.add_task(_render)
    return {"job_id": job_id, "status": "started"}


# Serve React SPA (Studio) at / when frontend is built
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="spa")
else:
    # Fallback: redirect / to dashboard when React app not built
    @app.get("/", response_class=HTMLResponse)
    async def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard", status_code=302)
