#!/usr/bin/env python3
"""
========================================
INTERFAZ GRAFICA DE CONSOLA - YAML -> ASANA
Con Rich para mostrar estado de sincronizacion
========================================
"""

import sys
import os

# Agregar lib al path para poder importar rich
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(script_dir, "lib")
if os.path.exists(lib_dir):
    sys.path.insert(0, lib_dir)

import urllib.request
import urllib.error
import urllib.parse
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Intentar importar rich, si no esta, usar version simple
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# ========================================
# CONFIGURACION
# ========================================

# Importar modulo de configuracion
import config as config_module

# Cargar configuracion
config_manager = config_module.ConfigManager()
app_config = config_manager.load()

# Variables globales desde configuracion
CONFIG = {
    "asana_token": app_config.asana.token,
    "workspace_gid": app_config.asana.workspace_gid,
    "yaml_file": app_config.defaults.yaml_file,
    "dry_run": app_config.defaults.dry_run,
    "trilium_sync": app_config.defaults.trilium_sync,
}

# Mapeo de personas desde configuracion
PERSON_MAP = app_config.person_map

# ========================================
# DATA CLASSES
# ========================================

class SyncStatus(Enum):
    """Estado de sincronizacion"""
    NEW = "new"
    EXISTS = "exists"
    SYNCED = "synced"
    PENDING = "pending"
    ERROR = "error"

@dataclass
class AsanaProject:
    """Proyecto de Asana"""
    name: str
    gid: str = ""
    description: str = ""
    status: SyncStatus = SyncStatus.NEW
    
@dataclass
class AsanaSection:
    """Seccion de Asana"""
    name: str
    project_gid: str
    gid: str = ""
    status: SyncStatus = SyncStatus.NEW

@dataclass
class AsanaTask:
    """Tarea de Asana"""
    name: str
    gid: str = ""
    notes: str = ""
    due_date: str = ""
    assignee: str = ""
    project: str = "Core"
    section: str = ""
    status: SyncStatus = SyncStatus.NEW
    assignee_gid: str = ""
    raw_data: Dict = field(default_factory=dict)
    
    @property
    def task_id(self) -> str:
        """Extraer ID de la tarea del nombre"""
        return self.name.split(' ')[0] if self.name else ""

@dataclass
class SyncState:
    """Estado de sincronizacion completo"""
    projects: List[AsanaProject] = field(default_factory=list)
    sections: List[AsanaSection] = field(default_factory=list)
    tasks: List[AsanaTask] = field(default_factory=list)
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
# CLASE: ASANA CLIENT
# ========================================

class AsanaClient:
    """Cliente para interactuar con la API de Asana"""
    
    BASE_URL = "https://app.asana.com/api/1.0"
    
    def __init__(self, token: str, workspace_gid: str = ""):
        self.token = token
        self.workspace_gid = workspace_gid
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Cache
        self._projects_cache: Dict[str, Dict] = {}
        self._sections_cache: Dict[str, Dict] = {}
        self._users_cache: Dict[str, Dict] = {}
        
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Hacer peticion a la API de Asana"""
        url = self.BASE_URL + endpoint
        
        if params:
            query = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v])
            url += "?" + query
        
        request_data = None
        if data:
            request_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=request_data, headers=self.headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            raise Exception(f"Asana API Error {e.code}: {error_body}")
    
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        return self._request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        return self._request("PUT", endpoint, data=data)
    
    def get_projects(self) -> List[Dict]:
        projects = []
        offset = None
        
        while True:
            params = {"workspace": self.workspace_gid, "limit": 50}
            if offset:
                params["offset"] = offset
                
            data = self.get("/projects", params=params)
            
            if not data:
                break
                
            projects_data = data.get("data")
            if projects_data:
                projects.extend(projects_data)
            
            next_page = data.get("next_page")
            if not next_page:
                break
            offset = next_page.get("offset")
            if not offset:
                break
                
        return projects
    
    def get_or_create_project(self, name: str, description: str = "") -> Dict:
        if name in self._projects_cache:
            return self._projects_cache[name]
        
        if CONFIG["dry_run"]:
            project = {"gid": f"DRY-PROJ-{name}", "name": name}
            self._projects_cache[name] = project
            return project
        
        print(f"  Buscando proyecto: {name}")
        projects = self.get_projects()
        
        project = next((p for p in projects if p.get("name") == name), None)
        
        if project:
            self._projects_cache[name] = project
            return project
        
        data = self.post("/projects", {
            "data": {
                "name": name,
                "workspace": self.workspace_gid,
                "notes": description
            }
        })
        project = data.get("data", {})
        self._projects_cache[name] = project
        return project
    
    def get_sections(self, project_gid: str) -> List[Dict]:
        sections = []
        offset = None
        
        while True:
            params = {"limit": 100}
            if offset:
                params["offset"] = offset
                
            data = self.get(f"/projects/{project_gid}/sections", params=params)
            sections_data = data.get("data")
            if sections_data:
                sections.extend(sections_data)
            
            next_page = data.get("next_page")
            if not next_page:
                break
            offset = next_page.get("offset")
            if not offset:
                break
                
        return sections
    
    def get_or_create_section(self, project_gid: str, name: str) -> Dict:
        cache_key = f"{project_gid}:{name}"
        
        if cache_key in self._sections_cache:
            return self._sections_cache[cache_key]
        
        if CONFIG["dry_run"] or project_gid.startswith("DRY-"):
            section = {"gid": f"DRY-SEC-{name}", "name": name}
            self._sections_cache[cache_key] = section
            return section
        
        sections = self.get_sections(project_gid)
        section = next((s for s in sections if s.get("name") == name), None)
        
        if section:
            self._sections_cache[cache_key] = section
            return section
        
        data = self.post(f"/projects/{project_gid}/sections", {
            "data": {"name": name}
        })
        section = data.get("data", {})
        self._sections_cache[cache_key] = section
        return section
    
    def get_workspace_users(self) -> List[Dict]:
        if self._users_cache:
            return list(self._users_cache.values())
            
        users = []
        offset = None
        
        while True:
            params = {"workspace": self.workspace_gid, "limit": 50}
            if offset:
                params["offset"] = offset
                
            data = self.get("/users", params=params)
            users_data = data.get("data")
            if users_data:
                users.extend(users_data)
            
            next_page = data.get("next_page")
            if not next_page:
                break
            offset = next_page.get("offset")
            if not offset:
                break
        
        for user in users:
            email = user.get("email", "")
            self._users_cache[email] = user
            
        return users
    
    def find_user(self, identifier: str) -> Optional[Dict]:
        users = self.get_workspace_users()
        
        user = next((u for u in users if u.get("email", "").lower() == identifier.lower()), None)
        if user:
            return user
            
        user = next((u for u in users if identifier.lower() in u.get("name", "").lower()), None)
        if user:
            return user
            
        return None
    
    def resolve_assignee(self, assignee_id: str) -> Optional[str]:
        if not assignee_id:
            return None
            
        email = PERSON_MAP.get(assignee_id)
        
        if not email:
            return None
        
        if CONFIG["dry_run"]:
            return f"DRY-USER-{assignee_id}"
        
        user = self.find_user(email)
        
        if not user:
            return None
            
        return user.get("gid")
    
    def check_project_exists(self, name: str) -> bool:
        """Verificar si un proyecto existe"""
        if CONFIG["dry_run"]:
            return False
        
        projects = self.get_projects()
        return any(p.get("name") == name for p in projects)
    
    def check_section_exists(self, project_gid: str, name: str) -> bool:
        """Verificar si una seccion existe"""
        if CONFIG["dry_run"] or project_gid.startswith("DRY-"):
            return False
        
        sections = self.get_sections(project_gid)
        return any(s.get("name") == name for s in sections)

# ========================================
# PARSER YAML
# ========================================

class YAMLParser:
    """Parser simple para el formato YAML de tareas"""
    
    @staticmethod
    def parse_file(filepath: str) -> Dict:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return YAMLParser.parse_content(content)
    
    @staticmethod
    def parse_content(content: str) -> Dict:
        result = {
            "tasks": [],
            "sections": [],
            "projects": []
        }
        
        current_key = None
        current_item = {}
        multiline_key = None
        multiline_value = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                continue
            
            if stripped.endswith(':') and not stripped.startswith('-'):
                if current_key and current_item:
                    if current_key == 'tasks':
                        result['tasks'].append(current_item)
                    elif current_key == 'sections':
                        result['sections'].append(current_item)
                    elif current_key == 'projects':
                        result['projects'].append(current_item)
                    current_item = {}
                
                current_key = stripped.rstrip(':')
                multiline_key = None
                continue
            
            if stripped.startswith('- '):
                if current_item and current_key:
                    if current_key == 'tasks':
                        result['tasks'].append(current_item)
                    elif current_key == 'sections':
                        result['sections'].append(current_item)
                    elif current_key == 'projects':
                        result['projects'].append(current_item)
                
                current_item = {}
                stripped = stripped[2:]
            
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value == '|' or value == '|+':
                    multiline_key = key
                    multiline_value = []
                    continue
                
                if value:
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    current_item[key] = value
                else:
                    multiline_key = key
                    multiline_value = []
                    
            elif multiline_key and stripped:
                if line.startswith(' ') or line.startswith('\t'):
                    multiline_value.append(stripped)
                else:
                    if multiline_key and multiline_value:
                        current_item[multiline_key] = '\n'.join(multiline_value)
                    multiline_key = None
        
        if current_item and current_key:
            if current_key == 'tasks':
                result['tasks'].append(current_item)
            elif current_key == 'sections':
                result['sections'].append(current_item)
            elif current_key == 'projects':
                result['projects'].append(current_item)
        
        return YAMLParser._link_sections(result)
    
    @staticmethod
    def _link_sections(data: Dict) -> Dict:
        task_to_section = {}
        
        for section in data.get('sections', []):
            task_ids = section.get('tasks', [])
            for task_id in task_ids:
                task_to_section[task_id] = section.get('name')
        
        for task in data.get('tasks', []):
            task_name = task.get('name', '')
            task_id = task_name.split(' ')[0] if task_name else None
            
            if task_id and task_id in task_to_section:
                task['section'] = task_to_section[task_id]
        
        return data

# ========================================
# ANALYZER - Analiza el estado
# ========================================

class SyncAnalyzer:
    """Analiza el estado de sincronizacion sin hacer cambios"""
    
    def __init__(self, asana_client: AsanaClient):
        self.asana = asana_client
        self.state = SyncState()
        
    def analyze(self, yaml_file: str) -> SyncState:
        """Analizar el archivo YAML y comparar con Asana"""
        
        # Parsear YAML
        data = YAMLParser.parse_file(yaml_file)
        
        # Analizar proyectos
        for project in data['projects']:
            name = project.get('name', '')
            if not name:
                continue
                
            exists = self.asana.check_project_exists(name)
            p = AsanaProject(
                gid="",
                name=name,
                description=project.get('description', ''),
                status=SyncStatus.EXISTS if exists else SyncStatus.NEW
            )
            
            if not exists:
                self.state.warnings.append(f"Proyecto '{name}' sera creado")
            else:
                self.state.warnings.append(f"Proyecto '{name}' ya existe")
                
            self.state.projects.append(p)
        
        # Analizar secciones
        for section in data['sections']:
            name = section.get('name', '')
            if not name:
                continue
            
            project_name = self._get_project_for_section(name, section.get('tasks', []))
            project = self.asana.get_or_create_project(project_name, "")
            
            exists = self.asana.check_section_exists(project['gid'], name)
            s = AsanaSection(
                gid="",
                name=name,
                project_gid=project['gid'],
                status=SyncStatus.EXISTS if exists else SyncStatus.NEW
            )
            
            self.state.sections.append(s)
        
        # Analizar tareas
        for task in data['tasks']:
            name = task.get('name', '')
            if not name:
                continue
            
            assignee_id = task.get('assignee', '')
            assignee_gid = self.asana.resolve_assignee(assignee_id) if assignee_id else ""
            
            t = AsanaTask(
                name=name,
                notes=task.get('notes', ''),
                due_date=task.get('due_date', ''),
                assignee=assignee_id,
                project=task.get('projects', 'Core'),
                section=task.get('section', ''),
                assignee_gid=assignee_gid or "",
                status=SyncStatus.NEW,
                raw_data=task
            )
            
            self.state.tasks.append(t)
        
        return self.state
    
    def _get_project_for_section(self, section_name: str, task_ids: List[str]) -> str:
        if "Infraestructura" in section_name:
            return "Infraestructura"
        if "Core" in section_name:
            return "Core"
        if "Utilidades" in section_name:
            return "Utilidades"
        if "Observabilidad" in section_name:
            return "Observabilidad"
        if "QA" in section_name:
            return "QA"
        if "Diferido" in section_name:
            return "Diferido"
        return "Core"

# ========================================
# UI - Interfaz con Rich
# ========================================

class RichUI:
    """Interfaz de usuario con Rich"""
    
    @staticmethod
    def print_header():
        """Imprimir header"""
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[bold cyan]YAML -> ASANA[/bold cyan] | [yellow]Importador de Planeacion[/yellow]",
                border_style="cyan",
                box=box.DOUBLE
            ))
        else:
            print("=" * 60)
            print("YAML -> ASANA | Importador de Planeacion")
            print("=" * 60)
    
    @staticmethod
    def print_summary(state: SyncState):
        """Imprimir resumen"""
        if not RICH_AVAILABLE:
            print("\n" + "=" * 60)
            print("RESUMEN")
            print("=" * 60)
            print(f"Proyectos: {len(state.projects)}")
            print(f"Secciones: {len(state.sections)}")
            print(f"Tareas: {len(state.tasks)}")
            return
        
        # Tabla de resumen
        table = Table(title="Resumen de Sincronizacion", box=box.ROUNDED)
        table.add_column("Elemento", style="cyan", justify="left")
        table.add_column("Total", style="magenta", justify="center")
        table.add_column("Nuevos", style="green", justify="center")
        table.add_column("Existentes", style="yellow", justify="center")
        
        new_projects = sum(1 for p in state.projects if p.status == SyncStatus.NEW)
        exists_projects = sum(1 for p in state.projects if p.status == SyncStatus.EXISTS)
        
        new_sections = sum(1 for s in state.sections if s.status == SyncStatus.NEW)
        exists_sections = sum(1 for s in state.sections if s.status == SyncStatus.EXISTS)
        
        table.add_row(
            "Proyectos",
            str(len(state.projects)),
            str(new_projects),
            str(exists_projects)
        )
        table.add_row(
            "Secciones",
            str(len(state.sections)),
            str(new_sections),
            str(exists_sections)
        )
        table.add_row(
            "Tareas",
            str(len(state.tasks)),
            str(len(state.tasks)),
            "0"
        )
        
        console.print(table)
    
    @staticmethod
    def print_projects(state: SyncState):
        """Imprimir tabla de proyectos"""
        if not RICH_AVAILABLE:
            print("\n--- PROYECTOS ---")
            for p in state.projects:
                status = "[NUEVO]" if p.status == SyncStatus.NEW else "[EXISTE]"
                print(f"  {status} {p.name}")
            return
        
        table = Table(title="Proyectos", box=box.SIMPLE)
        table.add_column("Estado", style="cyan", width=10)
        table.add_column("Proyecto", style="white")
        table.add_column("Descripcion", style="dim")
        
        for p in state.projects:
            if p.status == SyncStatus.NEW:
                status = "[green]NUEVO[/green]"
            else:
                status = "[yellow]EXISTE[/yellow]"
            
            table.add_row(status, p.name, p.description[:50])
        
        console.print(table)
    
    @staticmethod
    def print_tasks(state: SyncState):
        """Imprimir tabla de tareas"""
        if not RICH_AVAILABLE:
            print("\n--- TAREAS ---")
            for t in state.tasks:
                due = f" [due: {t.due_date}]" if t.due_date else ""
                assignee = f" [@{t.assignee}]" if t.assignee else ""
                print(f"  - {t.name}{due}{assignee}")
            return
        
        table = Table(title="Tareas a Importar", box=box.SIMPLE)
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Tarea", style="white")
        table.add_column("Proyecto", style="blue", width=15)
        table.add_column("Asignado", style="magenta", width=10)
        table.add_column("Fecha Limite", style="yellow", width=12)
        
        for t in state.tasks:
            table.add_row(
                t.task_id,
                t.name[:40],
                t.project[:15],
                t.assignee or "-",
                t.due_date or "-"
            )
        
        console.print(table)
    
    @staticmethod
    def print_warnings(state: SyncState):
        """Imprimir advertencias"""
        if not state.warnings:
            return
        
        if not RICH_AVAILABLE:
            print("\n--- ADVERTENCIAS ---")
            for w in state.warnings:
                print(f"  ! {w}")
            return
        
        console.print("\n[bold yellow]Advertencias:[/bold yellow]")
        for w in state.warnings:
            console.print(f"  [yellow]![/yellow] {w}")
    
    @staticmethod
    def print_progress(message: str):
        """Imprimir progreso"""
        if RICH_AVAILABLE:
            console.print(f"[cyan]{message}[/cyan]")
        else:
            print(f"> {message}")
    
    @staticmethod
    def print_success(message: str):
        """Imprimir exito"""
        if RICH_AVAILABLE:
            console.print(f"[green]✓ {message}[/green]")
        else:
            print(f"✓ {message}")
    
    @staticmethod
    def print_error(message: str):
        """Imprimir error"""
        if RICH_AVAILABLE:
            console.print(f"[red]✗ {message}[/red]")
        else:
            print(f"✗ {message}")

# ========================================
# MAIN
# ========================================

def main():
    parser = argparse.ArgumentParser(description="Importar YAML a Asana - Analizador de Estado")
    parser.add_argument('--yaml-file', default=CONFIG['yaml_file'], help='Archivo YAML de tareas')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Modo dry-run')
    parser.add_argument('--execute', action='store_true', help='Ejecutar importacion (sin dry-run)')
    parser.add_argument('--token', default=CONFIG['asana_token'], help='Token de Asana')
    parser.add_argument('--workspace', default=CONFIG['workspace_gid'], help='Workspace GID')
    
    args = parser.parse_args()
    
    CONFIG['yaml_file'] = args.yaml_file
    CONFIG['dry_run'] = not args.execute
    CONFIG['asana_token'] = args.token
    CONFIG['workspace_gid'] = args.workspace
    
    # Mostrar header
    RichUI.print_header()
    
    if not CONFIG['dry_run']:
        RichUI.print_error("MODO DE EJECUCION - Se crearan los elementos en Asana!")
    else:
        RichUI.print_progress("MODO ANALISIS - Solo se mostrara el estado\n")
    
    # Verificar archivo
    if not os.path.exists(CONFIG['yaml_file']):
        RichUI.print_error(f"Archivo no encontrado: {CONFIG['yaml_file']}")
        sys.exit(1)
    
    # Crear cliente
    asana = AsanaClient(CONFIG['asana_token'], CONFIG['workspace_gid'])
    
    # Analizar
    RichUI.print_progress("Analizando archivo YAML...")
    analyzer = SyncAnalyzer(asana)
    state = analyzer.analyze(CONFIG['yaml_file'])
    
    # Mostrar resultados
    RichUI.print_summary(state)
    RichUI.print_projects(state)
    RichUI.print_tasks(state)
    RichUI.print_warnings(state)
    
    # Prompt para ejecutar
    if not args.execute:
        if RICH_AVAILABLE:
            console.print("\n[bold]Para ejecutar la importacion, usa:[/bold]")
            console.print(f"  [cyan]python yaml_to_asana_rich.py --yaml-file {CONFIG['yaml_file']} --execute[/cyan]")
        else:
            print("\nPara ejecutar la importacion, usa:")
            print(f"  python yaml_to_asana_rich.py --yaml-file {CONFIG['yaml_file']} --execute")


if __name__ == "__main__":
    main()
