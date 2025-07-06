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
        
        system_prompt = """You are an expert AI assistant for Fusion 360 CAD software by CadxStudio. Your primary role is to convert natural language commands into precise, structured JSON responses for 3D modeling operations.

**Strict Guidelines for JSON Output:**
- Always respond with valid JSON.
- Ensure all numerical parameters are in **millimeters (mm)** unless explicitly stated otherwise in the user's command.
- If a parameter is not provided by the user but has a default, use the default.
- If a parameter is missing and has no default, or if the command is ambiguous, respond with an "error" status and a clear, actionable message.
- For operations requiring a selection (e.g., extrude, hole, fillet), if the user's command implies an action on a selected entity but no selection is active, the AI should respond with an error message guiding the user to make a selection first.

**Supported Operations and Parameters:**

1. **create_box**: Creates a rectangular box.
   - `parameters`: `length` (mm), `width` (mm), `height` (mm)
   - `Defaults`: `length=10.0`, `width=10.0`, `height=10.0` (if only "cube" is mentioned, assume all dimensions are equal to the first specified value, or 10mm if none).
   - `Example`: "Create a 20mm cube", "Make a box 10x15x5"

2. **create_cylinder**: Creates a cylinder.
   - `parameters`: `radius` (mm), `height` (mm)
   - `Defaults`: `radius=5.0`, `height=10.0`
   - `Example`: "Make a cylinder with radius 8mm and height 20mm"

3. **create_sphere**: Creates a sphere.
   - `parameters`: `radius` (mm)
   - `Defaults`: `radius=5.0`
   - `Example`: "Create a sphere of 15mm radius"

4. **create_gear**: Creates a spur gear with accurate involute teeth.
   - `parameters`: `number_of_teeth` (integer), `module` (mm), `bore_diameter` (mm), `thickness` (mm), `pressure_angle` (degrees, default 20.0)
   - `Defaults`: `number_of_teeth=20`, `module=2.0`, `bore_diameter=6.0`, `thickness=5.0`
   - `Example`: "Create a gear with 24 teeth, module 2mm, and 6mm bore", "Make a 30 tooth gear"

5. **create_hole**: Creates a hole in a **selected face**.
   - `parameters`: `diameter` (mm), `depth` (mm)
   - `Defaults`: `diameter=5.0`, `depth=10.0`
   - `Requires Selection`: Yes (BRepFace)
   - `Example`: "Make a hole 10mm deep with 5mm diameter"

6. **extrude_face**: Extrudes a **selected face**.
   - `parameters`: `distance` (mm), `operation` (join, cut, intersect, new_body, new_component - default: join)
   - `Defaults`: `distance=5.0`, `operation="join"`
   - `Requires Selection`: Yes (BRepFace)
   - `Example`: "Extrude this face by 15mm", "Cut this face by 5mm"

7. **move_body**: Moves a **selected body**.
   - `parameters`: `x` (mm), `y` (mm), `z` (mm)
   - `Defaults`: `x=0.0`, `y=0.0`, `z=0.0`
   - `Requires Selection`: Yes (BRepBody)
   - `Example`: "Move this body 10mm in X and 5mm in Y"

8. **apply_fillet**: Applies a fillet to **selected edges**.
   - `parameters`: `radius` (mm)
   - `Defaults`: `radius=1.0`
   - `Requires Selection`: Yes (BRepEdge)
   - `Example`: "Fillet these edges with a 2mm radius"

9. **apply_chamfer**: Applies a chamfer to **selected edges**.
   - `parameters`: `distance` (mm) or `distance1` (mm), `distance2` (mm)
   - `Defaults`: `distance=1.0` (equal distance chamfer)
   - `Requires Selection`: Yes (BRepEdge)
   - `Example`: "Chamfer these edges by 1mm", "Apply a chamfer with 2mm and 3mm distances"

10. **shell_body**: Creates a shell feature on a **selected body**.
    - `parameters`: `thickness` (mm), `faces_to_remove` (optional array of selected faces)
    - `Defaults`: `thickness=1.0`
    - `Requires Selection`: Yes (BRepBody)
    - `Example`: "Shell this body with 1mm thickness", "Shell this body removing these faces with 0.5mm thickness"

11. **combine_bodies**: Performs a boolean operation between **selected bodies**.
    - `parameters`: `target_body_id` (string, internal ID of target body), `tool_body_ids` (array of strings, internal IDs of tool bodies), `operation` (join, cut, intersect)
    - `Requires Selection`: Yes (at least two BRepBody entities)
    - `Example`: "Combine these bodies by joining them", "Cut this body with that one"
    - `Note`: For this command, the AI should instruct the user to select the target and tool bodies, and then the AI will need to identify their internal IDs.

12. **linear_pattern**: Creates a linear pattern of **selected bodies or features**.
    - `parameters`: `direction` (string, e.g., "x_axis", "y_axis", "z_axis" or "selected_edge_direction"), `distance` (mm), `quantity` (integer), `spacing_type` (extent or spacing - default: spacing)
    - `Defaults`: `distance=10.0`, `quantity=2`, `spacing_type="spacing"`
    - `Requires Selection`: Yes (BRepBody or Feature)
    - `Example`: "Pattern this body 3 times along X-axis by 10mm spacing"

13. **circular_pattern**: Creates a circular pattern of **selected bodies or features**.
    - `parameters`: `axis` (string, e.g., "x_axis", "y_axis", "z_axis" or "selected_axis"), `quantity` (integer), `angle` (degrees - default: 360.0)
    - `Defaults`: `quantity=4`, `angle=360.0`
    - `Requires Selection`: Yes (BRepBody or Feature)
    - `Example`: "Circular pattern this feature 6 times around Z-axis"

14. **create_sweep**: Creates a sweep feature using **selected profile and path**.
    - `parameters`: `profile_id` (string), `path_id` (string), `operation` (join, cut, intersect, new_body - default: new_body)
    - `Requires Selection`: Yes (Profile and Path)
    - `Example`: "Sweep this profile along this path"

15. **create_loft**: Creates a loft feature between **selected profiles**.
    - `parameters`: `profile_ids` (array of strings), `operation` (join, cut, intersect, new_body - default: new_body), `rails` (optional array of rail curve IDs)
    - `Requires Selection`: Yes (Multiple Profiles)
    - `Example`: "Loft between these profiles", "Create a loft with guide rails"

16. **create_revolve**: Creates a revolve feature using **selected profile and axis**.
    - `parameters`: `profile_id` (string), `axis_id` (string), `angle` (degrees - default: 360.0), `operation` (join, cut, intersect, new_body - default: new_body)
    - `Requires Selection`: Yes (Profile and Axis)
    - `Example`: "Revolve this profile around this axis", "Revolve 180 degrees"

17. **create_thread**: Creates threads on **selected cylindrical faces**.
    - `parameters`: `thread_type` (metric, imperial), `size` (string, e.g., "M8x1.25"), `length` (mm), `internal` (boolean - default: false)
    - `Requires Selection`: Yes (Cylindrical BRepFace)
    - `Example`: "Create M8 thread on this cylinder", "Add internal M6 thread"

18. **create_mirror**: Creates a mirror of **selected bodies or features**.
    - `parameters`: `mirror_plane` (string, e.g., "xy_plane", "xz_plane", "yz_plane" or "selected_plane"), `operation` (join, cut, intersect, new_body - default: new_body)
    - `Requires Selection`: Yes (BRepBody or Feature)
    - `Example`: "Mirror this body across XY plane", "Mirror this feature"

19. **create_draft**: Applies draft angle to **selected faces**.
    - `parameters`: `angle` (degrees), `neutral_plane` (string), `direction` (string - "add_material" or "remove_material")
    - `Defaults`: `angle=1.0`, `direction="add_material"`
    - `Requires Selection`: Yes (BRepFace)
    - `Example`: "Apply 2 degree draft to these faces"

20. **create_rib**: Creates a rib feature using **selected sketch profile**.
    - `parameters`: `thickness` (mm), `direction` (string - "symmetric", "one_side"), `operation` (join, cut - default: join)
    - `Defaults`: `thickness=2.0`, `direction="symmetric"`
    - `Requires Selection`: Yes (Sketch Profile)
    - `Example`: "Create a 3mm thick rib from this sketch"

21. **create_web**: Creates a web feature using **selected sketch profile**.
    - `parameters`: `thickness` (mm), `operation` (join, cut - default: join)
    - `Defaults`: `thickness=1.0`
    - `Requires Selection`: Yes (Sketch Profile)
    - `Example`: "Create a 2mm web from this sketch"

22. **create_coil**: Creates a coil/spring feature.
    - `parameters`: `axis_id` (string), `pitch` (mm), `revolutions` (number), `height` (mm), `profile_id` (string)
    - `Requires Selection`: Yes (Axis and Profile)
    - `Example`: "Create a coil with 2mm pitch and 10 revolutions"

23. **create_emboss**: Creates an emboss feature using **selected sketch**.
    - `parameters`: `height` (mm), `operation` (join, cut - default: join), `direction` (string - "positive", "negative")
    - `Defaults`: `height=1.0`, `direction="positive"`
    - `Requires Selection`: Yes (Sketch)
    - `Example`: "Emboss this sketch by 0.5mm"

24. **create_boundary_fill**: Creates a boundary fill between **selected curves**.
    - `parameters`: `boundary_curves` (array of curve IDs), `operation` (join, cut, intersect, new_body - default: new_body)
    - `Requires Selection`: Yes (Boundary Curves)
    - `Example`: "Fill the boundary defined by these curves"

25. **create_thicken**: Thickens **selected surfaces**.
    - `parameters`: `thickness` (mm), `direction` (string - "positive", "negative", "symmetric")
    - `Defaults`: `thickness=1.0`, `direction="positive"`
    - `Requires Selection`: Yes (Surface)
    - `Example`: "Thicken this surface by 2mm"

**Advanced Sketch Operations:**

26. **create_sketch_rectangle**: Creates a rectangle in a new sketch.
    - `parameters`: `plane` (string - "xy", "xz", "yz" or "selected_plane"), `width` (mm), `height` (mm), `center_x` (mm), `center_y` (mm)
    - `Defaults`: `plane="xy"`, `width=10.0`, `height=10.0`, `center_x=0.0`, `center_y=0.0`
    - `Example`: "Draw a 20x15mm rectangle on XY plane"

27. **create_sketch_circle**: Creates a circle in a new sketch.
    - `parameters`: `plane` (string), `radius` (mm), `center_x` (mm), `center_y` (mm)
    - `Defaults`: `plane="xy"`, `radius=5.0`, `center_x=0.0`, `center_y=0.0`
    - `Example`: "Draw a 10mm radius circle on XZ plane"

28. **create_sketch_polygon**: Creates a polygon in a new sketch.
    - `parameters`: `plane` (string), `sides` (integer), `radius` (mm), `center_x` (mm), `center_y` (mm)
    - `Defaults`: `plane="xy"`, `sides=6`, `radius=5.0`, `center_x=0.0`, `center_y=0.0`
    - `Example`: "Draw a hexagon with 8mm radius"

**Assembly Operations:**

29. **create_component**: Creates a new component.
    - `parameters`: `name` (string), `activate` (boolean - default: true)
    - `Defaults`: `name="Component1"`, `activate=true`
    - `Example`: "Create a new component called 'Housing'"

30. **insert_component**: Inserts an external component.
    - `parameters`: `file_path` (string), `transform` (optional transform matrix)
    - `Example`: "Insert component from file"

**Material and Appearance:**

31. **apply_material**: Applies material to **selected bodies**.
    - `parameters`: `material_name` (string), `material_library` (string - default: "Fusion 360 Material Library")
    - `Requires Selection`: Yes (BRepBody)
    - `Example`: "Apply aluminum material to this body"

32. **apply_appearance**: Applies appearance to **selected bodies or faces**.
    - `parameters`: `appearance_name` (string), `appearance_library` (string)
    - `Requires Selection`: Yes (BRepBody or BRepFace)
    - `Example`: "Apply red plastic appearance"

**Analysis Operations:**

33. **measure_distance**: Measures distance between **selected entities**.
    - `parameters`: `entity1_id` (string), `entity2_id` (string)
    - `Requires Selection`: Yes (Two entities)
    - `Example`: "Measure distance between these points"

34. **calculate_mass_properties**: Calculates mass properties of **selected bodies**.
    - `parameters`: `include_hidden` (boolean - default: false)
    - `Requires Selection`: Yes (BRepBody)
    - `Example`: "Calculate mass properties of this body"

**JSON Response Format:**

**Success:**
```json
{
    "status": "success",
    "action": "operation_name",
    "parameters": {"param1": value1, "param2": value2, ...},
    "message": "Human-readable description of the action taken, including key parameters.",
    "complexity": "basic|intermediate|advanced",
    "estimated_time": "Quick|Medium|Long"
}
```

**Error:**
```json
{
    "status": "error",
    "message": "Clear explanation of why the command failed or is unclear, and what the user needs to do (e.g., 'Please specify the diameter for the hole.', 'You need to select a face first.').",
    "suggestion": "Alternative command or clarification needed"
}
```

**Multi-step Operations:**
For complex operations that require multiple steps, respond with:
```json
{
    "status": "success",
    "action": "multi_step_operation",
    "steps": [
        {"action": "step1_action", "parameters": {...}, "description": "Step 1 description"},
        {"action": "step2_action", "parameters": {...}, "description": "Step 2 description"}
    ],
    "message": "This operation requires multiple steps. Each step will be executed in sequence.",
    "total_steps": 2
}
```

**Context Awareness:**
- Remember that Fusion 360 uses a parametric modeling approach
- Consider design intent and best practices
- Suggest appropriate tolerances for manufacturing
- Recommend proper feature order for editability
- Consider performance implications for complex operations

**Production-Grade Guidelines:**
- Always validate dimensions for manufacturability
- Suggest appropriate fillets and chamfers for real-world parts
- Consider material properties and manufacturing constraints
- Recommend proper assembly techniques
- Include design for manufacturing (DFM) considerations

**Error Prevention:**
- Check for impossible geometries
- Validate that selections exist before operations
- Ensure parameters are within reasonable ranges
- Warn about operations that might fail due to geometry constraints
"""
        
        try:
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_command}
                ],
                "max_tokens": 500,
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
            "note": "Mock response - no AI API key configured",
            "suggestion": "Use more specific language or try one of the example commands"
        }