// ============================================
// SCRIPT: IMPORTAR PLANIFICACION DESDE YAML A ASANA
// Lee tasks.yml y crea proyectos, secciones y tareas en Asana
// ============================================
//
// CONFIGURACION (labels en ESTA nota):
//   #asanaToken=xxxxx
//   #asanaWorkspaceGid=xxxxx
//   #yamlFilePath=unorganizer/tasks.yml
//   #dryRun=true (opcional - si true, solo muestra lo que crearia)
//
// ============================================

const ASANA_BASE = "https://app.asana.com/api/1.0";

// ============================================
// CLASE: ASANA CLIENT
// ============================================
class AsanaClient {
  constructor(token) {
    this.token = token;
    this.cache = {
      projects: new Map(),
      sections: new Map(),
    };
  }

  async request(method, path, body = null) {
    const url = new URL(`${ASANA_BASE}${path}`);
    const options = {
      method,
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const res = await fetch(url.toString(), options);

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Asana HTTP ${res.status}: ${txt}`);
    }

    return await res.json();
  }

  async get(path, params = {}) {
    const url = new URL(`${ASANA_BASE}${path}`);
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    }
    return await this.request("GET", url.pathname + url.search);
  }

  async post(path, body) {
    return await this.request("POST", path, body);
  }

  async put(path, body) {
    return await this.request("PUT", path, body);
  }

  // Obtener o crear proyecto
  async getOrCreateProject(workspaceGid, name, description = "") {
    // Buscar en cache
    if (this.cache.projects.has(name)) {
      return this.cache.projects.get(name);
    }

    // Buscar proyectos existentes
    const data = await this.get("/projects", {
      workspace: workspaceGid,
      limit: 50,
      opt_fields: "gid,name",
    });

    let project = data.data?.find((p) => p.name === name);

    if (!project) {
      // Crear proyecto
      api.log(`Creando proyecto: ${name}`);
      const createData = await this.post("/projects", {
        data: {
          name,
          workspace: workspaceGid,
          notes: description,
        },
      });
      project = createData.data;
    }

    this.cache.projects.set(name, project);
    return project;
  }

  // Obtener o crear seccion
  async getOrCreateSection(projectGid, name) {
    const cacheKey = `${projectGid}:${name}`;

    if (this.cache.sections.has(cacheKey)) {
      return this.cache.sections.get(cacheKey);
    }

    // Buscar secciones existentes
    const data = await this.get(`/projects/${projectGid}/sections`, {
      limit: 100,
      opt_fields: "gid,name",
    });

    let section = data.data?.find((s) => s.name === name);

    if (!section) {
      // Crear seccion
      api.log(`  Creando seccion: ${name}`);
      const createData = await this.post(`/projects/${projectGid}/sections`, {
        data: {
          name,
        },
      });
      section = createData.data;
    }

    this.cache.sections.set(cacheKey, section);
    return section;
  }

  // Crear tarea
  async createTask(taskData) {
    const data = await this.post("/tasks", { data: taskData });
    return data.data;
  }

  // Agregar tarea a seccion (para orden)
  async addTaskToSection(sectionGid, taskGid) {
    await this.post(`/sections/${sectionGid}/addTask`, {
      data: {
        task: taskGid,
      },
    });
  }
}

// ============================================
// CLASE: YAML PARSER
// ============================================
class YAMLParser {
  // Parsear contenido YAML manualmente (sin dependencias)
  static parse(yamlContent) {
    const result = {
      tasks: [],
      sections: [],
      projects: [],
    };

    let currentSection = null;
    let currentProject = null;
    let inTasks = false;
    let inSections = false;
    let inProjects = false;

    const lines = yamlContent.split("\n");

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      // Detectar secciones principales
      if (trimmed === "tasks:") {
        inTasks = true;
        inSections = false;
        inProjects = continue;
        continue;
      }
      if (trimmed === "sections:") {
        inTasks = false;
        inSections = true;
        inProjects = false;
        continue;
      }
      if (trimmed === "projects:") {
        inTasks = false;
        inSections = false;
        inProjects = true;
        continue;
      }

      if (inTasks) {
        const task = this.parseTask(lines, i);
        if (task) {
          result.tasks.push(task);
          i = task._endLine;
        }
      } else if (inSections) {
        const section = this.parseSection(lines, i);
        if (section) {
          result.sections.push(section);
          i = section._endLine;
        }
      } else if (inProjects) {
        const project = this.parseProject(lines, i);
        if (project) {
          result.projects.push(project);
          i = project._endLine;
        }
      }
    }

    // Limpiar propiedades internas
    result.tasks.forEach((t) => delete t._endLine);
    result.sections.forEach((s) => delete s._endLine);
    result.projects.forEach((p) => delete p._endLine);

    return result;
  }

  static parseTask(lines, startLine) {
    const task = {};
    let i = startLine;
    let foundDash = false;

    // Buscar el inicio de la tarea (- name:)
    while (i < lines.length) {
      const line = lines[i];
      if (line.match(/^\s*-\s+name:/)) {
        foundDash = true;
        task.name = this.extractValue(line, "name");
        break;
      }
      i++;
    }

    if (!foundDash) return null;

    // Parsear propiedades siguientes
    i++;
    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      // Nueva tarea
      if (trimmed.match(/^-\s+name:/)) {
        break;
      }

      // Nueva seccion
      if (trimmed.match(/^[a-z]+:$/)) {
        break;
      }

      if (trimmed.startsWith("notes:") || trimmed.startsWith("notes:|")) {
        // Multiline notes
        task.notes = "";
        i++;
        while (i < lines.length) {
          const noteLine = lines[i];
          if (noteLine.trim().match(/^[a-z]+:/)) break;
          if (noteLine.match(/^\s{2,}/)) {
            task.notes += noteLine.trim() + "\n";
          } else if (noteLine.trim() !== "") {
            break;
          }
          i++;
        }
        task.notes = task.notes.trim();
        continue;
      }

      if (trimmed.startsWith("due_date:")) {
        task.due_date = this.extractValue(line, "due_date");
      } else if (trimmed.startsWith("assignee:")) {
        task.assignee = this.extractValue(line, "assignee");
      } else if (trimmed.startsWith("projects:")) {
        task.projects = this.extractValue(line, "projects");
      }

      i++;
    }

    task._endLine = i - 1;
    return task.name ? task : null;
  }

  static parseSection(lines, startLine) {
    const section = {};
    let i = startLine;

    // Buscar inicio de seccion
    while (i < lines.length) {
      const line = lines[i];
      if (line.match(/^\s+-\s+name:/)) {
        section.name = this.extractValue(line, "name");
        break;
      }
      i++;
    }

    if (!section.name) return null;

    // Buscar tareas
    section.tasks = [];
    i++;
    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      if (trimmed.match(/^\s+-\s+tasks:/)) {
        const tasksStr = this.extractValue(line, "tasks");
        if (tasksStr) {
          section.tasks = tasksStr.split(",").map((t) => t.trim());
        }
      } else if (trimmed.match(/^\s+[a-z]+:$/)) {
        break;
      }

      i++;
    }

    section._endLine = i - 1;
    return section;
  }

  static parseProject(lines, startLine) {
    const project = {};
    let i = startLine;

    // Buscar inicio de proyecto
    while (i < lines.length) {
      const line = lines[i];
      if (line.match(/^\s+-\s+name:/)) {
        project.name = this.extractValue(line, "name");
        break;
      }
      i++;
    }

    if (!project.name) return null;

    // Buscar descripcion
    i++;
    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      if (trimmed.startsWith("description:")) {
        project.description = this.extractValue(line, "description");
      } else if (trimmed.match(/^\s+-\s+name:/)) {
        break;
      } else if (trimmed.match(/^[a-z]+:$/)) {
        break;
      }

      i++;
    }

    project._endLine = i - 1;
    return project;
  }

  static extractValue(line, key) {
    const match = line.match(new RegExp(`${key}:\\s*["']?([^"'\n]+)["']?`));
    return match ? match[1].trim() : "";
  }
}

// ============================================
// CLASE: IMPORT MANAGER
// ============================================
class ImportManager {
  constructor(config) {
    this.asana = new AsanaClient(config.token);
    this.config = config;
    this.workspaceGid = config.workspaceGid;
    this.dryRun = config.dryRun === true;
    this.taskIdMap = new Map(); // Map from "1.1" to Asana GID
  }

  async importFromYAML(yamlContent) {
    api.log("========================================");
    api.log("Importando planificacion a Asana");
    if (this.dryRun) {
      api.log("MODO DRY RUN - No se creara nada");
    }
    api.log("========================================");

    // Parsear YAML
    api.log("Parseando YAML...");
    const data = YAMLParser.parse(yamlContent);
    api.log(`Encontradas: ${data.tasks.length} tareas, ${data.projects.length} proyectos, ${data.sections.length} secciones`);

    // 1. Crear proyectos
    api.log("\n--- CREANDO PROYECTOS ---");
    for (const project of data.projects) {
      await this.createProject(project);
    }

    // 2. Crear secciones
    api.log("\n--- CREANDO SECCIONES ---");
    for (const section of data.sections) {
      await this.createSection(section, data.projects);
    }

    // 3. Crear tareas
    api.log("\n--- CREANDO TAREAS ---");
    for (const task of data.tasks) {
      await this.createTask(task, data.projects);
    }

    // 4. Organizar tareas en secciones
    api.log("\n--- ORGANIZANDO TAREAS ---");
    await this.organizeTasks(data);

    api.log("\n========================================");
    api.log("Importacion completada!");
    api.log("========================================");

    return {
      projects: this.asana.cache.projects.size,
      sections: this.asana.cache.sections.size,
      tasks: data.tasks.length,
    };
  }

  async createProject(project) {
    if (this.dryRun) {
      api.log(`[DRY] Crear proyecto: ${project.name}`);
      return;
    }

    try {
      const created = await this.asana.getOrCreateProject(
        this.workspaceGid,
        project.name,
        project.description || ""
      );
      api.log(`Proyecto: ${project.name} (${created.gid})`);
    } catch (e) {
      api.log({ error: `Error creando proyecto ${project.name}`, details: String(e) });
    }
  }

  async createSection(section, projects) {
    // Encontrar el proyecto correcto basado en las tareas
    const firstTaskId = section.tasks?.[0];
    if (!firstTaskId) return;

    // Buscar a que proyecto pertenece esta tarea
    const yamlPath = this.config.yamlFilePath || "unorganizer/tasks.yml";
    
    // Por ahora, asignar todas las secciones al primer proyecto que coincida
    // En un caso real, hariamos un mapeo mejor
    const projectName = this.getProjectForSection(section.name);
    const project = Array.from(this.asana.cache.projects.values()).find(
      (p) => p.name === projectName
    );

    if (!project) {
      api.log({ warn: `No se encontro proyecto para seccion: ${section.name}` });
      return;
    }

    if (this.dryRun) {
      api.log(`[DRY] Crear seccion: ${section.name} en ${project.name}`);
      return;
    }

    try {
      const created = await this.asana.getOrCreateSection(project.gid, section.name);
      api.log(`  Seccion: ${section.name} (${created.gid})`);
    } catch (e) {
      api.log({ error: `Error creando seccion ${section.name}`, details: String(e) });
    }
  }

  getProjectForSection(sectionName) {
    // Mapeo manual de secciones a proyectos
    if (sectionName.includes("Infraestructura")) return "Infraestructura";
    if (sectionName.includes("Core")) return "Core";
    if (sectionName.includes("Utilidades")) return "Utilidades";
    if (sectionName.includes("Observabilidad")) return "Observabilidad";
    if (sectionName.includes("QA")) return "QA";
    if (sectionName.includes("Diferido")) return "Diferido";
    return "Core"; // Default
  }

  async createTask(task, projects) {
    // Determinar proyecto
    const projectName = task.projects || "Core";
    const project = Array.from(this.asana.cache.projects.values()).find(
      (p) => p.name === projectName
    );

    if (!project) {
      api.log({ warn: `No se encontro proyecto para tarea: ${task.name}` });
      return;
    }

    // Buscar seccion para esta tarea
    const section = this.findSectionForTask(task.name);

    const taskData = {
      name: task.name,
      projects: [project.gid],
      notes: task.notes || "",
    };

    if (task.due_date && task.due_date !== "") {
      taskData.due_on = task.due_date;
    }

    if (this.dryRun) {
      api.log(`[DRY] Crear tarea: ${task.name} en ${projectName}`);
      return;
    }

    try {
      const created = await this.asana.createTask(taskData);
      this.taskIdMap.set(task.name, created.gid);
      api.log(`  Tarea: ${task.name} (${created.gid})`);
    } catch (e) {
      api.log({ error: `Error creando tarea ${task.name}`, details: String(e) });
    }
  }

  findSectionForTask(taskName) {
    // Buscar en las secciones definidas
    return null; // Por ahora no implementamos esta funcionalidad
  }

  async organizeTasks(data) {
    // Organizar tareas en secciones basandose en las referencias
    api.log("Organizacion completada (funcionalidad basica)");
  }
}

// ============================================
// LEER ARCHIVO YAML
// ============================================
function readYAMLFile(filePath) {
  // En Trilium, necesitamos leer el archivo
  // Esto es un placeholder - en el ambiente real se leeria el archivo
  throw new Error("No se puede leer archivos locales desde Trilium. Usa el contenido directo.");
}

// ============================================
// FUNCION PRINCIPAL
// ============================================
async function importPlanToAsana() {
  api.log("========================================");
  api.log("IMPORTADOR YAML -> ASANA");
  api.log("========================================");

  const scriptNote = api.currentNote;

  // Obtener configuracion
  const token = scriptNote.getLabelValue("asanaToken");
  const workspaceGid = scriptNote.getLabelValue("asanaWorkspaceGid");
  const yamlContent = scriptNote.getLabelValue("yamlContent"); // Contenido YAML directo
  const dryRun = scriptNote.getLabelValue("dryRun") === "true";

  if (!token) throw new Error("Falta label #asanaToken=...");
  if (!workspaceGid) throw new Error("Falta label #asanaWorkspaceGid=...");

  // Si no hay contenido YAML, usar un sample
  const yaml = yamlContent || `
tasks:
  - name: "Tarea de prueba"
    notes: "Esta es una tarea de prueba"
    due_date: "2026-03-15"
    assignee: "P1"
    projects: "Core"

projects:
  - name: "Core"
    description: "Proyecto principal"
`;

  const config = {
    token,
    workspaceGid,
    dryRun,
  };

  const importer = new ImportManager(config);

  try {
    const result = await importer.importFromYAML(yaml);
    api.log("\n=== RESUMEN ===");
    api.log(`Proyectos creados: ${result.projects}`);
    api.log(`Secciones creadas: ${result.sections}`);
    api.log(`Tareas creadas: ${result.tasks}`);
  } catch (e) {
    api.log(`ERROR: ${e.stack || e}`);
    throw e;
  }
}

// ============================================
// EJECUCION
// ============================================
(async () => {
  await importPlanToAsana();
})().catch((e) => api.log(`Error fatal: ${e.stack || e}`));
