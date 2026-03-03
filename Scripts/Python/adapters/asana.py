#!/usr/bin/env python3
"""
=======================================
ADAPTER - Asana (using direct API)
======================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))

import requests
from core import Project, Section, Task, SyncStatus, SyncState
from typing import Dict, List, Optional

# Import plugin de conversion markdown
try:
    from plugins.markdown_converter import convert_to_asana
except ImportError:
    def convert_to_asana(text):
        return text

# ========================================
# ASANA ADAPTER
# ========================================

# Secciones fijas de Agile/Scrum
AGILE_SECTIONS = ["To Do", "In Progress", "Done"]

class AsanaAdapter:
    """Adaptador de Asana usando API REST"""
    
    name = "asana"
    display_name = "Asana"
    BASE_URL = "https://app.asana.com/api/1.0"
    
    def __init__(self, config: Dict, person_map: Dict = None):
        self.person_map = person_map or {}
        self.workspace_gid = config.get("workspace_gid", "")
        self.team_gid = config.get("team_gid", "")
        self.portfolio_gid = config.get("portfolio_gid", "")
        self.scope = config.get("scope", "all")
        self.my_ids = config.get("my_ids", []) or []
        self.token = config.get("token", "")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Cache
        self._projects_cache: Dict[str, Dict] = {}
        self._sections_cache: Dict[str, Dict] = {}
        self._users_cache: Dict[str, str] = {}
    
    def _api_call(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request"""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def _get_project(self, name: str, description: str = "", dry_run: bool = True) -> Dict:
        """Obtener o crear proyecto"""
        if name in self._projects_cache:
            return self._projects_cache[name]
        
        if dry_run or not self.token:
            project = {"gid": f"DRY-PROJ-{name}", "name": name}
            self._projects_cache[name] = project
            return project
        
        # Buscar proyecto existente
        try:
            result = self._api_call('GET', f'/workspaces/{self.workspace_gid}/projects', params={'limit': 100})
            projects = result.get('data', [])
            for p in projects:
                if p['name'] == name:
                    self._projects_cache[name] = p
                    return p
        except Exception as e:
            print(f"Error buscando proyecto: {e}")
        
        # Crear proyecto
        try:
            data = {'name': name, 'workspace': self.workspace_gid}
            if description:
                data['notes'] = description
            result = self._api_call('POST', '/projects', json={'data': data})
            project = result.get('data', {})
            
            # Agregar al portfolio
            if self.portfolio_gid:
                try:
                    self._api_call('POST', f'/portfolios/{self.portfolio_gid}/addProject', 
                                 json={'data': {'project': project.get('gid')}})
                    print(f"Proyecto agregado al portfolio: {self.portfolio_gid}")
                except Exception as e:
                    print(f"Warning: No se pudo agregar al portfolio: {e}")
            
            self._projects_cache[name] = project
            return project
        except Exception as e:
            print(f"Error creando proyecto: {e}")
            return {"gid": "ERROR", "name": name}
    
    def _get_section(self, project_gid: str, name: str, dry_run: bool = True) -> Dict:
        """Obtener o crear seccion"""
        cache_key = f"{project_gid}:{name}"
        
        if cache_key in self._sections_cache:
            return self._sections_cache[cache_key]
        
        if dry_run or not self.token:
            section = {"gid": f"DRY-SEC-{name}", "name": name}
            self._sections_cache[cache_key] = section
            return section
        
        try:
            result = self._api_call('GET', f'/projects/{project_gid}/sections')
            sections = result.get('data', [])
            for s in sections:
                if s['name'] == name:
                    self._sections_cache[cache_key] = s
                    return s
            
            # Crear seccion
            result = self._api_call('POST', f'/projects/{project_gid}/sections', 
                                  json={'data': {'name': name}})
            section = result.get('data', {})
            self._sections_cache[cache_key] = section
            return section
        except Exception as e:
            print(f"Error obteniendo seccion: {e}")
            return {"gid": "ERROR", "name": name}
    
    def _resolve_assignee(self, assignee_id: str, dry_run: bool = True) -> Optional[str]:
        """Resolver assignee a email de Asana"""
        if dry_run or not self.token:
            return assignee_id
        
        # Si es P1, P2, etc, convertir a email
        if assignee_id in self.person_map:
            email = self.person_map[assignee_id]
        elif '@' in assignee_id:
            email = assignee_id
        else:
            return None
        
        # Buscar usuario
        if email in self._users_cache:
            return self._users_cache[email]
        
        try:
            result = self._api_call('GET', f'/workspaces/{self.workspace_gid}/users', params={'limit': 100})
            users = result.get('data', [])
            for u in users:
                if u.get('email', '').lower() == email.lower():
                    self._users_cache[email] = u['gid']
                    return u['gid']
        except Exception:
            pass
        
        return None
    
    # ------------------ public API ------------------
    
    def analyze(self, yaml_file: str, dry_run: bool = True) -> SyncState:
        from core import YAMLParser
        
        state = SyncState()
        data = YAMLParser.parse_file(yaml_file)
        
        project_data = data.get("project", {})
        project_name = project_data.get("name", "PBG Microservices")
        project_desc = project_data.get("description", "")
        
        if project_name:
            state.projects.append(Project(
                name=project_name,
                description=project_desc,
                status=SyncStatus.NEW
            ))
        
        # Usar secciones de Agile/Scrum (To Do, In Progress, Done)
        for section_name in AGILE_SECTIONS:
            state.sections.append(Section(
                name=section_name,
                project_gid=project_name,
                status=SyncStatus.NEW
            ))
        
        for task_data in data.get('tasks', []):
            name = task_data.get('name', '')
            if not name:
                continue
            
            if self.scope == "mine" and self.my_ids:
                if task_data.get('assignee', '') not in self.my_ids:
                    continue
            
            # Obtener subtareas
            subtasks = task_data.get('subtasks', [])
            if isinstance(subtasks, str):
                # Si es string, dividir por líneas
                subtasks = [s.strip() for s in subtasks.split('\n') if s.strip()]
            
            state.tasks.append(Task(
                name=name,
                description=task_data.get('notes', ''),
                due_date=task_data.get('due_date', ''),
                assignee=task_data.get('assignee', ''),
                project=project_name,
                section=task_data.get('section', ''),  # Original del YAML
                sync_status=SyncStatus.NEW,
                raw_data=task_data,
                subtasks=subtasks
            ))
        
        return state
    
    def execute(self, yaml_file: str, dry_run: bool = False) -> SyncState:
        """Ejecutar sincronizacion"""
        from core import YAMLParser
        
        state = SyncState()
        data = YAMLParser.parse_file(yaml_file)
        
        project_data = data.get('project', {})
        project_name = project_data.get('name', 'PBG Microservices')
        project_desc = project_data.get('description', '')
        
        project = self._get_project(project_name, project_desc, dry_run)
        state.projects.append(Project(
            name=project_name,
            gid=project.get('gid', ''),
            status=SyncStatus.SYNCED if not dry_run else SyncStatus.NEW
        ))
        
        # Crear secciones de Agile (To Do, In Progress, Done)
        agile_sections = {}
        for section_name in AGILE_SECTIONS:
            section = self._get_section(project.get('gid', ''), section_name, dry_run)
            agile_sections[section_name] = section.get('gid', '')
            state.sections.append(Section(
                name=section_name,
                project_gid=project.get('gid', ''),
                gid=section.get('gid', ''),
                status=SyncStatus.SYNCED if not dry_run else SyncStatus.NEW
            ))
        
        # Por defecto, las tareas van a "To Do"
        default_section_gid = agile_sections.get("To Do", "")
        
        # Agrupar tareas por SECCIÓN del YAML
        from collections import defaultdict
        tareas_por_seccion = defaultdict(list)
        
        for task_data in data.get('tasks', []):
            name = task_data.get('name', '')
            if not name:
                continue
            
            # Usar la sección del YAML como clave
            seccion = task_data.get('section', 'Sin sección')
            tareas_por_seccion[seccion].append(task_data)
        
        # Crear tareas padre (secciones) y subtareas
        for seccion_nombre, tareas in tareas_por_seccion.items():
            if not tareas:
                continue
            
            # Nombre del padre = nombre de la sección
            nombre_padre = seccion_nombre
            
            # Crear tarea padre (la sección) - sin notas, solo el nombre
            task_body = {
                'name': nombre_padre,
                'notes': '',  # La sección no tiene notas
                'workspace': self.workspace_gid
            }
            
            parent_gid = f"DRY-PADRE-{nombre_padre}"
            if not dry_run and self.token:
                try:
                    result = self._api_call('POST', '/tasks', json={'data': task_body})
                    parent_gid = result.get('data', {}).get('gid', 'ERROR')
                    
                    # Añadir a sección To Do
                    if default_section_gid and parent_gid and parent_gid != 'ERROR':
                        try:
                            self._api_call('POST', f'/sections/{default_section_gid}/addTask', 
                                         json={'data': {'task': parent_gid}})
                        except Exception as sec_err:
                            pass
                except Exception as e:
                    print(f"Error creando tarea padre '{nombre_padre}': {e}")
                    parent_gid = "ERROR"
            
            # Crear subtareas (invertidas para que aparezcan en orden correcto en Asana)
            created_subtasks = []
            tareas_invertidas = list(tareas)[::-1]  # Invertir orden
            
            for subtask_data in tareas_invertidas:
                st_name = subtask_data.get('name', '')
                if not st_name:
                    continue
                
                st_assignee_id = subtask_data.get('assignee', '')
                st_assignee_gid = self._resolve_assignee(st_assignee_id, dry_run)
                st_notes = convert_to_asana(subtask_data.get('notes', ''))
                
                st_gid = f"DRY-SUB-{st_name}"
                
                if not dry_run and self.token:
                    st_body = {
                        'name': st_name,
                        'notes': st_notes,
                        'workspace': self.workspace_gid,
                        'parent': parent_gid
                    }
                    
                    if st_assignee_gid:
                        st_body['assignee'] = st_assignee_gid
                    
                    if subtask_data.get('due_date'):
                        st_body['due_on'] = subtask_data.get('due_date')
                    
                    if parent_gid != 'ERROR':
                        try:
                            result = self._api_call('POST', '/tasks', json={'data': st_body})
                            st_gid = result.get('data', {}).get('gid', 'ERROR')
                            created_subtasks.append(st_gid)
                        except Exception as e:
                            print(f"Error creando subtarea '{st_name}': {e}")
                else:
                    # Dry-run: agregar a la lista
                    created_subtasks.append(st_gid)
                
                # Agregar a state
                state.tasks.append(Task(
                    name=st_name,
                    gid=st_gid,
                    assignee=st_assignee_id,
                    project=project_name,
                    section="To Do",
                    sync_status=SyncStatus.SYNCED if not dry_run else SyncStatus.NEW,
                    raw_data=subtask_data,
                    subtasks=[]
                ))
            
            # Agregar tarea padre a state (la sección)
            state.tasks.append(Task(
                name=nombre_padre,
                gid=parent_gid,
                assignee="",  # La sección no tiene assignee
                project=project_name,
                section="To Do",
                sync_status=SyncStatus.SYNCED if not dry_run else SyncStatus.NEW,
                raw_data={},
                subtasks=created_subtasks
            ))
        
        return state
