# Application Global Variables
# This module serves as a way to share variables across different
# modules (global variables).

import os

# Flag that indicates to run in Debug mode or not. When running in Debug mode
# more information is written to the Text Command window. Generally, it's useful
# to set this to True while developing an add-in and set it to False when you
# are ready to distribute it.
DEBUG = True

# Gets the name of the add-in from the name of the folder the py file is in.
# This is used when defining unique internal names for various UI elements 
# that need a unique name. It's also recommended to use a company name as 
# part of the ID to better ensure the ID is unique.
ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = 'ACME'

# Palettes
sample_palette_id = f'{COMPANY_NAME}_{ADDIN_NAME}_palette_id'

# AI Configuration
# For production, consider using environment variables or secure storage
# For development/testing, you can set your OpenAI API key here
AI_API_KEY = None  # Set to your OpenAI API key: "sk-your-api-key-here"

# AI Service Configuration
AI_SERVICE_TYPE = "openai"  # Currently supports "openai"
AI_MODEL = "gpt-3.5-turbo"  # Model to use for OpenAI

# Supported AI Commands (for reference and validation)
SUPPORTED_AI_COMMANDS = {
    "create_box": {
        "description": "Creates a rectangular box",
        "parameters": ["length", "width", "height"],
        "units": "mm"
    },
    "create_cylinder": {
        "description": "Creates a cylinder",
        "parameters": ["radius", "height"],
        "units": "mm"
    },
    "create_sphere": {
        "description": "Creates a sphere",
        "parameters": ["radius"],
        "units": "mm"
    },
    "extrude_face": {
        "description": "Extrudes a selected face",
        "parameters": ["distance"],
        "units": "mm",
        "requires_selection": True
    },
    "move_body": {
        "description": "Moves a selected body",
        "parameters": ["x", "y", "z"],
        "units": "mm",
        "requires_selection": True
    }
}