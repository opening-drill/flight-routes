"""Lightweight HTTP server for container health checks."""

from __future__ import annotations

import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/health")
def health() -> tuple[dict[str, str], int]:
    return jsonify({"status": "ok", "service": "flight-routes"}), 200


@app.get("/")
def root() -> tuple[dict[str, str], int]:
    return jsonify({"service": "flight-routes", "health": "/health"}), 200


if __name__ == "__main__":
    host = os.getenv("HEALTH_HOST", "0.0.0.0")
    port = int(os.getenv("HEALTH_PORT", "8080"))
    app.run(host=host, port=port, threaded=True)
