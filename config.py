"""
Configuration management for Equinox application.
This file handles all environment variables and application settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Application Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MODEL = os.getenv('DEFAULT_MODEL', 'gpt-3.5-turbo-instruct')
    
    # External Services
    LLM_URL = os.getenv('LLM_URL', 'http://localhost:8865/chat/completions')
    
    # Database Settings
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'example_collection')
    
    # API Settings
    MAX_TOKENS_DEFAULT = int(os.getenv('MAX_TOKENS_DEFAULT', '100'))
    TEMPERATURE_DEFAULT = float(os.getenv('TEMPERATURE_DEFAULT', '0.7'))
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration variables"""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override defaults for production
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production
    
    @classmethod
    def validate_config(cls):
        """Additional validation for production"""
        super().validate_config()
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-change-in-production':
            raise ValueError("SECRET_KEY must be set for production")
        
        return True

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    UPLOAD_FOLDER = 'test_uploads'

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config_map.get(config_name, DevelopmentConfig)