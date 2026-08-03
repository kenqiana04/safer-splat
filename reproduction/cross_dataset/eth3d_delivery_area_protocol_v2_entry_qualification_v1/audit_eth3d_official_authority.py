#!/usr/bin/env python3
"""Freeze only official ETH3D/3DGS metadata and small text authorities."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


HTML_SOURCES = [
    ("eth3d_home", "https://www.eth3d.net/", ["data license", "MVS paper"]),
    ("eth3d_mvs_overview", "https://www.eth3d.net/overview", ["MVS benchmark family", "DSLR and rig variants"]),
    ("eth3d_mvs_datasets", "https://www.eth3d.net/datasets", ["Delivery Area variants", "archive filenames", "declared sizes"]),
    ("eth3d_mvs_documentation", "https://www.eth3d.net/documentation", ["COLMAP calibration", "ground-truth provenance", "evaluation source link"]),
    ("eth3d_slam_overview", "https://www.eth3d.net/slam_overview", ["SLAM benchmark exclusion"]),
    ("eth3d_slam_datasets", "https://www.eth3d.net/slam_datasets", ["SLAM dataset namespace exclusion"]),
    ("eth3d_slam_documentation", "https://www.eth3d.net/slam_documentation", ["SLAM sensor modalities exclusion"]),
]

REPOSITORIES = [
    "ETH3D/dataset-pipeline",
    "ETH3D/multi-view-evaluation",
    "ETH3D/format-loader",
    "graphdeco-inria/gaussian-splatting",
]

SMALL_TEXT_PATHS = {
    "ETH3D/dataset-pipeline": ["README.md", "LICENSE"],
    "ETH3D/multi-view-evaluation": ["README.md", "LICENSE.txt"],
    "ETH3D/format-loader": ["README.md", "LICENSE.txt"],
    "graphdeco-inria/gaussian-splatting": [
        "README.md",
        "LICENSE.md",
        ".gitmodules",
        "train.py",
        "arguments/__init__.py",
        "scene/dataset_readers.py",
        "scene/gaussian_model.py",
    ],
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, method: str = "GET") -> tuple[bytes, dict]:
    token = os.environ.get("GITHUB_TOKEN") if "github.com" in url else None
    headers = {
        "User-Agent": "safer-splat-protocol-v2-metadata-audit/1.0",
        "Accept": "application/vnd.github+json" if "api.github.com" in url else "*/*",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url,
        method=method,
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read() if method == "GET" else b""
        meta = {
            "requested_url": url,
            "final_url": response.geturl(),
            "http_status": response.status,
            "retrieval_utc": utc_now(),
            "content_type": response.headers.get("Content-Type"),
            "content_length_header": response.headers.get("Content-Length"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }
        return body, meta


def title_from_html(data: bytes) -> str | None:
    text = data.decode("utf-8", errors="replace")
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    if not match:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    out = root / "official_authority"
    out.mkdir(parents=True, exist_ok=True)

    counters = {
        "official_html_fetch_count": 0,
        "github_api_metadata_fetch_count": 0,
        "small_official_text_fetch_count": 0,
        "official_paper_head_count": 0,
        "dataset_archive_download_count": 0,
        "dataset_payload_bytes": 0,
    }
    web_identities = []
    authority_registry = []

    for key, url, cited_fields in HTML_SOURCES:
        data, meta = fetch(url)
        counters["official_html_fetch_count"] += 1
        path = out / f"{key}.html"
        path.write_bytes(data)
        identity = {
            **meta,
            "authority_id": key,
            "title": title_from_html(data),
            "sha256": sha256(data),
            "bytes": len(data),
            "snapshot_path": path.relative_to(root).as_posix(),
            "cited_fields": cited_fields,
            "authority_level": "OFFICIAL_PRIMARY",
        }
        web_identities.append(identity)
        authority_registry.append(identity)

    paper_url = "https://www.eth3d.net/data/schoeps2017cvpr.pdf"
    _, paper_meta = fetch(paper_url, method="HEAD")
    counters["official_paper_head_count"] += 1
    paper_identity = {
        **paper_meta,
        "authority_id": "eth3d_cvpr2017_paper_head",
        "title": "A Multi-View Stereo Benchmark with High-Resolution Images and Multi-Camera Videos",
        "sha256": None,
        "bytes": 0,
        "cited_fields": ["benchmark definition", "evaluation protocol"],
        "authority_level": "OFFICIAL_PRIMARY_HEAD_ONLY",
    }
    web_identities.append(paper_identity)
    authority_registry.append(paper_identity)

    repo_identities = []
    for repo in REPOSITORIES:
        repo_url = f"https://api.github.com/repos/{repo}"
        repo_body, repo_meta = fetch(repo_url)
        counters["github_api_metadata_fetch_count"] += 1
        repo_json = json.loads(repo_body)
        default_branch = repo_json["default_branch"]

        commit_url = f"https://api.github.com/repos/{repo}/commits/{default_branch}"
        commit_body, commit_meta = fetch(commit_url)
        counters["github_api_metadata_fetch_count"] += 1
        commit_json = json.loads(commit_body)
        head = commit_json["sha"]

        tree_url = f"https://api.github.com/repos/{repo}/git/trees/{head}?recursive=1"
        tree_body, tree_meta = fetch(tree_url)
        counters["github_api_metadata_fetch_count"] += 1
        tree_json = json.loads(tree_body)
        submodules = [
            {"path": item["path"], "commit": item["sha"]}
            for item in tree_json.get("tree", [])
            if item.get("mode") == "160000" and item.get("type") == "commit"
        ]

        text_identities = []
        for relpath in SMALL_TEXT_PATHS[repo]:
            raw_url = f"https://raw.githubusercontent.com/{repo}/{head}/{relpath}"
            try:
                body, raw_meta = fetch(raw_url)
            except urllib.error.HTTPError as exc:
                if exc.code == 404 and relpath == ".gitmodules":
                    text_identities.append({"path": relpath, "status": 404, "required": False})
                    continue
                raise
            counters["small_official_text_fetch_count"] += 1
            safe_name = f"{repo.replace('/', '__')}__{relpath.replace('/', '__')}"
            snapshot = out / safe_name
            snapshot.write_bytes(body)
            text_identities.append(
                {
                    **raw_meta,
                    "path": relpath,
                    "sha256": sha256(body),
                    "bytes": len(body),
                    "snapshot_path": snapshot.relative_to(root).as_posix(),
                    "required": True,
                }
            )

        license_entry = next((x for x in text_identities if x.get("path", "").lower().startswith("license")), None)
        identity = {
            "repository": repo,
            "html_url": repo_json["html_url"],
            "description": repo_json.get("description"),
            "default_branch": default_branch,
            "head_commit": head,
            "head_commit_utc": commit_json["commit"]["committer"]["date"],
            "repo_api_identity": {**repo_meta, "sha256": sha256(repo_body), "bytes": len(repo_body)},
            "commit_api_identity": {**commit_meta, "sha256": sha256(commit_body), "bytes": len(commit_body)},
            "tree_api_identity": {**tree_meta, "sha256": sha256(tree_body), "bytes": len(tree_body)},
            "license_spdx_api": repo_json.get("license", {}).get("spdx_id") if repo_json.get("license") else None,
            "license_sha256": license_entry.get("sha256") if license_entry else None,
            "submodules": submodules,
            "small_text_identities": text_identities,
            "authority_level": "OFFICIAL_PRIMARY",
        }
        repo_identities.append(identity)
        authority_registry.append(
            {
                "authority_id": repo.replace("/", "__"),
                "title": repo,
                "requested_url": repo_json["html_url"],
                "final_url": repo_json["html_url"],
                "http_status": 200,
                "retrieval_utc": repo_meta["retrieval_utc"],
                "sha256": sha256(repo_body),
                "head_commit": head,
                "license_sha256": identity["license_sha256"],
                "cited_fields": ["repository identity", "README/source contract", "license", "submodules"],
                "authority_level": "OFFICIAL_PRIMARY",
            }
        )

    (out / "official_web_snapshot_identity.json").write_text(json.dumps(web_identities, indent=2) + "\n", encoding="utf-8")
    (out / "official_repo_identity.json").write_text(json.dumps(repo_identities, indent=2) + "\n", encoding="utf-8")
    (out / "primary_authority_registry.json").write_text(json.dumps(authority_registry, indent=2) + "\n", encoding="utf-8")
    (out / "metadata_fetch_counters.json").write_text(json.dumps(counters, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "authority_count": len(authority_registry), "counters": counters}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
