# AI Service Integration Module
# This module handles communication with external AI services

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional
from . import fusionAddInUtils as futil

class AIService:
    """
    AI Service class to handle communication with external AI APIs
    Currently supports OpenAI GPT and can be extended for other services
    """
    
    def __init__(self, api_key: str = None, service_type: str = "openai"):
        self.api_key = api_key or self._get_api_key_from_config()
        self.service_type = service_type.lower()
        self.base_urls = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        }
        
    def _get_api_key_from_config(self) -> Optional[str]:
        """
        Get API key from config or environment
        For MVP, we'll use a placeholder - in production, this should be more secure
        """
        try:
            from ... import config
            return getattr(config, 'AI_API_KEY', None)
        except:
            return None
    
    def process_natural_language_command(self, user_command: str) -> Dict[str, Any]:
        """
        Process a natural language command and return structured data
        
        Args:
            user_command: The user's natural language input
            
        Returns:
            Dictionary containing the parsed command structure
        """
        try:
            if not self.api_key:
                return self._create_mock_response(user_command)
            
            if self.service_type == "openai":
                return self._process_with_openai(user_command)
            else:
                return self._create_mock_response(user_command)
                
        except Exception as e:
            futil.log(f"AI Service Error: {str(e)}", futil.adsk.core.LogLevels.ErrorLogLevel)
            return {
                "status": "error",
                "message": f"AI service error: {str(e)}",
                "originalCommand": user_command
            }
    
    def _process_with_openai(self, user_command: str) -> Dict[str, Any]:
        """Process command using OpenAI API"""
        
        system_prompt = """You are an AI assistant for Fusion 360 CAD software by CadxStudio. 
        Convert natural language commands into structured JSON responses for 3D modeling operations.
        
        Supported operations:
        - create_box: Creates a rectangular box (parameters: length, width, height in mm)
        - create_cylinder: Creates a cylinder (parameters: radius, height in mm)
        - create_sphere: Creates a sphere (parameters: radius in mm)
        - create_gear: Creates a spur gear (parameters: number_of_teeth, module in mm, bore_diameter in mm, thickness in mm)
        - create_hole: Creates a hole in selected face (parameters: diameter in mm, depth in mm)
        - extrude_face: Extrudes selected face (parameters: distance in mm)
        - move_body: Moves selected body (parameters: x, y, z in mm)
        
        Always respond with valid JSON in this format:
        {
            "status": "success",
            "action": "operation_name",
            "parameters": {"param1": value1, "param2": value2},
            "message": "Human readable description"
        }
        
        For gears, if not specified:
        - Default module: 2.0mm
        - Default bore_diameter: 6.0mm
        - Default thickness: 5.0mm
        - Default number_of_teeth: 20
        
        If the command is unclear or unsupported, respond with:
        {
            "status": "error",
            "message": "Explanation of the issue"
        }
        """
        
        try:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_command}
                ],
                "max_tokens": 200,
                "temperature": 0.1
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            req = urllib.request.Request(
                self.base_urls["openai"],
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            ai_response = result['choices'][0]['message']['content'].strip()
            
            # Try to parse the AI response as JSON
            try:
                parsed_response = json.loads(ai_response)
                parsed_response["originalCommand"] = user_command
                parsed_response["aiRawResponse"] = ai_response
                return parsed_response
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "message": "AI returned invalid JSON format",
                    "originalCommand": user_command,
                    "aiRawResponse": ai_response
                }
                
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP Error {e.code}: {e.reason}"
            if e.code == 401:
                error_msg = "Invalid API key. Please check your OpenAI API key."
            elif e.code == 429:
                error_msg = "API rate limit exceeded. Please try again later."
            
            return {
                "status": "error",
                "message": error_msg,
                "originalCommand": user_command
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Network error: {str(e)}",
                "originalCommand": user_command
            }
    
    def _create_mock_response(self, user_command: str) -> Dict[str, Any]:
        """
        Create a mock response for testing when no API key is available
        This helps with development and testing
        """
        command_lower = user_command.lower()
        
        # Simple pattern matching for common commands
        if "cube" in command_lower or "box" in command_lower:
            # Try to extract dimensions
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', user_command)
            
            if numbers:
                size = float(numbers[0])
                return {
                    "status": "success",
                    "action": "create_box",
                    "parameters": {"length": size, "width": size, "height": size},
                    "message": f"Creating a {size}mm cube",
                    "originalCommand": user_command,
                    "note": "Mock response - no AI API key configured"
                }
        
        elif "cylinder" in command_lower:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', user_command)
            
            if len(numbers) >= 2:
                radius = float(numbers[0])
                height = float(numbers[1])
                return {
                    "status": "success",
                    "action": "create_cylinder",
                    "parameters": {"radius": radius, "height": height},
                    "message": f"Creating a cylinder with radius {radius}mm and height {height}mm",
                    "originalCommand": user_command,
                    "note": "Mock response - no AI API key configured"
                }
        
        elif "sphere" in command_lower:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', user_command)
            
            if numbers:
                radius = float(numbers[0])
                return {
                    "status": "success",
                    "action": "create_sphere",
                    "parameters": {"radius": radius},
                    "message": f"Creating a sphere with radius {radius}mm",
                    "originalCommand": user_command,
                    "note": "Mock response - no AI API key configured"
                }
        
        elif "gear" in command_lower:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', user_command)
            
            # Extract number of teeth if mentioned
            teeth = 20  # default
            module = 2.0  # default
            bore = 6.0  # default
            thickness = 5.0  # default
            
            if numbers:
                teeth = int(float(numbers[0]))
                if len(numbers) > 1:
                    module = float(numbers[1])
                if len(numbers) > 2:
                    bore = float(numbers[2])
                if len(numbers) > 3:
                    thickness = float(numbers[3])
            
            return {
                "status": "success",
                "action": "create_gear",
                "parameters": {
                    "number_of_teeth": teeth,
                    "module": module,
                    "bore_diameter": bore,
                    "thickness": thickness
                },
                "message": f"Creating a gear with {teeth} teeth, module {module}mm",
                "originalCommand": user_command,
                "note": "Mock response - no AI API key configured"
            }
        
        elif "hole" in command_lower:
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', user_command)
            
            diameter = 5.0  # default
            depth = 10.0  # default
            
            if numbers:
                diameter = float(numbers[0])
                if len(numbers) > 1:
                    depth = float(numbers[1])
            
            return {
                "status": "success",
                "action": "create_hole",
                "parameters": {"diameter": diameter, "depth": depth},
                "message": f"Creating a hole with diameter {diameter}mm and depth {depth}mm",
                "originalCommand": user_command,
                "note": "Mock response - no AI API key configured"
            }
        
        # Default response for unrecognized commands
        return {
            "status": "error",
            "message": "Command not recognized. Try 'create a 10mm cube', 'make a cylinder with radius 5mm and height 20mm', 'create a gear with 24 teeth', or 'make a hole with diameter 8mm'",
            "originalCommand": user_command,
            "note": "Mock response - no AI API key configured"
        }