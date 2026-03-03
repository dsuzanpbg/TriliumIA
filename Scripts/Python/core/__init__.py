#!/usr/bin/env python3
"""
========================================
CORE - Nucleo del Framework
Clases base y utilidades comunes
========================================
"""

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Type
from enum import Enum
import urllib.request
import urllib.error
import urllib.parse

# ========================================
# ENUMS
# ========================================

class SyncStatus(Enum):
    """Estado de sincronizacion"""
    NEW = "new"
    EXISTS = "exists"
    SYNCED = "synced"
    PENDING = "pending"
    ERROR = "error"

class TaskStatus(Enum):
    """Estado de una tarea"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class Priority(Enum):
    """Prioridad de tarea"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ========================================
# DATA CLASSES
# ========================================

@dataclass
class Project:
    """Proyecto"""
    name: str
    gid: str = ""
    description: str = ""
    status: SyncStatus = SyncStatus.NEW
    metadata: Dict = field(default_factory=dict)

@dataclass
class Section:
    """Seccion/Columna/Lista"""
    name: str
    project_gid: str
    gid: str = ""
    status: SyncStatus = SyncStatus.NEW

@dataclass
class Task:
    """Tarea"""
    name: str
    gid: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    due_date: str = ""
    assignee: str = ""
    project: str = "Core"
    section: str = ""
    tags: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    sync_status: SyncStatus = SyncStatus.NEW
    raw_data: Dict = field(default_factory=dict)
    subtasks: List[str] = field(default_factory=list)  # Subtareas como lista de nombres

    @property
    def task_id(self) -> str:
        """Extraer ID de la tarea del nombre"""
        return self.name.split(' ')[0] if self.name else ""

@dataclass
class SyncState:
    """Estado de sincronizacion"""
    projects: List[Project] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def total_new(self) -> int:
        return sum(1 for p in self.projects if p.status == SyncStatus.NEW)
    
    @property
    def total_exists(self) -> int:
        return sum(1 for p in self.projects if p.status == SyncStatus.EXISTS)
    
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)

# ========================================
# CONFIG
# ========================================

@dataclass
class AsanaConfig:
    """Configuracion de Asana"""
    token: str = ""
    workspace_gid: str = ""

@dataclass  
class JiraConfig:
    """Configuracion de Jira"""
    domain: str = ""
    email: str = ""
    api_token: str = ""
    project_key: str = ""

@dataclass
class GitHubConfig:
    """Configuracion de GitHub"""
    token: str = ""
    owner: str = ""
    repo: str = ""

@dataclass
class TriliumConfig:
    """Configuracion de Trilium"""
    etapi_token: str = ""
    base_url: str = "http://localhost:3784"
    parent_note_id: str = ""

@dataclass
class DefaultsConfig:
    """Configuracion por defecto"""
    yaml_file: str = "unorganizer/tasks.yml"
    dry_run: bool = True
    trilium_sync: bool = True

@dataclass
class AppConfig:
    """Configuracion completa"""
    asana: AsanaConfig = field(default_factory=AsanaConfig)
    jira: JiraConfig = field(default_factory=JiraConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    trilium: TriliumConfig = field(default_factory=TriliumConfig)
    person_map: Dict[str, str] = field(default_factory=dict)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

# ========================================
# HTTP CLIENT
# ========================================

class HTTPClient:
    """Cliente HTTP base"""
    
    def __init__(self, base_url: str = "", headers: Dict = None):
        self.base_url = base_url
        self.headers = headers or {}
        
    def _build_url(self, endpoint: str, params: Dict = None) -> str:
        url = self.base_url + endpoint
        if params:
            query = "&".join([
                f"{k}={urllib.parse.quote(str(v))}" 
                for k, v in params.items() if v
            ])
            url += "?" + query
        return url
    
    def request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        url = self._build_url(endpoint, params)
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        headers = self.headers.copy()
        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise Exception(f"HTTP {e.code}: {error_body}")
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        return self.request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        return self.request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        return self.request("PUT", endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict:
        return self.request("DELETE", endpoint)

# ========================================
# CONFIG MANAGER
# ========================================

class ConfigManager:
    """Gestor de configuracion"""
    
    DEFAULT_FILE = "config.json"
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self.DEFAULT_FILE
        self.config: AppConfig = AppConfig()
        
    def load(self, config_file: str = None) -> AppConfig:
        filename = config_file or self.config_file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, "..", filename)
        
        if not os.path.exists(filepath):
            filepath = filename
            
        if not os.path.exists(filepath):
            return self.config
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.config = AppConfig(
                asana=AsanaConfig(
                    token=data.get("asana", {}).get("token", ""),
                    workspace_gid=data.get("asana", {}).get("workspace_gid", "")
                ),
                jira=JiraConfig(
                    domain=data.get("jira", {}).get("domain", ""),
                    email=data.get("jira", {}).get("email", ""),
                    api_token=data.get("jira", {}).get("api_token", ""),
                    project_key=data.get("jira", {}).get("project_key", "")
                ),
                github=GitHubConfig(
                    token=data.get("github", {}).get("token", ""),
                    owner=data.get("github", {}).get("owner", ""),
                    repo=data.get("github", {}).get("repo", "")
                ),
                trilium=TriliumConfig(
                    etapi_token=data.get("trilium", {}).get("etapi_token", ""),
                    base_url=data.get("trilium", {}).get("base_url", "http://localhost:3784"),
                    parent_note_id=data.get("trilium", {}).get("parent_note_id", "")
                ),
                person_map=data.get("person_map", {}),
                defaults=DefaultsConfig(
                    yaml_file=data.get("defaults", {}).get("yaml_file", "unorganizer/tasks.yml"),
                    dry_run=data.get("defaults", {}).get("dry_run", True),
                    trilium_sync=data.get("defaults", {}).get("trilium_sync", True)
                )
            )
        except Exception as e:
            print(f"Error cargando config: {e}")
            
        return self.config
    
    def save(self, config_file: str = None) -> bool:
        filename = config_file or self.config_file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, "..", filename)
        
        try:
            data = {
                "asana": asdict(self.config.asana),
                "jira": asdict(self.config.jira),
                "github": asdict(self.config.github),
                "trilium": asdict(self.config.trilium),
                "person_map": self.config.person_map,
                "defaults": asdict(self.config.defaults)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando config: {e}")
            return False

# ========================================
# YAML PARSER
# ========================================

import yaml

class YAMLParser:
    """Parser para YAML de tareas usando PyYAML"""
    
    @staticmethod
    def parse_file(filepath: str) -> Dict:
        with open(filepath, 'r', encoding='utf-8') as f:
            return YAMLParser.parse_content(f.read())
    
    @staticmethod
    def parse_content(content: str) -> Dict:
        data = yaml.safe_load(content)
        
        if not data:
            return {"tasks": [], "sections": [], "project": {}}
        
        result = {
            "tasks": data.get("tasks", []) or [],
            "sections": data.get("sections", []) or [],
            "project": data.get("project", {}) or {}
        }
        
        return YAMLParser._link_sections(result)
    
    @staticmethod
    def _link_sections(data: Dict) -> Dict:
        task_to_section = {}
        
        for section in data.get('sections', []):
            for task_id in section.get('tasks', []):
                task_to_section[task_id] = section.get('name')
        
        for task in data.get('tasks', []):
            task_name = task.get('name', '')
            task_id = task_name.split(' ')[0] if task_name else None
            
            if task_id and task_id in task_to_section:
                task['section'] = task_to_section[task_id]
        
        return data
