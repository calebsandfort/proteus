"""Tests for PromptManager and PromptVersion (FR-8.7)"""

import pytest
from datetime import datetime
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.agent.prompts import (
    PromptVersion,
    PromptManager,
)


class TestPromptVersionModel:
    """FR-8.7: PromptVersion model validation"""

    def test_prompt_version_model(self):
        """PromptVersion has all required fields"""
        version = PromptVersion(
            version="v1.0.0",
            template_name="test_prompt",
            template_content="Hello {name}",
            variables=["name"],
            created_at=datetime.now(),
            created_by="test_user",
            changelog="Initial version",
        )
        assert version.version == "v1.0.0"
        assert version.template_name == "test_prompt"
        assert version.template_content == "Hello {name}"
        assert version.variables == ["name"]
        assert version.created_by == "test_user"
        assert version.changelog == "Initial version"

    def test_prompt_version_changelog_optional(self):
        """PromptVersion changelog field is optional"""
        version = PromptVersion(
            version="v1.0.0",
            template_name="test_prompt",
            template_content="Hello {name}",
            variables=["name"],
            created_at=datetime.now(),
            created_by="test_user",
        )
        assert version.changelog is None


class TestPromptManagerInitialization:
    """FR-8.7: PromptManager initialization"""

    def test_prompt_manager_initialization_empty_dir(self, monkeypatch):
        """PromptManager initializes with empty dict when no prompts"""
        # Mock Path.exists to return False (no prompts directory)
        with patch("src.agent.prompts.Path.exists", return_value=False):
            manager = PromptManager(prompt_dir="./nonexistent")
            assert manager.prompts == {}

    def test_prompt_manager_initialization_with_prompts(self):
        """PromptManager initializes with provided prompts dict"""
        prompts = {
            "greeting": {
                "v1.0.0": PromptVersion(
                    version="v1.0.0",
                    template_name="greeting",
                    template_content="Hello {name}",
                    variables=["name"],
                    created_at=datetime.now(),
                    created_by="test",
                )
            }
        }
        manager = PromptManager(prompt_dir="./config/prompts", prompts=prompts)
        assert "greeting" in manager.prompts
        assert "v1.0.0" in manager.prompts["greeting"]


class TestPromptManagerGetPrompt:
    """FR-8.7: Prompt retrieval"""

    def test_prompt_manager_get_prompt_raises_for_missing(self):
        """get_prompt raises ValueError for unknown prompt"""
        manager = PromptManager(prompt_dir="./config/prompts", prompts={})
        with pytest.raises(ValueError, match="Prompt unknown_prompt version latest not found"):
            manager.get_prompt("unknown_prompt")

    def test_prompt_manager_get_prompt_raises_for_missing_version(self):
        """get_prompt raises ValueError for unknown version"""
        prompts = {
            "greeting": {
                "v1.0.0": PromptVersion(
                    version="v1.0.0",
                    template_name="greeting",
                    template_content="Hello {name}",
                    variables=["name"],
                    created_at=datetime.now(),
                    created_by="test",
                )
            }
        }
        manager = PromptManager(prompt_dir="./config/prompts", prompts=prompts)
        with pytest.raises(ValueError, match="Prompt greeting version v2.0.0 not found"):
            manager.get_prompt("greeting", version="v2.0.0")

    def test_prompt_manager_get_prompt_returns_content(self):
        """get_prompt returns template content for valid prompt"""
        prompts = {
            "greeting": {
                "v1.0.0": PromptVersion(
                    version="v1.0.0",
                    template_name="greeting",
                    template_content="Hello {name}",
                    variables=["name"],
                    created_at=datetime.now(),
                    created_by="test",
                )
            }
        }
        manager = PromptManager(prompt_dir="./config/prompts", prompts=prompts)
        content = manager.get_prompt("greeting", version="v1.0.0")
        assert content == "Hello {name}"


class TestPromptManagerRenderPrompt:
    """FR-8.7: Prompt rendering with variables"""

    def test_prompt_manager_render_prompt(self):
        """render_prompt substitutes variables into template"""
        prompts = {
            "greeting": {
                "v1.0.0": PromptVersion(
                    version="v1.0.0",
                    template_name="greeting",
                    template_content="Hello {name}, you have {count} messages",
                    variables=["name", "count"],
                    created_at=datetime.now(),
                    created_by="test",
                )
            }
        }
        manager = PromptManager(prompt_dir="./config/prompts", prompts=prompts)
        rendered, version = manager.render_prompt("greeting", {"name": "Alice", "count": 5})
        assert rendered == "Hello Alice, you have 5 messages"

    def test_prompt_manager_render_prompt_returns_version(self):
        """render_prompt returns PromptVersion with correct metadata"""
        created_at = datetime.now()
        prompts = {
            "greeting": {
                "v1.0.0": PromptVersion(
                    version="v1.0.0",
                    template_name="greeting",
                    template_content="Hello {name}",
                    variables=["name"],
                    created_at=created_at,
                    created_by="test_user",
                    changelog="Initial version",
                )
            }
        }
        manager = PromptManager(prompt_dir="./config/prompts", prompts=prompts)
        rendered, version = manager.render_prompt("greeting", {"name": "Bob"})
        assert isinstance(version, PromptVersion)
        assert version.version == "v1.0.0"
        assert version.template_name == "greeting"
        assert version.created_by == "test_user"
        assert version.changelog == "Initial version"

    def test_prompt_manager_render_prompt_uses_latest_version(self):
        """render_prompt uses latest version when multiple exist"""
        prompts = {
            "greeting": {
                "v1.0.0": PromptVersion(
                    version="v1.0.0",
                    template_name="greeting",
                    template_content="Hello {name} v1",
                    variables=["name"],
                    created_at=datetime.now(),
                    created_by="test",
                ),
                "v2.0.0": PromptVersion(
                    version="v2.0.0",
                    template_name="greeting",
                    template_content="Hello {name} v2",
                    variables=["name"],
                    created_at=datetime.now(),
                    created_by="test",
                ),
            }
        }
        manager = PromptManager(prompt_dir="./config/prompts", prompts=prompts)
        rendered, version = manager.render_prompt("greeting", {"name": "Test"})
        assert rendered == "Hello Test v2"
        assert version.version == "v2.0.0"


class TestPromptManagerLoadYaml:
    """FR-8.7: YAML prompt loading"""

    def test_prompt_manager_loads_yaml_prompts(self, monkeypatch):
        """Loads prompts from YAML files if prompt_dir exists"""
        yaml_data = {
            "prompts": {
                "greeting": {
                    "v1.0.0": {
                        "version": "v1.0.0",
                        "template_name": "greeting",
                        "template_content": "Hello {name}",
                        "variables": ["name"],
                        "created_at": "2024-01-01T00:00:00",
                        "created_by": "test_user",
                        "changelog": "Initial version",
                    }
                }
            }
        }
        # Create mock Path that returns our mock files
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [MagicMock()]
        mock_path.glob.return_value[0].open.return_value.__enter__.return_value.read.return_value = str(yaml_data)

        with patch("src.agent.prompts.Path", return_value=mock_path):
            with patch("src.agent.prompts.yaml.safe_load", return_value=yaml_data):
                manager = PromptManager(prompt_dir="./config/prompts")
                assert "greeting" in manager.prompts
                assert "v1.0.0" in manager.prompts["greeting"]

    def test_prompt_manager_loads_yaml_prompts_creates_datetime(self, monkeypatch):
        """Loaded prompts have datetime objects for created_at"""
        yaml_data = {
            "prompts": {
                "greeting": {
                    "v1.0.0": {
                        "version": "v1.0.0",
                        "template_name": "greeting",
                        "template_content": "Hello {name}",
                        "variables": ["name"],
                        "created_at": "2024-01-01T00:00:00",
                        "created_by": "test_user",
                        "changelog": None,
                    }
                }
            }
        }
        # Create mock Path that returns our mock files
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = [MagicMock()]
        mock_path.glob.return_value[0].open.return_value.__enter__.return_value.read.return_value = str(yaml_data)

        with patch("src.agent.prompts.Path", return_value=mock_path):
            with patch("src.agent.prompts.yaml.safe_load", return_value=yaml_data):
                manager = PromptManager(prompt_dir="./config/prompts")
                prompt = manager.prompts["greeting"]["v1.0.0"]
                assert isinstance(prompt.created_at, datetime)
