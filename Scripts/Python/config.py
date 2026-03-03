#!/usr/bin/env python3
"""
========================================
CONFIG - Modulo de configuracion
Carga y guarda configuracion desde archivos JSON
========================================
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

# ========================================
# CONFIG CLASSES
# ========================================

@dataclass
class AsanaConfig:
    """Configuracion de Asana"""
    token: str = ""
    workspace_gid: str = ""

@dataclass
class DefaultsConfig:
    """Configuracion por defecto"""
    yaml_file: str = "unorganizer/tasks.yml"
    dry_run: bool = True
    trilium_sync: bool = True
    conflict_resolution: str = "latest-wins"
    scope: str = "all"  # all | mine
    my_ids: List[str] = field(default_factory=list)

@dataclass
class AppConfig:
    """Configuracion completa de la aplicacion"""
    asana: AsanaConfig = field(default_factory=AsanaConfig)
    person_map: Dict[str, str] = field(default_factory=dict)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)

# ========================================
# CONFIG MANAGER
# ========================================

class ConfigManager:
    """Gestor de configuracion"""
    
    DEFAULT_CONFIG_FILE = "config_default.json"
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: AppConfig = AppConfig()
        
    def load(self, config_file: str = None) -> AppConfig:
        """Cargar configuracion desde archivo"""
        filename = config_file or self.config_file
        
        # Buscar en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        if not os.path.exists(filepath):
            # Buscar en el directorio actual
            if os.path.exists(filename):
                filepath = filename
            else:
                # Usar configuracion por defecto
                return self.config
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parsear configuracion
            self.config = AppConfig(
                asana=AsanaConfig(
                    token=data.get("asana", {}).get("token", ""),
                    workspace_gid=data.get("asana", {}).get("workspace_gid", "")
                ),
                person_map=data.get("person_map", {}),
                defaults=DefaultsConfig(
                    yaml_file=data.get("defaults", {}).get("yaml_file", "unorganizer/tasks.yml"),
                    dry_run=data.get("defaults", {}).get("dry_run", True),
                    trilium_sync=data.get("defaults", {}).get("trilium_sync", True),
                    conflict_resolution=data.get("defaults", {}).get("conflict_resolution", "latest-wins"),
                    scope=data.get("defaults", {}).get("scope", "all"),
                    my_ids=data.get("defaults", {}).get("my_ids", [])
                )
            )
            
            return self.config
            
        except Exception as e:
            print(f"Error cargando configuracion: {e}")
            return self.config
    
    def save(self, config_file: str = None) -> bool:
        """Guardar configuracion a archivo"""
        filename = config_file or self.config_file
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)
        
        try:
            data = {
                "asana": asdict(self.config.asana),
                "person_map": self.config.person_map,
                "defaults": asdict(self.config.defaults)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error guardando configuracion: {e}")
            return False
    
    def get_person_email(self, person_id: str) -> Optional[str]:
        """Obtener email de una persona"""
        return self.config.person_map.get(person_id)
    
    def set_person(self, person_id: str, email: str):
        """Establecer email de una persona"""
        self.config.person_map[person_id] = email
    
    def get_asana_token(self) -> str:
        """Obtener token de Asana"""
        return self.config.asana.token
    
    def get_workspace_gid(self) -> str:
        """Obtener workspace GID"""
        return self.config.asana.workspace_gid
    
    @staticmethod
    def create_default_config():
        """Crear archivo de configuracion por defecto"""
        config = AppConfig(
            asana=AsanaConfig(
                token="TU_TOKEN_DE_ASANA",
                workspace_gid="TU_WORKSPACE_GID"
            ),
            person_map={
                "P1": "email@tu_dominio.com",
                "P2": "email2@tu_dominio.com",
                "P3": "email3@tu_dominio.com"
            },
            defaults=DefaultsConfig()
        )
        
        return config

# ========================================
# EJEMPLO DE USO
# ========================================

if __name__ == "__main__":
    # Cargar configuracion
    manager = ConfigManager()
    config = manager.load()
    
    print("=== Configuracion Actual ===")
    print(f"Token: {config.asana.token[:20]}..." if config.asana.token else "Token: (vacio)")
    print(f"Workspace: {config.asana.workspace_gid}")
    print(f"Person Map: {config.person_map}")
    print(f"YAML File: {config.defaults.yaml_file}")
    print(f"Dry Run: {config.defaults.dry_run}")
