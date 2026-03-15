"""UE CLI 会话管理模块。

管理当前工作上下文和状态，提供会话状态持久化、引擎路径管理、
项目路径管理和命令历史记录功能。

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class SessionError(Exception):
    """会话操作异常基类。"""
    pass


class SessionNotFoundError(SessionError):
    """当会话文件不存在时抛出。"""
    pass


class InvalidSessionError(SessionError):
    """当会话数据无效时抛出。"""
    pass


class SessionState:
    """会话状态数据类。

    存储会话的所有状态信息，包括引擎路径、项目路径、
    当前地图、环境变量和命令历史。

    Attributes:
        engine_path: UE 引擎安装路径。
        project_path: 当前项目路径（.uproject 文件）。
        current_map: 当前打开的地图名称。
        environment: 环境变量字典。
        history: 命令历史记录列表。
        created_at: 会话创建时间。
        updated_at: 会话最后更新时间。
    """

    def __init__(
        self,
        engine_path: Optional[Path] = None,
        project_path: Optional[Path] = None,
        current_map: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        """初始化会话状态。

        Args:
            engine_path: UE 引擎安装路径。
            project_path: 当前项目路径。
            current_map: 当前地图名称。
            environment: 环境变量字典。
            history: 命令历史记录。
            created_at: 创建时间 ISO 格式字符串。
            updated_at: 更新时间 ISO 格式字符串。
        """
        self.engine_path: Optional[Path] = engine_path
        self.project_path: Optional[Path] = project_path
        self.current_map: Optional[str] = current_map
        self.environment: Dict[str, str] = environment or {}
        self.history: List[Dict[str, Any]] = history or []
        self.created_at: str = created_at or datetime.now().isoformat()
        self.updated_at: str = updated_at or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """将会话状态转换为字典。

        Returns:
            包含会话状态的字典。
        """
        return {
            "engine_path": str(self.engine_path) if self.engine_path else None,
            "project_path": str(self.project_path) if self.project_path else None,
            "current_map": self.current_map,
            "environment": self.environment,
            "history": self.history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """从字典创建会话状态。

        Args:
            data: 包含会话状态的字典。

        Returns:
            SessionState 实例。

        Raises:
            InvalidSessionError: 当数据格式无效时。
        """
        try:
            engine_path = data.get("engine_path")
            project_path = data.get("project_path")

            return cls(
                engine_path=Path(engine_path) if engine_path else None,
                project_path=Path(project_path) if project_path else None,
                current_map=data.get("current_map"),
                environment=data.get("environment", {}),
                history=data.get("history", []),
                created_at=data.get("created_at", datetime.now().isoformat()),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
            )
        except (TypeError, ValueError) as e:
            raise InvalidSessionError(f"Invalid session data: {e}")

    def update_timestamp(self) -> None:
        """更新最后修改时间戳。"""
        self.updated_at = datetime.now().isoformat()


class SessionManager:
    """UE CLI 会话管理器。

    管理会话状态的持久化、加载和更新。支持自动保存和
    命令历史记录功能。

    Attributes:
        SESSION_FILE: 默认会话文件名。
        MAX_HISTORY_SIZE: 最大历史记录条数。

    Example:
        >>> from core.session import SessionManager
        >>> session = SessionManager()
        >>> session.set_engine(Path("C:/Program Files/Epic Games/UE_5.4"))
        >>> session.set_project(Path("D:/Projects/MyGame/MyGame.uproject"))
        >>> session.add_command_history("build", {"target": "Editor"})
        >>> session.save()
    """

    SESSION_FILE: str = ".ue_cli_session.json"
    MAX_HISTORY_SIZE: int = 100

    def __init__(
        self,
        working_dir: Union[str, Path] = ".",
        session_file: Optional[str] = None,
        auto_save: bool = True,
    ) -> None:
        """初始化会话管理器。

        Args:
            working_dir: 工作目录，会话文件将存储在此处。
            session_file: 自定义会话文件名，默认使用 SESSION_FILE。
            auto_save: 是否在状态变更时自动保存。
        """
        self.working_dir: Path = Path(working_dir).resolve()
        self.session_file: Path = self.working_dir / (session_file or self.SESSION_FILE)
        self.auto_save: bool = auto_save
        self._state: SessionState = self._load_or_create()

    def _load_or_create(self) -> SessionState:
        """加载现有会话或创建新会话。

        Returns:
            加载或新创建的 SessionState。
        """
        if self.session_file.exists():
            try:
                return self._load_from_file()
            except (SessionError, json.JSONDecodeError):
                # 如果加载失败，创建新会话
                pass
        return SessionState()

    def _load_from_file(self) -> SessionState:
        """从文件加载会话状态。

        Returns:
            加载的 SessionState。

        Raises:
            SessionNotFoundError: 当会话文件不存在时。
            InvalidSessionError: 当会话数据无效时。
        """
        if not self.session_file.exists():
            raise SessionNotFoundError(f"Session file not found: {self.session_file}")

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SessionState.from_dict(data)
        except json.JSONDecodeError as e:
            raise InvalidSessionError(f"Invalid JSON in session file: {e}")
        except IOError as e:
            raise SessionError(f"Failed to read session file: {e}")

    def save(self) -> None:
        """保存会话状态到文件。

        Raises:
            SessionError: 当保存失败时。
        """
        try:
            self.working_dir.mkdir(parents=True, exist_ok=True)
            self._state.update_timestamp()

            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(self._state.to_dict(), f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise SessionError(f"Failed to save session: {e}")

    def _auto_save(self) -> None:
        """如果启用自动保存，则保存会话。"""
        if self.auto_save:
            self.save()

    def set_engine(self, engine_path: Union[str, Path]) -> None:
        """设置引擎路径。

        Args:
            engine_path: UE 引擎安装路径。

        Raises:
            SessionError: 当路径无效时。
        """
        path = Path(engine_path).resolve()
        if not path.exists():
            raise SessionError(f"Engine path does not exist: {path}")

        self._state.engine_path = path
        self._state.update_timestamp()
        self._auto_save()

    def get_engine(self) -> Optional[Path]:
        """获取当前设置的引擎路径。

        Returns:
            引擎路径，如果未设置则返回 None。
        """
        return self._state.engine_path

    def clear_engine(self) -> None:
        """清除引擎路径设置。"""
        self._state.engine_path = None
        self._state.update_timestamp()
        self._auto_save()

    def set_project(self, project_path: Union[str, Path]) -> None:
        """设置项目路径。

        Args:
            project_path: .uproject 文件路径。

        Raises:
            SessionError: 当路径无效或不是 .uproject 文件时。
        """
        path = Path(project_path).resolve()
        if not path.exists():
            raise SessionError(f"Project file does not exist: {path}")
        if path.suffix != ".uproject":
            raise SessionError(f"Not a valid .uproject file: {path}")

        self._state.project_path = path
        self._state.update_timestamp()
        self._auto_save()

    def get_project(self) -> Optional[Path]:
        """获取当前设置的项目路径。

        Returns:
            项目路径（.uproject 文件），如果未设置则返回 None。
        """
        return self._state.project_path

    def clear_project(self) -> None:
        """清除项目路径设置。"""
        self._state.project_path = None
        self._state.current_map = None
        self._state.update_timestamp()
        self._auto_save()

    def set_current_map(self, map_name: str) -> None:
        """设置当前地图。

        Args:
            map_name: 地图名称或路径。
        """
        self._state.current_map = map_name
        self._state.update_timestamp()
        self._auto_save()

    def get_current_map(self) -> Optional[str]:
        """获取当前地图。

        Returns:
            当前地图名称，如果未设置则返回 None。
        """
        return self._state.current_map

    def clear_current_map(self) -> None:
        """清除当前地图设置。"""
        self._state.current_map = None
        self._state.update_timestamp()
        self._auto_save()

    def set_environment_variable(self, key: str, value: str) -> None:
        """设置环境变量。

        Args:
            key: 环境变量名。
            value: 环境变量值。
        """
        self._state.environment[key] = value
        self._state.update_timestamp()
        self._auto_save()

    def get_environment_variable(self, key: str) -> Optional[str]:
        """获取环境变量。

        Args:
            key: 环境变量名。

        Returns:
            环境变量值，如果不存在则返回 None。
        """
        return self._state.environment.get(key)

    def remove_environment_variable(self, key: str) -> None:
        """移除环境变量。

        Args:
            key: 环境变量名。
        """
        if key in self._state.environment:
            del self._state.environment[key]
            self._state.update_timestamp()
            self._auto_save()

    def get_all_environment_variables(self) -> Dict[str, str]:
        """获取所有环境变量。

        Returns:
            环境变量字典的副本。
        """
        return self._state.environment.copy()

    def add_command_history(
        self,
        command: str,
        args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
    ) -> None:
        """添加命令到历史记录。

        Args:
            command: 命令名称。
            args: 命令参数字典。
            result: 命令执行结果摘要。
        """
        entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "args": args or {},
        }
        if result:
            entry["result"] = result

        self._state.history.append(entry)

        # 限制历史记录大小
        if len(self._state.history) > self.MAX_HISTORY_SIZE:
            self._state.history = self._state.history[-self.MAX_HISTORY_SIZE :]

        self._state.update_timestamp()
        self._auto_save()

    def get_command_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取命令历史记录。

        Args:
            limit: 返回的最大记录数，None 表示全部。

        Returns:
            命令历史记录列表，最新的在最后。
        """
        history = self._state.history.copy()
        if limit is not None and limit > 0:
            history = history[-limit:]
        return history

    def clear_command_history(self) -> None:
        """清除命令历史记录。"""
        self._state.history.clear()
        self._state.update_timestamp()
        self._auto_save()

    def get_state(self) -> SessionState:
        """获取当前会话状态的副本。

        Returns:
            SessionState 实例的副本。
        """
        return SessionState.from_dict(self._state.to_dict())

    def get_working_dir(self) -> Path:
        """获取工作目录。

        Returns:
            工作目录路径。
        """
        return self.working_dir

    def get_session_file_path(self) -> Path:
        """获取会话文件路径。

        Returns:
            会话文件完整路径。
        """
        return self.session_file

    def is_valid(self) -> bool:
        """检查会话是否有效（至少设置了引擎或项目）。

        Returns:
            如果引擎路径或项目路径已设置则返回 True。
        """
        return self._state.engine_path is not None or self._state.project_path is not None

    def reset(self) -> None:
        """重置会话到初始状态。"""
        self._state = SessionState()
        self._auto_save()

    def export_to_dict(self) -> Dict[str, Any]:
        """导出会话状态为字典。

        Returns:
            会话状态字典。
        """
        return self._state.to_dict()

    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典导入会话状态。

        Args:
            data: 包含会话状态的字典。

        Raises:
            InvalidSessionError: 当数据格式无效时。
        """
        self._state = SessionState.from_dict(data)
        self._auto_save()


# 向后兼容的别名
Session = SessionManager
