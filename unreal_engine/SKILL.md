---
name: unreal-engine
description: "Unreal Engine 5 CLI 工具集，提供项目管理、构建系统、编辑器控制、资产管理等自动化功能。支持 UE5 项目创建、编译、打包、插件管理等完整工作流。"
homepage: https://github.com/oc-cliany/unreal-engine-cli
metadata:
  {
    "openclaw": {
      "emoji": "🎮",
      "requires": {
        "bins": ["python"],
        "pythonPackages": ["click", "pydantic", "colorama", "prompt-toolkit", "rich", "pygments"]
      },
      "config": {
        "engine_path": "C:/Program Files/Epic Games/UE_5.4",
        "default_project_template": "Blank",
        "build_parallel_jobs": 8
      }
    }
  }
---

# Unreal Engine 5 CLI 技能

为 Unreal Engine 5 提供完整的命令行接口和自动化工具集，支持项目管理、构建系统、编辑器控制、资产管理等完整工作流。

## 何时使用

✅ **使用此技能当需要：**

- 自动化 UE5 项目创建和配置
- 批量构建和编译项目
- 控制 Unreal Editor 行为
- 管理游戏资产和蓝图
- 处理插件安装和配置
- 执行项目打包和发布
- 集成到 CI/CD 流水线

❌ **不要使用此技能当：**

- 需要图形界面操作（使用 Unreal Editor）
- 实时游戏开发调试（使用编辑器内调试工具）
- 美术资源创作（使用专业 DCC 工具）

## 快速开始

### 安装

```bash
# 从 PyPI 安装
pip install unreal-engine-cli

# 从源码安装
git clone https://github.com/oc-cliany/unreal-engine-cli.git
cd unreal-engine-cli
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

### 基本使用

```bash
# 显示帮助
ue-cli --help

# 启动交互式 REPL
ue-cli repl

# 创建新项目
ue-cli project create MyGame --template=ThirdPerson

# 构建项目
ue-cli build --target=Editor --platform=Win64

# 启动编辑器
ue-cli editor launch --map=/Game/Maps/MainMenu
```

## 工具接口集成

### 1. unreal_engine_cli 接口

主 CLI 接口，提供完整的命令集：

```python
# Python API 使用示例
from cli_anything.unreal_engine import UE5CLI

# 初始化 CLI
cli = UE5CLI()

# 执行命令
result = cli.execute_command("project", ["create", "MyProject", "--template=Blank"])
print(result)
```

### 2. ue5_project 项目管理接口

```python
from cli_anything.unreal_engine.core.project import ProjectManager, ProjectInfo

# 初始化项目管理器
project_manager = ProjectManager()

# 创建新项目
project_info = project_manager.create_project(
    name="MyGame",
    template="FirstPerson",
    path=Path("D:/Projects/MyGame")
)

# 打开现有项目
project_info = project_manager.open_project(
    project_path=Path("D:/Projects/MyGame/MyGame.uproject")
)

# 分析项目依赖
dependencies = project_manager.analyze_dependencies(project_info.path)
```

### 3. ue5_build 编译系统接口

```python
from cli_anything.unreal_engine.core.build import (
    BuildSystem, BuildOptions, BuildConfiguration, BuildTarget, BuildPlatform
)

# 初始化构建系统
build_system = BuildSystem(
    engine_path=Path("C:/Program Files/Epic Games/UE_5.4")
)

# 配置构建选项
options = BuildOptions(
    configuration=BuildConfiguration.DEVELOPMENT,
    target=BuildTarget.EDITOR,
    platform=BuildPlatform.WIN64,
    verbose=True,
    parallel=8
)

# 执行构建
result = build_system.build_project(
    project_path=Path("D:/Projects/MyGame/MyGame.uproject"),
    options=options
)

if result["success"]:
    print("构建成功！")
else:
    print(f"构建失败: {result['stderr']}")
```

### 4. ue5_editor 编辑器控制接口

```python
from cli_anything.unreal_engine.core.editor import (
    EditorManager, EditorOptions, EditorMode
)

# 初始化编辑器管理器
editor = EditorManager(
    engine_path=Path("C:/Program Files/Epic Games/UE_5.4"),
    project_path=Path("D:/Projects/MyGame/MyGame.uproject")
)

# 配置编辑器选项
options = EditorOptions(
    map="/Game/Maps/MainMenu",
    game_mode="Game",
    mode=EditorMode.HEADLESS,
    windowed=True,
    res_x=1920,
    res_y=1080,
    unattended=True
)

# 启动编辑器（无头模式）
process = editor.launch(options, wait=False)

# 执行命令
result = editor.run_commandlet("ResavePackages", ["-Package=/Game/Textures"])
```

### 5. ue5_asset 资产管理接口

```python
from cli_anything.unreal_engine.core.asset import (
    AssetManager, ImportOptions, AssetType
)

# 初始化资产管理器
asset_manager = AssetManager(
    project_path=Path("D:/Projects/MyGame/MyGame.uproject")
)

# 导入资产
import_options = ImportOptions(
    import_materials=True,
    import_textures=True,
    import_lods=True,
    auto_generate_collision=True
)

asset_path = asset_manager.import_asset(
    source_path=Path("D:/Models/Character.fbx"),
    destination_path="/Game/Characters/MainCharacter",
    options=import_options
)

# 列出资产
materials = asset_manager.list_assets(
    path="/Game",
    recursive=True,
    filter_type=AssetType.MATERIAL
)
```

### 6. ue5_plugin 插件管理接口

```python
from cli_anything.unreal_engine.core.plugin import PluginManager

# 初始化插件管理器
plugin_manager = PluginManager(
    project_path=Path("D:/Projects/MyGame/MyGame.uproject")
)

# 列出所有插件
plugins = plugin_manager.list_plugins()

# 启用插件
plugin_manager.enable_plugin("MyPlugin")

# 安装插件
plugin_manager.install_plugin(
    source_path=Path("D:/Plugins/MyPlugin.zip"),
    plugin_name="MyPlugin"
)
```

## OpenClaw 集成配置

### 技能配置文件

在 OpenClaw 配置中添加以下内容：

```json
{
  "skills": {
    "unreal_engine": {
      "enabled": true,
      "engine_path": "C:/Program Files/Epic Games/UE_5.4",
      "default_project_path": "D:/Projects",
      "build_options": {
        "parallel_jobs": 8,
        "default_platform": "Win64",
        "default_configuration": "Development"
      },
      "editor_options": {
        "headless_by_default": false,
        "default_map": "/Game/Maps/DefaultMap"
      }
    }
  }
}
```

### 环境变量设置

```bash
# Windows
set UE_ENGINE_PATH=C:\Program Files\Epic Games\UE_5.4
set UE_PROJECT_PATH=D:\Projects
set UE_BUILD_PARALLEL=8

# Linux/macOS
export UE_ENGINE_PATH="/opt/UnrealEngine/UE_5.4"
export UE_PROJECT_PATH="$HOME/Projects"
export UE_BUILD_PARALLEL=8
```

### 权限和安全性配置

```yaml
# security.yaml
unreal_engine:
  allowed_operations:
    - project.create
    - project.open
    - build.execute
    - editor.launch
    - asset.import
    - asset.export
    - plugin.manage
  
  restricted_paths:
    - "C:/Windows"
    - "/etc"
    - "/usr"
  
  max_build_time: 3600  # 最大构建时间（秒）
  max_file_size: 1073741824  # 最大文件大小（1GB）
```

## 使用指南

### CLI 调用示例

```bash
# 项目管理
ue-cli project create MyProject --template=Blank --output-dir=D:/Projects
ue-cli project open D:/Projects/MyProject/MyProject.uproject
ue-cli project info

# 构建系统
ue-cli build --target=Editor --platform=Win64 --configuration=Development
ue-cli build clean
ue-cli build rebuild --target=Game --platform=Win64

# 编辑器控制
ue-cli editor launch --map=/Game/Maps/MainMenu --headless
ue-cli editor commandlet ResavePackages -Package=/Game/Textures
ue-cli editor status

# 资产管理
ue-cli asset import D:/Models/Character.fbx /Game/Characters/MainCharacter
ue-cli asset list --path=/Game/Characters --recursive
ue-cli asset references /Game/Characters/MainCharacter

# 插件管理
ue-cli plugin list
ue-cli plugin enable MyPlugin
ue-cli plugin install D:/Plugins/MyPlugin.zip

# 打包发布
ue-cli cook --platform=Win64
ue-cli package --platform=Win64 --configuration=Shipping
```

### Python API 使用示例

```python
import sys
from pathlib import Path
from cli_anything.unreal_engine import UE5CLI
from cli_anything.unreal_engine.core.build import BuildSystem, BuildOptions

def automate_build_pipeline():
    """自动化构建流水线示例"""
    
    # 初始化 CLI
    cli = UE5CLI()
    
    # 1. 创建项目
    print("创建项目...")
    result = cli.execute_command("project", [
        "create", "MyAutomatedGame",
        "--template=ThirdPerson",
        "--output-dir=D:/Projects"
    ])
    
    if not result["success"]:
        print(f"项目创建失败: {result['error']}")
        return
    
    project_path = Path("D:/Projects/MyAutomatedGame/MyAutomatedGame.uproject")
    
    # 2. 构建项目
    print("构建项目...")
    build_system = BuildSystem(
        engine_path=Path("C:/Program Files/Epic Games/UE_5.4")
    )
    
    build_options = BuildOptions(
        target="Editor",
        platform="Win64",
        configuration="Development",
        verbose=True,
        parallel=8
    )
    
    build_result = build_system.build_project(project_path, build_options)
    
    if build_result["success"]:
        print("构建成功！")
    else:
        print(f"构建失败: {build_result['stderr']}")
        return
    
    # 3. 启动编辑器执行命令
    print("启动编辑器执行命令...")
    editor_result = cli.execute_command("editor", [
        "launch",
        "--headless",
        "--command=ResavePackages -Package=/Game"
    ])
    
    # 4. 打包项目
    print("打包项目...")
    package_result = cli.execute_command("package", [
        "--platform=Win64",
        "--configuration=Shipping",
        "--output-dir=D:/Builds"
    ])
    
    if package_result["success"]:
        print("自动化流水线完成！")
    else:
        print(f"打包失败: {package_result['error']}")

if __name__ == "__main__":
    automate_build_pipeline()
```

### OpenClaw 集成示例

```python
# OpenClaw 技能集成示例
from openclaw.skills.base import Skill
from pathlib import Path
import subprocess
import json

class UnrealEngineSkill(Skill):
    """Unreal Engine 技能实现"""
    
    def __init__(self, config):
        super().__init__(config)
        self.engine_path = Path(config.get("engine_path", ""))
        self.project_path = Path(config.get("project_path", ""))
        
    def create_project(self, name, template="Blank", output_dir=None):
        """创建 UE5 项目"""
        if not output_dir:
            output_dir = self.project_path
            
        cmd = [
            "ue-cli", "project", "create", name,
            f"--template={template}",
            f"--output-dir={output_dir}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            project_file = output_dir / name / f"{name}.uproject"
            return {
                "success": True,
                "project_path": str(project_file),
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "error": result.stderr,
                "output": result.stdout
            }
    
    def build_project(self, project_path, target="Editor", platform="Win64"):
        """构建 UE5 项目"""
        cmd = [
            "ue-cli", "build",
            f"--target={target}",
            f"--platform={platform}",
            f"--project={project_path}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def import_asset(self, project_path, source_path, destination_path):
        """导入资产到项目"""
        cmd = [
            "ue-cli", "asset", "import",
            source_path, destination_path,
            f"--project={project_path}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "asset_path": destination_path,
            "output": result.stdout
        }
```

## 配置示例

### 完整技能配置

```yaml
# skills/unreal_engine.yaml
name: unreal-engine
version: 1.0.0
author: OC-CLIANY Project
description: Unreal Engine 5 CLI 工具集

# 引擎配置
engine:
  path: "C:/Program Files/Epic Games/UE_5.4"
  version: "5.4.0"
  detect_automatically: true

# 项目配置
project:
  default_template: "Blank"
  default_output_dir: "D:/Projects"
  auto_open_after_create: true

# 构建配置
build:
  default_platform: "Win64"
  default_configuration: "Development"
  parallel_jobs: 8
  clean_before_build: true
  generate_project_files: true

# 编辑器配置
editor:
  default_map: "/Game/Maps/DefaultMap"
  headless_by_default: false
  windowed: true
  resolution: "1920x1080"
  unattended: true

# 资产配置
asset:
  default_import_options:
    import_materials: true
    import_textures: true
    import_lods: true
    auto_generate_collision: true
  supported_formats:
    - ".fbx"
    - ".obj"
    - ".blend"
    - ".tga"
    - ".png"
    - ".jpg"

# 插件配置
plugin:
  enabled_by_default: false
  auto_update: true
  trusted_sources:
    - "Epic Marketplace"
    - "GitHub"

# 日志配置
logging:
  level: "INFO"
  file: "~/.ue_cli/ue_cli.log"
  max_size_mb: 100
  backup_count: 5

# 安全性配置
security:
  allowed_operations:
    - project.create
    - project.open
    - build.execute
    - editor.launch
    - asset.import
    - asset.export
    - plugin.manage
  require_confirmation: true
  max_file_size_mb: 1024
  timeout_seconds: 3600
```

### 项目特定配置

```json
{
  "project": {
    "name": "MyGame",
    "engine_version": "5.4.0",
    "ue_cli_version": "1.0.0"
  },
  "build": {
    "targets": [
      {
        "name": "Editor",
        "platform": "Win64",
        "configuration": "Development",
        "enabled": true
      },
      {
        "name": "Game",
        "platform": "Win64",
        "configuration": "Shipping",
        "enabled": true
      },
      {
        "name": "Server",
        "platform": "Win64",
        "configuration": "Development",
        "enabled": false
      }
    ],
    "options": {
      "parallel": 8,
      "verbose": true,
      "clean": false
    }
  },
  "assets": {
    "import_directories": [
      "D:/Assets/Models",
      "D:/Assets/Textures",
      "D:/Assets/Audio"
    ],
    "export_formats": ["fbx", "obj", "png", "wav"],
    "auto_reimport": true
  },
  "plugins": {
    "required": ["MyPlugin", "AnotherPlugin"],
    "optional": ["ExperimentalPlugin"],
    "disabled": ["OldPlugin"]
  },
  "packaging": {
    "platforms": ["Win64", "Android", "iOS"],
    "configurations": ["Development", "Shipping"],
    "output_directory": "D:/Builds",
    "include_symbols": false,
    "compress": true
  }
}
```

## 故障排除

### 常见问题

1. **引擎路径未找到**
   ```bash
   # 设置引擎路径环境变量
   set UE_ENGINE_PATH=C:\Program Files\Epic Games\UE_5.4
   
   # 或在配置文件中指定
   echo '{"engine_path": "C:/Program Files/Epic Games/UE_5.4"}' > ~/.ue_cli/config.json
   ```

2. **项目文件损坏**
   ```bash
   # 验证项目文件
   ue-cli project validate MyProject.uproject
   
   # 重新生成项目文件
   ue-cli build generate --project=MyProject.uproject
   ```

3. **构建失败**
   ```bash
   # 清理构建缓存
   ue-cli build clean --project=MyProject.uproject
   
   # 启用详细日志
   ue-cli build --target=Editor --verbose --project=MyProject.uproject
   
   # 检查依赖
   ue-cli project dependencies --project=MyProject.uproject
   ```

4. **编辑器启动失败**
   ```bash
   # 检查编辑器版本
   ue-cli editor version
   
   # 以无头模式启动
   ue-cli editor launch --headless --project=MyProject.uproject
   
   # 检查日志文件
   tail -f ~/AppData/Local/UnrealEngine/Common/Logs/Editor.log
   ```

### 调试技巧

```python
# 启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)

from cli_anything.unreal_engine import UE5CLI

# 创建带调试的 CLI 实例
cli = UE5CLI(debug=True)

# 执行命令并捕获详细输出
result = cli.execute_command("build", ["--target=Editor", "--verbose"])
print(f"返回码: {result.returncode}")
print(f"标准输出: {result.stdout}")
print(f"标准错误: {result.stderr}")
```

## 最佳实践

### 项目组织

1. **使用版本控制**
   ```bash
   # 初始化 Git 仓库
   git init
   
   # 添加 .gitignore 用于 UE5 项目
   curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/main/UnrealEngine.gitignore
   
   # 提交初始版本
   git add .
   git commit -m "Initial UE5 project"
   ```

2. **模块化设计**
   ```python
   # 创建模块化项目结构
   project_structure = {
       "Source": {
           "MyGame": ["Public", "Private"],
           "MyGameEditor": ["Public", "Private"]
       },
       "Content": {
           "Characters": ["Blueprints", "Meshes", "Textures"],
           "Environments": ["Maps", "Materials", "Props"],
           "UI": ["Widgets", "Fonts", "Icons"]
       }
   }
   ```

3. **自动化脚本**
   ```python
   # 创建自动化构建脚本
   # build_automation.py
   import sys
   from pathlib import Path
   from cli_anything.unreal_engine import UE5CLI
   
   def main():
       cli = UE5CLI()
       
       # 1. 清理
       cli.execute_command("build", ["clean"])
       
       # 2. 构建
       build_result = cli.execute_command("build", [
           "--target=Editor",
           "--platform=Win64",
           "--configuration=Development"
       ])
       
       if not build_result["success"]:
           print("构建失败")
           sys.exit(1)
       
       # 3. 运行测试
       test_result = cli.execute_command("editor", [
           "commandlet", "RunTests",
           "-Project=MyProject.uproject"
       ])
       
       # 4. 打包
       if test_result["success"]:
           cli.execute_command("package", [
               "--platform=Win64",
               "--configuration=Shipping"
           ])
   
   if __name__ == "__main__":
       main()
   ```

### 性能优化

1. **并行构建**
   ```bash
   # 根据 CPU 核心数设置并行任务
   ue-cli build --target=Editor --parallel=$(nproc)
   
   # Windows
   ue-cli build --target=Editor --parallel=%NUMBER_OF_PROCESSORS%
   ```

2. **增量构建**
   ```bash
   # 启用增量构建（默认）
   ue-cli build --target=Editor --incremental
   
   # 禁用增量构建（完整重建）
   ue-cli build --target=Editor --no-incremental
   ```

3. **缓存优化**
   ```bash
   # 清理派生数据缓存
   ue-cli build clean --derived-data
   
   # 设置缓存位置
   ue-cli config set build.cache_dir "D:/UE5_Cache"
   ```

## 扩展开发

### 自定义命令

```python
# custom_commands.py
import click
from cli_anything.unreal_engine import UE5CLI

@click.command()
@click.option("--project", required=True, help="Project file path")
@click.option("--output", default="./report", help="Output directory")
def generate_docs(project, output):
    """生成项目文档"""
    cli = UE5CLI()
    
    # 1. 提取项目信息
    project_info = cli.execute_command("project", ["info", project])
    
    # 2. 列出所有资产
    assets = cli.execute_command("asset", ["list", "--recursive", project])
    
    # 3. 生成文档
    with open(f"{output}/project_docs.md", "w") as f:
        f.write(f"# {project_info['name']} 项目文档\n\n")
        f.write(f"引擎版本: {project_info['engine_version']}\n\n")
        f.write("## 资产列表\n\n")
        for asset in assets:
            f.write(f"- {asset['name']} ({asset['type']})\n")
    
    click.echo(f"文档已生成到: {output}/project_docs.md")

if __name__ == "__main__":
    generate_docs()
```

### 插件开发

```python
# custom_plugin.py
from cli_anything.unreal_engine.core.plugin import PluginManager, PluginInfo

class CustomPluginManager(PluginManager):
    """自定义插件管理器"""
    
    def install_from_git(self, repo_url, branch="main"):
        """从 Git 仓库安装插件"""
        import tempfile
        import shutil
        import subprocess
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 克隆仓库
            subprocess.run([
                "git", "clone",
                "--branch", branch,
                "--depth", "1",
                repo_url,
                temp_dir
            ], check=True)
            
            # 安装插件
            plugin_name = repo_url.split("/")[-1].replace(".git", "")
            return self.install_plugin(
                source_path=Path(temp_dir),
                plugin_name=plugin_name
            )
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def update_all_plugins(self):
        """更新所有插件"""
        plugins = self.list_plugins()
        
        for plugin in plugins:
            if plugin.get("update_url"):
                self.update_plugin(plugin["name"], plugin["update_url"])
```

## API 参考

### 核心类

| 类名 | 描述 | 主要方法 |
|------|------|----------|
| `UE5CLI` | 主 CLI 接口 | `execute_command()`, `start_repl()` |
| `ProjectManager` | 项目管理 | `create_project()`, `open_project()` |
| `BuildSystem` | 构建系统 | `build_project()`, `clean_project()` |
| `EditorManager` | 编辑器控制 | `launch()`, `run_commandlet()` |
| `AssetManager` | 资产管理 | `import_asset()`, `export_asset()` |
| `PluginManager` | 插件管理 | `list_plugins()`, `enable_plugin()` |
| `BlueprintManager` | 蓝图操作 | `create_blueprint()`, `compile_blueprint()` |

### 配置选项

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `engine_path` | `Path` | `""` | UE5 引擎安装路径 |
| `project_path` | `Path` | `""` | 项目文件路径 |
| `build.parallel` | `int` | `4` | 并行构建任务数 |
| `build.platform` | `str` | `"Win64"` | 目标平台 |
| `editor.headless` | `bool` | `false` | 无头模式 |
| `asset.import_options` | `dict` | `{}` | 资产导入选项 |

### 错误代码

| 代码 | 描述 | 解决方案 |
|------|------|----------|
| `ERR_ENGINE_NOT_FOUND` | 引擎未找到 | 设置 `UE_ENGINE_PATH` 环境变量 |
| `ERR_PROJECT_INVALID` | 项目文件无效 | 验证 `.uproject` 文件格式 |
| `ERR_BUILD_FAILED` | 构建失败 | 检查编译错误日志 |
| `ERR_EDITOR_LAUNCH` | 编辑器启动失败 | 检查引擎版本兼容性 |
| `ERR_ASSET_IMPORT` | 资产导入失败 | 检查文件格式和权限 |

## 更新日志

### v1.0.0 (2026-03-15)
- 初始版本发布
- 支持 UE5 项目管理、构建、编辑器控制
- 提供完整的 CLI 接口和 Python API
- 包含资产管理、插件管理、蓝图操作等功能
- 支持 OpenClaw 集成

## 支持与贡献

### 获取帮助

- **文档**: [https://docs.ue5cliany.org](https://docs.ue5cliany.org)
- **GitHub**: [https://github.com/oc-cliany/unreal-engine-cli](https://github.com/oc-cliany/unreal-engine-cli)
- **Discord**: [https://discord.gg/ue5cliany](https://discord.gg/ue5cliany)
- **邮箱**: contact@oc-cliany.org

### 报告问题

```bash
# 收集调试信息
ue-cli debug info --output=debug_report.json

# 提交问题到 GitHub
gh issue create --title="问题描述" --body="$(cat debug_report.json)"
```

### 贡献代码

1. Fork 仓库
2. 创建功能分支
3. 提交更改
4. 运行测试
5. 创建 Pull Request

```bash
# 开发环境设置
git clone https://github.com/oc-cliany/unreal-engine-cli.git
cd unreal-engine-cli
pip install -e ".[dev]"
pre-commit install

# 运行测试
pytest

# 代码检查
ruff check .
mypy cli_anything/unreal_engine
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

*技能版本: 1.0.0 | 最后更新: 2026-03-15 | UE5-CLIANY 项目团队*
