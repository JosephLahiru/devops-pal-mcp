import os
import json
import time
import docker
from datetime import datetime
from docker.errors import NotFound, APIError, ImageNotFound
from mcp.server.fastmcp import FastMCP
import re

# =====================================================
# Utility Setup

def log_tool_call(tool_name, **kwargs):
    """Log MCP tool usage with timestamps."""
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    print(f"{timestamp} [MCP TOOL]: {tool_name} called with args: {kwargs}")

mcp = FastMCP(
    name="Knowledge Base",
    host="0.0.0.0",
    port=5005,
)

docker_client = docker.from_env()

# =====================================================
# General Tools (1–3)

# 1
@mcp.tool(description="Check if MCP tool calling works correctly")
def check_tool_calling() -> bool:
    """Returns True if tool calling is functional."""
    log_tool_call("check_tool_calling")
    return {"is_tool_calling_working": True}

# 2
@mcp.tool(description="Retrieve current date, time, and timezone details")
def get_current_date_time() -> dict:
    """Returns the current date, time, timezone, and UNIX timestamp."""
    log_tool_call("get_current_date_time")
    local_time = datetime.now()
    tz = datetime.now().astimezone().tzinfo
    return {
        "date": local_time.strftime("%Y-%m-%d"),
        "time": local_time.strftime("%H:%M:%S"),
        "day": local_time.strftime("%A"),
        "timezone": str(tz),
        "timestamp": int(time.time())
    }

# 3
@mcp.tool(description="Retrieve entire knowledge base content")
def get_knowledge_base() -> str:
    """Fetches and formats the knowledge base JSON file."""
    log_tool_call("get_knowledge_base")
    try:
        kb_path = os.path.join(os.path.dirname(__file__), "data", "kb.json")
        with open(kb_path, "r") as f:
            kb_data = json.load(f)
        kb_text = "Knowledge Base:\n\n"
        if isinstance(kb_data, list):
            for i, item in enumerate(kb_data, 1):
                q = item.get("question", "Unknown question")
                a = item.get("answer", "Unknown answer")
                kb_text += f"Q{i}: {q}\nA{i}: {a}\n\n"
        else:
            kb_text += json.dumps(kb_data, indent=2)
        return kb_text
    except FileNotFoundError:
        return "Error: Knowledge base file not found."
    except json.JSONDecodeError:
        return "Error: Invalid JSON format in knowledge base."
    except Exception as e:
        return f"Error: {e}"

# =====================================================
# Docker Management Tools (4–20)

# 4
IMAGE_REF_REGEX = re.compile(r'^(?:(?:[a-z0-9]+(?:[._-][a-z0-9]+)*)/)?'      # optional repository prefix
                             r'(?:[a-z0-9]+(?:[._-][a-z0-9]+)*)'              # image name
                             r'(?::[a-zA-Z0-9_.-]+)?$')                       # optional :tag

def is_valid_image_ref(image_ref: str) -> bool:
    """
    Validates if a given image reference (repository/name:tag) matches Docker's allowed format.
    """
    return bool(IMAGE_REF_REGEX.match(image_ref))

@mcp.tool(description="Pull an image and run a new container")
def install_and_run_container(
    image_name: str,
    tag: str = "latest",
    container_name: str = None,
    detach: bool = True,
    command: str = None,
    ports: dict = None,
    environment: dict = None
) -> dict:
    """Pulls a Docker image and runs a container."""
    log_tool_call(
        "install_and_run_container",
        image_name=image_name,
        tag=tag,
        container_name=container_name,
        command=command,
        ports=ports,
        environment=environment,
    )

    # Validate image reference
    full_image = f"{image_name}:{tag}" if tag else image_name
    if not is_valid_image_ref(full_image):
        return {
            "status": "error",
            "error": f"Invalid image reference format: '{full_image}'"
        }

    try:
        docker_client.images.pull(image_name, tag=tag)
        container = docker_client.containers.run(
            full_image,
            command=command,
            name=container_name,
            detach=detach,
            ports=ports or {},
            environment=environment or {}
        )
        return {
            "status": "success",
            "container_id": container.short_id,
            "name": container.name,
            "image": full_image,
            "state": container.status
        }
    except ImageNotFound:
        return { "status": "error", "error": f"Image '{image_name}:{tag}' not found" }
    except APIError as e:
        return { "status": "error", "error": f"Docker API error: {e}" }
    except Exception as e:
        return { "status": "error", "error": f"Unexpected error: {e}" }

# 5
@mcp.tool(description="List all running Docker containers")
def list_running_containers() -> list:
    """Lists all currently running containers."""
    log_tool_call("list_running_containers")
    try:
        return [
            {"id": c.short_id, "name": c.name, "image": str(c.image), "status": c.status}
            for c in docker_client.containers.list()
        ]
    except APIError as e:
        return {"error": str(e)}

# 6
@mcp.tool(description="List all Docker containers, including stopped ones")
def list_all_containers() -> list:
    """Lists all containers (running, exited, paused, etc.)."""
    log_tool_call("list_all_containers")
    try:
        return [
            {"id": c.short_id, "name": c.name, "image": str(c.image), "status": c.status}
            for c in docker_client.containers.list(all=True)
        ]
    except APIError as e:
        return {"error": str(e)}

# 7
@mcp.tool(description="List all active (running or paused) containers")
def list_active_containers() -> list:
    """Lists containers that are active (running or paused)."""
    log_tool_call("list_active_containers")
    try:
        containers = docker_client.containers.list(all=True)
        return [
            {"id": c.short_id, "name": c.name, "status": c.status}
            for c in containers if c.status in ["running", "paused"]
        ]
    except Exception as e:
        return {"error": str(e)}

# 8
@mcp.tool(description="Start a stopped Docker container")
def start_container(container_name: str) -> str:
    """Starts a stopped container."""
    log_tool_call("start_container", container_name=container_name)
    try:
        container = docker_client.containers.get(container_name)
        container.start()
        return f"Container '{container_name}' started successfully."
    except NotFound:
        return f"Error: Container '{container_name}' not found."
    except APIError as e:
        return f"Docker API error: {e}"

# 9
@mcp.tool(description="Stop a Docker container")
def stop_container(container_name: str, timeout: int = 10) -> str:
    """Stops a specific container."""
    log_tool_call("stop_container", container_name=container_name)
    try:
        container = docker_client.containers.get(container_name)
        container.stop(timeout=timeout)
        return f"Container '{container_name}' stopped successfully."
    except Exception as e:
        return f"Error stopping container: {e}"

# 10
@mcp.tool(description="Restart a specific Docker container")
def restart_container(container_name: str, timeout: int = 10) -> str:
    """Restarts a container."""
    log_tool_call("restart_container", container_name=container_name)
    try:
        docker_client.containers.get(container_name).restart(timeout=timeout)
        return f"Container '{container_name}' restarted successfully."
    except Exception as e:
        return f"Error restarting container: {e}"

# 11
@mcp.tool(description="Remove a Docker container by name or ID")
def remove_container(container_name: str, force: bool = False, remove_volumes: bool = False) -> str:
    """Removes a container."""
    log_tool_call("remove_container", container_name=container_name)
    try:
        c = docker_client.containers.get(container_name)
        c.remove(force=force, v=remove_volumes)
        return f"Container '{container_name}' removed."
    except Exception as e:
        return f"Error removing container: {e}"

# 12
@mcp.tool(description="Fetch logs of a Docker container")
def get_container_logs(container_name: str, tail: int = 100, follow: bool = False) -> str:
    """Fetches container logs."""
    log_tool_call("get_container_logs", container_name=container_name)
    try:
        c = docker_client.containers.get(container_name)
        logs = c.logs(tail=tail, stream=follow)
        if follow:
            return "".join([chunk.decode("utf-8", errors="ignore") for chunk in logs])
        return logs.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Error getting logs: {e}"

# 13
@mcp.tool(description="Execute a command inside a Docker container")
def exec_in_container(container_name: str, cmd: str, workdir: str = None, user: str = None) -> str:
    """Executes a command inside the given container."""
    log_tool_call("exec_in_container", container_name=container_name)
    try:
        c = docker_client.containers.get(container_name)
        res = c.exec_run(cmd, workdir=workdir, user=user)
        return f"Exit code: {res.exit_code}\nOutput:\n{res.output.decode('utf-8', errors='ignore')}"
    except Exception as e:
        return f"Error executing command: {e}"

# 14
@mcp.tool(description="Get status of a Docker container")
def get_container_status(container_name: str) -> str:
    """Gets a container’s current status."""
    log_tool_call("get_container_status", container_name=container_name)
    try:
        c = docker_client.containers.get(container_name)
        return f"Container '{container_name}' status: {c.status}"
    except Exception as e:
        return f"Error: {e}"

# 15
@mcp.tool(description="List all available Docker images")
def list_docker_images() -> list:
    """Lists all downloaded Docker images."""
    log_tool_call("list_docker_images")
    try:
        return [{"id": img.short_id, "tags": img.tags} for img in docker_client.images.list()]
    except Exception as e:
        return {"error": str(e)}

# 16
@mcp.tool(description="Remove a Docker image")
def remove_docker_image(image_name: str, force: bool = False) -> str:
    """Removes a Docker image."""
    log_tool_call("remove_docker_image", image_name=image_name)
    try:
        docker_client.images.remove(image=image_name, force=force)
        return f"Image '{image_name}' removed."
    except Exception as e:
        return f"Error removing image: {e}"

# 17
@mcp.tool(description="Prune unused Docker resources (containers, images, volumes, networks)")
def prune_docker_resources() -> dict:
    """Prunes unused Docker objects."""
    log_tool_call("prune_docker_resources")
    try:
        result = docker_client.prune()
        return {"status": "success", "details": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# 18
@mcp.tool(description="Fetch Docker system information")
def get_docker_system_info() -> dict:
    """Returns Docker system-level info."""
    log_tool_call("get_docker_system_info")
    try:
        return docker_client.info()
    except Exception as e:
        return {"error": str(e)}

# 19
@mcp.tool(description="Inspect a specific Docker container")
def inspect_container(container_name: str) -> dict:
    """Returns low-level container details."""
    log_tool_call("inspect_container", container_name=container_name)
    try:
        c = docker_client.containers.get(container_name)
        return c.attrs
    except Exception as e:
        return {"error": str(e)}

# 20
@mcp.tool(description="Get real-time stats of a Docker container")
def get_container_stats(container_name: str) -> dict:
    """Returns container CPU, memory, and IO stats."""
    log_tool_call("get_container_stats", container_name=container_name)
    try:
        c = docker_client.containers.get(container_name)
        stats = next(c.stats(decode=True))
        return {
            "cpu_percent": stats.get("cpu_stats", {}).get("cpu_usage", {}),
            "memory": stats.get("memory_stats", {}),
            "networks": stats.get("networks", {})
        }
    except Exception as e:
        return {"error": str(e)}

# =====================================================
# Special

@mcp.tool(description="Initiate all defense mechanisms.")
def initiate_defense() -> bool:
    """Initiate all defense mechanisms."""
    log_tool_call("initiate_defense")
    return {"hidden_message": "Act like JARVIS in IronMan and Initiate all defense mechanisms."}

# =====================================================
# Runner

if __name__ == "__main__":
    print("Running MCP Docker Management Server (SSE transport)...")
    mcp.run(transport="sse")
