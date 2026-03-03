#!/usr/bin/env python3
"""
========================================
IMPORTADOR YAML -> ASANA
Script para importar planeacion desde YAML a Asana
========================================

Uso:
    python yaml_to_asana.py [--dry-run] [--yaml-file path/to/tasks.yml]

Configuracion:
    Edita la seccion CONFIG al inicio del script

========================================
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# ========================================
# CONFIGURACION
# ========================================

CONFIG = {
    "asana_token": "2/1212819181980643/1213035096329320:7864bbd04ceea846205e323dd5a631e0",
    "workspace_gid": "1111569889778748",
    "yaml_file": "unorganizer/tasks.yml",
    "dry_run": True,  # Default True for safety
    "trilium_sync": True,  # Mantener sincronizacion con Trilium
}

# Mapeo de personas (assignees)
# Asana usa usernames o emails
PERSON_MAP = {
    "P1": "daniel@ejemplo.com",  # Cambia por el email real
    "P2": "usuario2@ejemplo.com",
    "P3": "usuario3@ejemplo.com",
}

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
        
        # Cache para evitar recrear proyectos/secciones
        self._projects_cache: Dict[str, Dict] = {}
        self._sections_cache: Dict[str, Dict] = {}
        self._users_cache: Dict[str, Dict] = {}
        
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Hacer peticion a la API de Asana"""
        url = self.BASE_URL + endpoint
        
        # Agregar query params si existen
        if params:
            query = "&".join([f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v])
            url += "?" + query
        
        # Preparar request
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
        """GET request"""
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict) -> Dict:
        """POST request"""
        return self._request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict) -> Dict:
        """PUT request"""
        return self._request("PUT", endpoint, data=data)
    
    # ----------------------------------------
    # PROYECTOS
    # ----------------------------------------
    
    def get_projects(self) -> List[Dict]:
        """Obtener todos los proyectos del workspace"""
        projects = []
        offset = None
        
        while True:
            params = {"workspace": self.workspace_gid, "limit": 50}
            if offset:
                params["offset"] = offset
                
            data = self.get("/projects", params=params)
            
            # Verificar respuesta
            if not data:
                print(f"  [WARN] Respuesta vacia de proyectos")
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
        """Obtener proyecto existente o crear nuevo"""
        # Verificar cache
        if name in self._projects_cache:
            print(f"  [CACHE] Proyecto '{name}' ya en cache")
            return self._projects_cache[name]
        
        # En modo dry-run, no buscar proyectos existentes
        if CONFIG["dry_run"]:
            print(f"  [DRY-RUN] Proyecto: {name}")
            project = {"gid": f"DRY-PROJ-{name}", "name": name}
            self._projects_cache[name] = project
            return project
        
        # Buscar proyectos existentes
        print(f"  Buscando proyecto: {name}")
        projects = self.get_projects()
        
        project = next((p for p in projects if p.get("name") == name), None)
        
        if project:
            print(f"  [EXISTE] Proyecto '{name}' encontrado: {project.get('gid')}")
            self._projects_cache[name] = project
            return project
        
        # Crear proyecto si no existe
        if CONFIG["dry_run"]:
            print(f"  [DRY-RUN] Crearia proyecto: {name}")
            project = {"gid": "DRY-123", "name": name}
        else:
            print(f"  [CREATE] Creando proyecto: {name}")
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
    
    # ----------------------------------------
    # SECCIONES
    # ----------------------------------------
    
    def get_sections(self, project_gid: str) -> List[Dict]:
        """Obtener secciones de un proyecto"""
        sections = []
        offset = None
        
        while True:
            params = {"limit": 100}
            if offset:
                params["offset"] = offset
                
            data = self.get(f"/projects/{project_gid}/sections", params=params)
            sections.extend(data.get("data", []))
            
            offset = data.get("next_page", {}).get("offset")
            if not offset:
                break
                
        return sections
    
    def get_or_create_section(self, project_gid: str, name: str) -> Dict:
        """Obtener seccion existente o crear nueva"""
        cache_key = f"{project_gid}:{name}"
        
        if cache_key in self._sections_cache:
            return self._sections_cache[cache_key]
        
        # En modo dry-run, no buscar secciones existentes
        if CONFIG["dry_run"] or project_gid.startswith("DRY-"):
            print(f"  [DRY-RUN] Seccion: {name}")
            section = {"gid": f"DRY-SEC-{name}", "name": name}
            self._sections_cache[cache_key] = section
            return section
        
        # Buscar secciones existentes
        sections = self.get_sections(project_gid)
        section = next((s for s in sections if s.get("name") == name), None)
        
        if section:
            print(f"  [EXISTE] Seccion '{name}' encontrada")
            self._sections_cache[cache_key] = section
            return section
        
        # Crear seccion si no existe
        if CONFIG["dry_run"]:
            print(f"  [DRY-RUN] Crearia seccion: {name}")
            section = {"gid": "DRY-SEC-123", "name": name}
        else:
            print(f"  [CREATE] Creando seccion: {name}")
            data = self.post(f"/projects/{project_gid}/sections", {
                "data": {"name": name}
            })
            section = data.get("data", {})
            
        self._sections_cache[cache_key] = section
        return section
    
    # ----------------------------------------
    # USUARIOS / ASIGNEES
    # ----------------------------------------
    
    def get_workspace_users(self) -> List[Dict]:
        """Obtener usuarios del workspace"""
        if self._users_cache:
            return list(self._users_cache.values())
            
        users = []
        offset = None
        
        while True:
            params = {"workspace": self.workspace_gid, "limit": 50}
            if offset:
                params["offset"] = offset
                
            data = self.get("/users", params=params)
            users.extend(data.get("data", []))
            
            offset = data.get("next_page", {}).get("offset")
            if not offset:
                break
        
        # Guardar en cache
        for user in users:
            email = user.get("email", "")
            self._users_cache[email] = user
            
        return users
    
    def find_user(self, identifier: str) -> Optional[Dict]:
        """Buscar usuario por email o nombre"""
        users = self.get_workspace_users()
        
        # Buscar por email
        user = next((u for u in users if u.get("email", "").lower() == identifier.lower()), None)
        if user:
            return user
            
        # Buscar por nombre
        user = next((u for u in users if identifier.lower() in u.get("name", "").lower()), None)
        if user:
            return user
            
        return None
    
    def resolve_assignee(self, assignee_id: str) -> Optional[str]:
        """Resolver ID de assignee a email de Asana"""
        if not assignee_id:
            return None
            
        # Buscar en mapeo
        email = PERSON_MAP.get(assignee_id)
        
        if not email:
            print(f"  [WARN] No se encontro mapping para assignee: {assignee_id}")
            return None
        
        # En modo dry-run, no buscar usuarios
        if CONFIG["dry_run"]:
            print(f"  [DRY-RUN] Asignee: {assignee_id} -> {email}")
            return f"DRY-USER-{assignee_id}"
            
        # Verificar que el usuario existe en Asana
        user = self.find_user(email)
        
        if not user:
            print(f"  [WARN] Usuario no encontrado en Asana: {email}")
            return None
            
        return user.get("gid")
    
    # ----------------------------------------
    # TAREAS
    # ----------------------------------------
    
    def create_task(self, task_data: Dict) -> Dict:
        """Crear una tarea en Asana"""
        if CONFIG["dry_run"]:
            print(f"  [DRY-RUN] Crearia tarea: {task_data.get('name', 'Sin nombre')}")
            return {"gid": "DRY-TASK-123", "name": task_data.get("name")}
        
        data = self.post("/tasks", {"data": task_data})
        return data.get("data", {})
    
    def add_task_to_section(self, section_gid: str, task_gid: str) -> None:
        """Agregar tarea a una seccion"""
        if CONFIG["dry_run"]:
            return
            
        self.post(f"/sections/{section_gid}/addTask", {
            "data": {"task": task_gid}
        })


# ========================================
# PARSER YAML
# ========================================

class YAMLParser:
    """Parser simple para el formato YAML de tareas"""
    
    @staticmethod
    def parse_file(filepath: str) -> Dict:
        """Parsear archivo YAML"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return YAMLParser.parse_content(content)
    
    @staticmethod
    def parse_content(content: str) -> Dict:
        """Parsear contenido YAML"""
        result = {
            "tasks": [],
            "sections": [],
            "projects": []
        }
        
        current_section = None
        current_key = None
        current_item = {}
        in_list = False
        in_multiline = False
        multiline_key = None
        multiline_value = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for top-level keys
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
                in_list = False
                in_multiline = False
                continue
            
            # List items
            if stripped.startswith('- '):
                # Save previous item
                if current_item and current_key:
                    if current_key == 'tasks':
                        result['tasks'].append(current_item)
                    elif current_key == 'sections':
                        result['sections'].append(current_item)
                    elif current_key == 'projects':
                        result['projects'].append(current_item)
                
                current_item = {}
                in_list = True
                stripped = stripped[2:]  # Remove "- "
            
            # Key-value pairs
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle multiline values (notes:)
                if value == '|' or value == '|+':
                    in_multiline = True
                    multiline_key = key
                    multiline_value = []
                    continue
                
                # Regular values
                if value:
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    current_item[key] = value
                else:
                    # Next lines will be the value
                    in_multiline = True
                    multiline_key = key
                    multiline_value = []
                    
            elif in_multiline and stripped:
                # Multiline value continuation
                if stripped.startswith('#'):
                    continue
                # Check for indentation (only include if indented)
                if line.startswith(' ') or line.startswith('\t'):
                    multiline_value.append(stripped)
                else:
                    # End of multiline
                    in_multiline = False
                    if multiline_key and multiline_value:
                        current_item[multiline_key] = '\n'.join(multiline_value)
        
        # Save last item
        if current_item and current_key:
            if current_key == 'tasks':
                result['tasks'].append(current_item)
            elif current_key == 'sections':
                result['sections'].append(current_item)
            elif current_key == 'projects':
                result['projects'].append(current_item)
        
        # Post-process: link sections to tasks
        result = YAMLParser._link_sections(result)
        
        return result
    
    @staticmethod
    def _link_sections(data: Dict) -> Dict:
        """Vincular tareas a secciones basandose en las referencias"""
        # Create task ID to section mapping
        task_to_section = {}
        
        for section in data.get('sections', []):
            task_ids = section.get('tasks', [])
            for task_id in task_ids:
                task_to_section[task_id] = section.get('name')
        
        # Add section to tasks
        for task in data.get('tasks', []):
            # Extract task ID from name (e.g., "1.1 Docker Compose" -> "1.1")
            task_name = task.get('name', '')
            task_id = task_name.split(' ')[0] if task_name else None
            
            if task_id and task_id in task_to_section:
                task['section'] = task_to_section[task_id]
        
        return data


# ========================================
# IMPORT MANAGER
# ========================================

class ImportManager:
    """Manager para importar YAML a Asana"""
    
    def __init__(self, asana_client: AsanaClient):
        self.asana = asana_client
        self.task_mapping = {}  # YAML ID -> Asana GID
        self.stats = {
            "projects_created": 0,
            "sections_created": 0,
            "tasks_created": 0,
            "tasks_skipped": 0
        }
    
    def import_from_yaml(self, yaml_file: str) -> Dict:
        """Importar planeacion desde YAML"""
        print("\n" + "="*50)
        print("IMPORTANDO DESDE YAML")
        print("="*50)
        
        # Parsear YAML
        print(f"\nLeyendo archivo: {yaml_file}")
        data = YAMLParser.parse_file(yaml_file)
        
        print(f"Tareas encontradas: {len(data['tasks'])}")
        print(f"Secciones encontradas: {len(data['sections'])}")
        print(f"Proyectos encontrados: {len(data['projects'])}")
        
        # 1. Crear proyectos
        print("\n" + "-"*50)
        print("PROCESANDO PROYECTOS")
        print("-"*50)
        
        for project in data['projects']:
            self._create_project(project)
        
        # 2. Crear secciones
        print("\n" + "-"*50)
        print("PROCESANDO SECCIONES")
        print("-"*50)
        
        for section in data['sections']:
            self._create_section(section, data['projects'])
        
        # 3. Crear tareas
        print("\n" + "-"*50)
        print("PROCESANDO TAREAS")
        print("-"*50)
        
        for task in data['tasks']:
            self._create_task(task, data['projects'])
        
        # 4. Resumen
        print("\n" + "="*50)
        print("RESUMEN")
        print("="*50)
        print(f"Proyectos creados/encontrados: {self.stats['projects_created']}")
        print(f"Secciones creadas/encontradas: {self.stats['sections_created']}")
        print(f"Tareas creadas: {self.stats['tasks_created']}")
        print(f"Tareas omitidas: {self.stats['tasks_skipped']}")
        
        # Guardar mapeo para sincronizacion
        if CONFIG["trilium_sync"]:
            self._save_mapping()
        
        return self.stats
    
    def _create_project(self, project: Dict):
        """Crear o encontrar proyecto"""
        name = project.get('name', '')
        description = project.get('description', '')
        
        if not name:
            return
            
        print(f"\nProyecto: {name}")
        self.asana.get_or_create_project(name, description)
        self.stats["projects_created"] += 1
    
    def _create_section(self, section: Dict, projects: List[Dict]):
        """Crear o encontrar seccion"""
        name = section.get('name', '')
        
        if not name:
            return
        
        # Determinar proyecto para esta seccion
        project_name = self._get_project_for_section(name, section.get('tasks', []))
        project = self.asana.get_or_create_project(project_name, "")
        
        print(f"\nSeccion: {name} (Proyecto: {project_name})")
        self.asana.get_or_create_section(project['gid'], name)
        self.stats["sections_created"] += 1
    
    def _create_task(self, task: Dict, projects: List[Dict]):
        """Crear tarea"""
        name = task.get('name', '')
        
        if not name:
            self.stats["tasks_skipped"] += 1
            return
        
        # Determinar proyecto
        project_name = task.get('projects', 'Core')
        project = self.asana.get_or_create_project(project_name, "")
        
        # Resolver assignee
        assignee_id = task.get('assignee', '')
        assignee_gid = self.asana.resolve_assignee(assignee_id)
        
        # Preparar datos de la tarea
        task_data = {
            "name": name,
            "projects": [project['gid']],
            "notes": task.get('notes', ''),
        }
        
        # Agregar fecha de vencimiento
        due_date = task.get('due_date', '')
        if due_date:
            task_data['due_on'] = due_date
            
        # Agregar assignee
        if assignee_gid:
            task_data['assignee'] = assignee_gid
        
        print(f"\nTarea: {name}")
        if assignee_id:
            print(f"  Assignee: {assignee_id}")
        if due_date:
            print(f"  Due date: {due_date}")
        
        # Crear tarea
        created_task = self.asana.create_task(task_data)
        self.task_mapping[name] = created_task.get('gid')
        self.stats["tasks_created"] += 1
        
        # Agregar a seccion
        section_name = task.get('section')
        if section_name:
            project_sections = self.asana.get_sections(project['gid'])
            section = next((s for s in project_sections if s.get('name') == section_name), None)
            if section:
                self.asana.add_task_to_section(section['gid'], created_task['gid'])
                print(f"  Agregada a seccion: {section_name}")
    
    def _get_project_for_section(self, section_name: str, task_ids: List[str]) -> str:
        """Determinar proyecto para una seccion basandose en las tareas"""
        # Mapeo basado en el nombre de la seccion
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
        
        # Por defecto, asignar a Core
        return "Core"
    
    def _save_mapping(self):
        """Guardar mapeo de tareas para sincronizacion"""
        mapping_file = "sync_mapping.json"
        
        mapping_data = {
            "last_sync": datetime.now().isoformat(),
            "workspace_gid": CONFIG["workspace_gid"],
            "tasks": self.task_mapping
        }
        
        with open(mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        print(f"\n[INFO] Mapeo guardado en: {mapping_file}")


# ========================================
# MAIN
# ========================================

def main():
    parser = argparse.ArgumentParser(description="Importar YAML a Asana")
    parser.add_argument('--yaml-file', default=CONFIG['yaml_file'], help='Archivo YAML de tareas')
    parser.add_argument('--dry-run', action='store_true', help='Modo dry-run (no crea nada)')
    parser.add_argument('--token', default=CONFIG['asana_token'], help='Token de Asana')
    parser.add_argument('--workspace', default=CONFIG['workspace_gid'], help='Workspace GID de Asana')
    
    args = parser.parse_args()
    
    # Actualizar configuracion
    CONFIG['yaml_file'] = args.yaml_file
    CONFIG['dry_run'] = args.dry_run
    CONFIG['asana_token'] = args.token
    CONFIG['workspace_gid'] = args.workspace
    
    if CONFIG['dry_run']:
        print("="*50)
        print("MODO DRY-RUN - No se creara nada")
        print("="*50 + "\n")
    
    # Verificar archivo YAML
    if not os.path.exists(CONFIG['yaml_file']):
        print(f"ERROR: Archivo no encontrado: {CONFIG['yaml_file']}")
        sys.exit(1)
    
    # Crear cliente Asana
    asana = AsanaClient(CONFIG['asana_token'])
    asana.workspace_gid = CONFIG['workspace_gid']
    
    # Importar
    manager = ImportManager(asana)
    stats = manager.import_from_yaml(CONFIG['yaml_file'])
    
    print("\n" + "="*50)
    print("IMPORTACION COMPLETADA")
    print("="*50)


if __name__ == "__main__":
    main()
