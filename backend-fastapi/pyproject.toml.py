[build - system]
requires = ["setuptools>=61.0", "wheel"]
build - backend = "setuptools.build_meta"

[project]
name = "docintel-backend"
version = "1.0.0"
description = "AI-Powered Document Intelligence Platform - FastAPI Backend"
authors = [
    {name = "AI Engineering Team", email = "team@docintel.com"}
]
license = {text = "MIT"}
readme = "README.md"
requires - python = ">=3.11"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    # Core Framework
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "python-multipart==0.0.6",

    # Database
    "sqlalchemy==2.0.23",
    "asyncpg==0.29.0",
    "alembic==1.12.1",
    "pgvector==0.2.5",

    # AI/ML
    "openai==1.3.0",
    "langchain==0.0.340",
    "langgraph==0.0.20",
    "sentence-transformers==2.2.2",
    "tiktoken==0.5.1",
    "transformers==4.36.0",

    # Vector Store
    "qdrant-client==1.7.0",

    # Cache & Queue
    "redis==5.0.1",
    "aioredis==2.0.1",
    "aiokafka==0.8.0",

    # Document Processing
    "unstructured==0.10.30",
    "python-docx==1.1.0",
    "PyPDF2==3.0.1",
    "pdf2image==1.16.3",
    "pytesseract==0.3.10",
    "langchain-community==0.0.10",

    # Monitoring & Logging
    "prometheus-client==0.19.0",
    "opentelemetry-api==1.21.0",
    "opentelemetry-sdk==1.21.0",
    "loguru==0.7.2",

    # Utilities
    "python-dotenv==1.0.0",
    "pydantic==2.5.0",
    "pydantic-settings==2.1.0",
    "httpx==0.25.1",
    "tenacity==8.2.3",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "python-dateutil==2.8.2",

    # AWS SDK
    "boto3==1.34.3",
]

[project.optional - dependencies]
dev = [
    "pytest==7.4.3",
    "pytest-asyncio==0.21.1",
    "pytest-cov==4.1.0",
    "httpx==0.25.1",
    "faker==20.1.0",
    "black==23.11.0",
    "isort==5.13.0",
    "flake8==6.1.0",
    "mypy==1.7.1",
    "pre-commit==3.5.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/docintel"
Repository = "https://github.com/yourusername/docintel.git"
Documentation = "https://docs.docintel.com"

[tool.black]
line - length = 100
target - version = ['py311', 'py312']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
  | migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
skip_gitignore = true
skip_migrations = true

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
disallow_untyped_defs = false
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
follow_imports = "silent"
exclude = [
    "migrations/",
    "venv/",
    ".venv/",
    "tests/",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml"
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
timeout = 300

[tool.coverage.run]
source = ["app"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/venv/*",
    "*/.venv/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
]

[tool.pydantic - settings]
case_sensitive = true
env_file = ".env"
env_file_encoding = "utf-8"

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]
exclude = ["tests*", "migrations*"]

# Ruff configuration (alternative to flake8)
[tool.ruff]
line - length = 100
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "C901",  # too complex
]
exclude = [
    "migrations/",
    "venv/",
    ".venv/",
]

[tool.ruff.per - file - ignores]
"__init__.py" = ["F401"]
"tests/*" = ["S101"]

# Bandit security checks
[tool.bandit]
exclude_dirs = ["tests", "migrations", "venv"]
skips = ["B101", "B311"]
severity = "medium"

# Commitizen for conventional commits
[tool.commitizen]
name = "cz_conventional_commits"
version = "1.0.0"
version_files = [
    "pyproject.toml:version",
    "app/__init__.py:__version__",
]

# VSCode settings
[tool.vscode]
python.defaultInterpreterPath = "./venv/bin/python"
python.linting.enabled = true
python.linting.mypyEnabled = true
python.linting.ruffEnabled = true
python.formatting.provider = "black"
editor.formatOnSave = true
editor.codeActionsOnSave = {
    "source.organizeImports": true
}