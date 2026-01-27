"""
KGCS Configuration Module

Loads environment variables from .env file and provides type-safe access to configuration.
Supports both local dev and production environments.

Usage:
    from src.config import neo4j_config, etl_config, validation_config
    
    uri = neo4j_config.uri
    user = neo4j_config.user
    password = neo4j_config.password
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed, use environment variables


@dataclass
class Neo4jConfig:
    """Neo4j database connection configuration."""
    
    uri: str
    user: str
    password: str
    database: str = 'neo4j'
    encrypted: bool = False
    trust: str = 'TRUST_ALL_CERTIFICATES'
    auth_enabled: bool = True
    
    @classmethod
    def from_env(cls) -> 'Neo4jConfig':
        """Load configuration from environment variables."""
        return cls(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.getenv('NEO4J_USER', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', 'password'),
            database=os.getenv('NEO4J_DATABASE', 'neo4j'),
            encrypted=os.getenv('NEO4J_ENCRYPTED', 'false').lower() == 'true',
            trust=os.getenv('NEO4J_TRUST', 'TRUST_ALL_CERTIFICATES'),
            auth_enabled=os.getenv('NEO4J_AUTH_ENABLED', 'true').lower() == 'true',
        )
    
    def to_dict(self) -> dict:
        """Export as dictionary (excluding password for security)."""
        return {
            'uri': self.uri,
            'user': self.user,
            'database': self.database,
            'encrypted': self.encrypted,
            'trust': self.trust,
            'auth_enabled': self.auth_enabled,
        }
    
    def validate(self) -> bool:
        """Validate that all required fields are set."""
        required = [self.uri, self.user, self.password, self.database]
        return all(required)


@dataclass
class ETLConfig:
    """ETL Pipeline configuration."""
    
    batch_size: int = 1000
    parallelism: int = 4
    timeout_seconds: int = 300
    
    @classmethod
    def from_env(cls) -> 'ETLConfig':
        """Load configuration from environment variables."""
        return cls(
            batch_size=int(os.getenv('ETL_BATCH_SIZE', '1000')),
            parallelism=int(os.getenv('ETL_PARALLELISM', '4')),
            timeout_seconds=int(os.getenv('ETL_TIMEOUT_SECONDS', '300')),
        )
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            'batch_size': self.batch_size,
            'parallelism': self.parallelism,
            'timeout_seconds': self.timeout_seconds,
        }


@dataclass
class ValidationConfig:
    """SHACL Validation configuration."""
    
    validate_before_ingest: bool = True
    shapes_dir: str = 'docs/ontology/shacl'
    abort_on_failure: bool = True
    
    @classmethod
    def from_env(cls) -> 'ValidationConfig':
        """Load configuration from environment variables."""
        return cls(
            validate_before_ingest=os.getenv('VALIDATE_BEFORE_INGEST', 'true').lower() == 'true',
            shapes_dir=os.getenv('SHACL_SHAPES_DIR', 'docs/ontology/shacl'),
            abort_on_failure=os.getenv('ABORT_ON_VALIDATION_FAILURE', 'true').lower() == 'true',
        )
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            'validate_before_ingest': self.validate_before_ingest,
            'shapes_dir': self.shapes_dir,
            'abort_on_failure': self.abort_on_failure,
        }


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    level: str = 'INFO'
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Load configuration from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', None),
        )
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            'level': self.level,
            'log_file': self.log_file,
        }


class KGCSConfig:
    """Main KGCS configuration (aggregates all configs)."""
    
    def __init__(self):
        self.neo4j = Neo4jConfig.from_env()
        self.etl = ETLConfig.from_env()
        self.validation = ValidationConfig.from_env()
        self.logging = LoggingConfig.from_env()
    
    def to_dict(self) -> dict:
        """Export all configuration as dictionary (excluding secrets)."""
        return {
            'neo4j': self.neo4j.to_dict(),
            'etl': self.etl.to_dict(),
            'validation': self.validation.to_dict(),
            'logging': self.logging.to_dict(),
        }
    
    def validate_all(self) -> bool:
        """Validate all configurations."""
        return self.neo4j.validate()


# Global configuration instance
config = KGCSConfig()


# Convenience exports
neo4j_config = config.neo4j
etl_config = config.etl
validation_config = config.validation
logging_config = config.logging


if __name__ == '__main__':
    """Print configuration (excluding secrets) when run as script."""
    import json
    print("KGCS Configuration:")
    print(json.dumps(config.to_dict(), indent=2))
