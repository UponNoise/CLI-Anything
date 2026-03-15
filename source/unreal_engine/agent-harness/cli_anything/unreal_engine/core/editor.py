"""Unreal Engine CLI - Editor control module.

Provides editor launch, commandlet execution, and automation control.
Handles headless mode, map loading, game mode specification, and
editor command-line operations.

Copyright (c) 2026 OC-CLIANY Project
SPDX-License-Identifier: MIT
"""

import platform
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class EditorMode(Enum):
    """UE5 editor launch modes."""
    NORMAL = "normal"
    HEADLESS = "headless"
    VR = "vr"
    STANDALONE = "standalone"


class GameMode(Enum):
    """Common UE5 game modes."""
    GAME = "Game"
    EDITOR = "Editor"
    PIE = "PIE"  # Play In Editor
    STANDALONE = "Standalone"


@dataclass
class EditorOptions:
    """Options for UE5 editor launch.

    Attributes:
        map: Map to load on startup (e.g., "/Game/Maps/MainMenu").
        game_mode: Game mode to use.
        mode: Editor launch mode (normal, headless, vr, standalone).
        log: Enable logging to file.
        log_window: Show log window on startup.
        fullscreen: Launch in fullscreen mode.
        windowed: Force windowed mode.
        res_x: Window width.
        res_y: Window height.
        dx11: Force DirectX 11.
        dx12: Force DirectX 12.
        vulkan: Force Vulkan.
        nosplash: Skip splash screen.
        no_slate: Disable Slate UI (for automation).
        unattended: Run in unattended mode (no user interaction).
        extra_args: Additional command-line arguments.
    """
    map: Optional[str] = None
    game_mode: Optional[str] = None
    mode: EditorMode = EditorMode.NORMAL
    log: bool = True
    log_window: bool = False
    fullscreen: bool = False
    windowed: bool = True
    res_x: Optional[int] = None
    res_y: Optional[int] = None
    dx11: bool = False
    dx12: bool = False
    vulkan: bool = False
    nosplash: bool = False
    no_slate: bool = False
    unattended: bool = False
    extra_args: List[str] = field(default_factory=list)


@dataclass
class CommandletOptions:
    """Options for UE5 commandlet execution.

    Attributes:
        commandlet: Name of the commandlet to run.
        args: Arguments to pass to the commandlet.
        unattended: Run in unattended mode.
        null_rhi: Use null RHI (no rendering).
        log: Enable logging.
    """
    commandlet: str
    args: List[str] = field(default_factory=list)
    unattended: bool = True
    null_rhi: bool = True
    log: bool = True


class EditorError(Exception):
    """Base exception for editor operations."""
    pass


class EditorNotFoundError(EditorError):
    """Raised when the editor executable cannot be found."""
    pass


class EditorLaunchError(EditorError):
    """Raised when editor launch fails."""
    pass


class CommandletError(EditorError):
    """Raised when commandlet execution fails."""
    pass


class EditorManager:
    """UE5 editor management and control.

    This class provides methods to launch the UE5 editor with various
    command-line options and execute editor commandlets for automation.

    Example:
        >>> from core.editor import EditorManager, EditorOptions, EditorMode
        >>> from pathlib import Path
        >>>
        >>> editor = EditorManager(
        ...     engine_path=Path("C:/Program Files/Epic Games/UE_5.4"),
        ...     project_path=Path("D:/Projects/MyGame/MyGame.uproject")
        ... )
        >>>
        >>> # Launch editor with a specific map
        >>> options = EditorOptions(
        ...     map="/Game/Maps/MainMenu",
        ...     game_mode="Game",
        ...     windowed=True,
        ...     res_x=1920,
        ...     res_y=1080
        ... )
        >>> process = editor.launch(options)
        >>>
        >>> # Run a commandlet
        >>> editor.run_commandlet("ResavePackages", ["-Package=/Game/Textures"])
    """

    def __init__(
        self,
        engine_path: Union[str, Path],
        project_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize the editor manager.

        Args:
            engine_path: Path to UE5 engine installation.
            project_path: Optional path to the .uproject file.

        Raises:
            EditorNotFoundError: If the editor executable is not found.
        """
        self.engine_path = Path(engine_path).resolve()
        self.project_path = Path(project_path).resolve() if project_path else None
        self._editor_exe = self._find_editor()

    def _find_editor(self) -> Path:
        """Locate the UE5 editor executable.

        Returns:
            Path to the editor executable.

        Raises:
            EditorNotFoundError: If the editor executable cannot be found.
        """
        system = platform.system()

        if system == "Windows":
            editor_paths = [
                self.engine_path / "Engine" / "Binaries" / "Win64" / "UnrealEditor.exe",
                self.engine_path / "Engine" / "Binaries" / "Win64" / "UE4Editor.exe",
            ]
        elif system == "Darwin":  # macOS
            editor_paths = [
                self.engine_path / "Engine" / "Binaries" / "Mac" / "UnrealEditor.app" / "Contents" / "MacOS" / "UnrealEditor",
                self.engine_path / "Engine" / "Binaries" / "Mac" / "UE4Editor.app" / "Contents" / "MacOS" / "UE4Editor",
            ]
        else:  # Linux
            editor_paths = [
                self.engine_path / "Engine" / "Binaries" / "Linux" / "UnrealEditor",
                self.engine_path / "Engine" / "Binaries" / "Linux" / "UE4Editor",
            ]

        for path in editor_paths:
            if path.exists():
                return path

        raise EditorNotFoundError(
            f"Editor executable not found in: {self.engine_path}"
        )

    def launch(
        self,
        options: Optional[EditorOptions] = None,
        wait: bool = False,
    ) -> Union[subprocess.Popen, subprocess.CompletedProcess]:
        """Launch the UE5 editor.

        Args:
            options: Editor launch options. Uses defaults if not provided.
            wait: Whether to wait for the editor to exit before returning.

        Returns:
            subprocess.Popen if wait=False, subprocess.CompletedProcess if wait=True.

        Raises:
            EditorLaunchError: If the editor fails to launch.
        """
        options = options or EditorOptions()
        cmd = self._build_launch_command(options)

        try:
            if wait:
                return subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            else:
                return subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
        except Exception as e:
            raise EditorLaunchError(f"Failed to launch editor: {e}")

    def _build_launch_command(self, options: EditorOptions) -> List[str]:
        """Build the editor launch command.

        Args:
            options: Editor launch options.

        Returns:
            List of command-line arguments.
        """
        cmd: List[str] = [str(self._editor_exe)]

        # Add project path if specified
        if self.project_path:
            cmd.append(str(self.project_path))

        # Map to load
        if options.map:
            cmd.append(options.map)

        # Game mode
        if options.game_mode:
            cmd.append(f"-game={options.game_mode}")

        # Mode-specific options
        if options.mode == EditorMode.HEADLESS:
            cmd.append("-RenderOffScreen")
            cmd.append("-NullRHI")
        elif options.mode == EditorMode.VR:
            cmd.append("-vr")
        elif options.mode == EditorMode.STANDALONE:
            cmd.append("-game")
            cmd.append("-fullscreen")

        # Window options
        if options.fullscreen:
            cmd.append("-fullscreen")
        elif options.windowed:
            cmd.append("-windowed")

        if options.res_x:
            cmd.append(f"-ResX={options.res_x}")
        if options.res_y:
            cmd.append(f"-ResY={options.res_y}")

        # Rendering options
        if options.dx11:
            cmd.append("-dx11")
        if options.dx12:
            cmd.append("-dx12")
        if options.vulkan:
            cmd.append("-vulkan")

        # UI options
        if options.nosplash:
            cmd.append("-nosplash")
        if options.no_slate:
            cmd.append("-NoSlate")
        if options.unattended:
            cmd.append("-unattended")

        # Logging
        if options.log:
            cmd.append("-log")
        if options.log_window:
            cmd.append("-LogWindow")

        # Extra arguments
        cmd.extend(options.extra_args)

        return cmd

    def run_commandlet(
        self,
        commandlet: str,
        args: Optional[List[str]] = None,
        options: Optional[CommandletOptions] = None,
    ) -> Dict[str, Any]:
        """Run an editor commandlet.

        Commandlets are command-line tools built into the editor for
        automation tasks like resaving packages, cooking content, etc.

        Args:
            commandlet: Name of the commandlet to run (e.g., "ResavePackages").
            args: Arguments to pass to the commandlet.
            options: Commandlet execution options.

        Returns:
            Dictionary containing execution results.

        Raises:
            CommandletError: If the commandlet execution fails.
        """
        if options is None:
            options = CommandletOptions(commandlet=commandlet, args=args or [])
        else:
            options.commandlet = commandlet
            if args:
                options.args = args

        cmd = self._build_commandlet_command(options)

        result = {
            "commandlet": commandlet,
            "command": " ".join(cmd),
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": "",
        }

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            result["return_code"] = process.returncode
            result["stdout"] = process.stdout
            result["stderr"] = process.stderr
            result["success"] = process.returncode == 0
        except Exception as e:
            result["stderr"] = str(e)
            raise CommandletError(f"Commandlet execution failed: {e}")

        if not result["success"]:
            raise CommandletError(
                f"Commandlet '{commandlet}' failed with code {result['return_code']}: "
                f"{result['stderr']}"
            )

        return result

    def _build_commandlet_command(self, options: CommandletOptions) -> List[str]:
        """Build the commandlet execution command.

        Args:
            options: Commandlet execution options.

        Returns:
            List of command-line arguments.
        """
        cmd: List[str] = [str(self._editor_exe)]

        # Add project path if specified
        if self.project_path:
            cmd.append(str(self.project_path))

        # Commandlet specification
        cmd.append(f"-run={options.commandlet}")

        # Commandlet arguments
        cmd.extend(options.args)

        # Common options
        if options.unattended:
            cmd.append("-unattended")
        if options.null_rhi:
            cmd.append("-NullRHI")
        if options.log:
            cmd.append("-log")

        return cmd

    def run_resave_packages(
        self,
        package_path: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the ResavePackages commandlet.

        Resaves packages to update them to the current engine version.

        Args:
            package_path: Path to package or directory to resave.
            filter: File filter pattern (e.g., "*.uasset").

        Returns:
            Commandlet execution results.
        """
        args: List[str] = []
        if package_path:
            args.append(f"-Package={package_path}")
        if filter:
            args.append(f"-Filter={filter}")

        return self.run_commandlet("ResavePackages", args)

    def run_cook_commandlet(
        self,
        target_platform: str = "Windows",
        maps: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run the Cook commandlet.

        Cooks content for the specified platform.

        Args:
            target_platform: Target platform (Windows, Mac, Linux, etc.).
            maps: List of maps to cook.

        Returns:
            Commandlet execution results.
        """
        args = [f"-TargetPlatform={target_platform}"]
        if maps:
            args.append(f"-Map={'+'.join(maps)}")

        return self.run_commandlet("Cook", args)

    def run_fixup_redirects(
        self,
        package_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the FixupRedirects commandlet.

        Fixes up redirectors in the project.

        Args:
            package_path: Path to package or directory to fix.

        Returns:
            Commandlet execution results.
        """
        args: List[str] = []
        if package_path:
            args.append(f"-Package={package_path}")

        return self.run_commandlet("FixupRedirects", args)

    def is_running(self, process: Optional[subprocess.Popen] = None) -> bool:
        """Check if the editor process is running.

        Args:
            process: The process object returned by launch().

        Returns:
            True if the editor is running, False otherwise.
        """
        if process is None:
            return False
        return process.poll() is None

    def terminate(self, process: subprocess.Popen) -> None:
        """Terminate the editor process.

        Args:
            process: The process object returned by launch().
        """
        if process.poll() is None:
            process.terminate()

    def kill(self, process: subprocess.Popen) -> None:
        """Force kill the editor process.

        Args:
            process: The process object returned by launch().
        """
        if process.poll() is None:
            process.kill()

    @property
    def editor_path(self) -> Path:
        """Path to the editor executable."""
        return self._editor_exe
